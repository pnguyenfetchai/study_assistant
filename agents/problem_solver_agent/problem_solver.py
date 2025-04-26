from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context
from dotenv import load_dotenv
import os
from openai import OpenAI
import sys
sys.path.append('..')
from query_protocol import query_protocol, RequestResponse
from problem_protocol import problem_protocol, QueryRequest
from chat_protocol import chat_proto
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent, ChatAcknowledgement

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent addresses
QUERY_AGENT_ADDRESS = "agent1qta523twlmzwxw8kcl98sv3kk67qeg8c0k9x7whdktsa3tw6paa8yyez7wv"
CANVAS_AGENT_ADDRESS = "agent1q0uvz4t5tv8dcahzwgks4pymps98ua9m2rnpfguxrzk55zv0xg2p2ye834v"
ANALYZER_AGENT_ADDRESS = "agent1qdsp54ynk7gaeyn9h04dzjm9ndxhg9nlgjls8a49e9jxdhk2tap8wg78mf8"

client = OpenAI(api_key=OPENAI_API_KEY)

problem_solver_agent = Agent(
    name="problem_solver_agent",
    port=8004,
    mailbox=True
)


problem = {}

@problem_protocol.on_message(model=QueryRequest)
async def solve_problem(ctx: Context, sender: str, message: QueryRequest):
    ctx.logger.info(f"Received problem-solving request: {message.query}")

    problem[sender] = message.query
    
    query_text = f"Provide relevant materials for solving: {message.query} DO NOT ATTEMPT TO SOLVE THE PROBLEM AND ONLY PROVIDE THE NECESSARY CONTEXT FROM THE KNOWLEDGE BASE THAT HELP SOLVING THE PROBLEM"
    await ctx.send(QUERY_AGENT_ADDRESS, QueryRequest(query=query_text))

@query_protocol.on_message(model=RequestResponse)
async def receive_query_response(ctx: Context, sender: str, requestresponse: RequestResponse):
    ctx.logger.info(f"Received context from Query Agent: {requestresponse.response}")

    
    problem_solution = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Solve the given problem using relevant course materials."},
            {"role": "user", "content": f"Original Problem: {problem[CANVAS_AGENT_ADDRESS]}\nContext: {requestresponse.response}"}
        ]
    )
    solution = problem_solution.choices[0].message.content
    
    ctx.logger.info(f"Sending problem solution: {solution}")
    await ctx.send(ANALYZER_AGENT_ADDRESS, RequestResponse(request=requestresponse.request,response=solution))

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    try:
        # Send acknowledgment first
        await ctx.send(
            sender,
            ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id)
        )

        # Extract text content from the message
        text_content = next((content.text for content in msg.content if isinstance(content, TextContent)), None)
        if not text_content:
            error_msg = "No text content found in the message"
            ctx.logger.error(error_msg)
            await ctx.send(sender, ChatMessage(
                content=[TextContent(type="text", text=error_msg)],
                timestamp=datetime.now(),
                msg_id=uuid4()
            ))
            return

        ctx.logger.info(f"Received direct chat message from {sender}: {text_content}")

        # Use GPT-4 to solve the problem directly
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert problem solver. Analyze the given problem and provide a detailed solution with clear steps and explanations."
                },
                {"role": "user", "content": text_content}
            ]
        )
        solution = completion.choices[0].message.content

        # Send the solution back
        await ctx.send(sender, ChatMessage(
            content=[TextContent(type="text", text=solution)],
            timestamp=datetime.now(),
            msg_id=uuid4()
        ))

    except Exception as e:
        error_msg = f"Error processing chat message: {str(e)}"
        ctx.logger.error(error_msg)
        await ctx.send(sender, ChatMessage(
            content=[TextContent(type="text", text=error_msg)],
            timestamp=datetime.now(),
            msg_id=uuid4()
        ))

problem_solver_agent.include(problem_protocol)
problem_solver_agent.include(query_protocol)
problem_solver_agent.include(chat_proto)

if __name__ == "__main__":
    problem_solver_agent.run()
