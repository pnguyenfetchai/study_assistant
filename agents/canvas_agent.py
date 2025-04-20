from uagents import Agent, Context, Model
from dotenv import load_dotenv
import os
from openai import OpenAI
from chat_protocol import chat_proto, create_text_chat
from problem_protocol import problem_protocol
from query_protocol import query_protocol, QueryRequest, RequestResponse
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent, ChatAcknowledgement
from datetime import datetime
load_dotenv()

QUERY_AGENT_ADDRESS = os.getenv("QUERY_AGENT_ADDRESS")
PROBLEM_SOLVER_AGENT_ADDRESS = os.getenv("PROBLEM_SOLVER_AGENT_ADDRESS")
USER_AGENT_ADDRESS = os.getenv("USER_AGENT_ADDRESS")
ANALYZER_AGENT_ADDRESS = os.getenv("ANALYZER_AGENT_ADDRESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

class RequestResponse(Model):
    request: str
    response: str


canvas_agent = Agent(
    name="canvas_agent",
    port=8003,
    mailbox=True
)




def classify_query_with_llm(query: str) -> str:
    """Classify the query using an LLM model."""
    print(f"Debug - Classifying query: {query}")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Classify this query as 'general' (if it is about school materials, classes, or schedules) or 'problem' (if it requires problem-solving like math or physics calculations). Only respond with 'general' or 'problem'."},
                  {"role": "user", "content": query}]
    )
    result = response.choices[0].message.content.strip()
    print(f"Debug - Classification result: {result}")
    return result



@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    # First send acknowledgment
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, TextContent):
            query = item.text
            ctx.logger.info(f"Received query: {query}")
            
            # Store the sender and message info for later response
            ctx.storage.set("current_sender", sender)
            ctx.storage.set("current_msg_id", str(msg.msg_id))
            
            # Classify the query
            query_type = classify_query_with_llm(query)
            ctx.logger.info(f"Query type: {query_type}")
            
            # Forward to appropriate agent based on classification
            if query_type == "general":
                ctx.logger.info(f"Forwarding general query to Query Agent: {query}")
                await ctx.send(QUERY_AGENT_ADDRESS, RequestResponse(request=query, response=""))
            else:
                ctx.logger.info(f"Forwarding problem-solving query to Problem Solver Agent: {query}")
                await ctx.send(PROBLEM_SOLVER_AGENT_ADDRESS, QueryRequest(query=query))

@query_protocol.on_message(RequestResponse)
async def handle_response(ctx: Context, sender: str, msg: RequestResponse):
    ctx.logger.info(f"Received response from {sender}: {msg.response}")
    # Get the original sender from storage
    original_sender = ctx.storage.get("current_sender")
    if original_sender:
        # Convert RequestResponse back to ChatMessage for ASI-1
        response_text = msg.response if msg.response else "No response available"
        ctx.logger.info(f"Sending response to {original_sender}: {response_text}")
        await ctx.send(
            original_sender,
            create_text_chat(response_text, end_session=True)
        )
    else:
        classification = classify_query_with_llm(msg.request)
        if classification == "general":
            ctx.logger.info(f"Forwarding general query to Query Agent: {msg.request}")
            await ctx.send(QUERY_AGENT_ADDRESS, msg)
        else:
            ctx.logger.info(f"Forwarding problem-solving query to Problem Solver Agent: {msg.request}")
            await ctx.send(PROBLEM_SOLVER_AGENT_ADDRESS, QueryRequest(query=msg.request))

        

        




canvas_agent.include(chat_proto, publish_manifest=True)
canvas_agent.include(problem_protocol)
canvas_agent.include(query_protocol)

if __name__ == "__main__":
    canvas_agent.run()
