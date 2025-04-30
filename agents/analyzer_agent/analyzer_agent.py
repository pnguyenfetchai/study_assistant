from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol
from dotenv import load_dotenv
import os
from openai import OpenAI
import sys
sys.path.append('..')
from chat_protocol import chat_proto
from query_protocol import query_protocol, RequestResponse
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent, ChatAcknowledgement, chat_protocol_spec

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent addresses
CANVAS_AGENT_ADDRESS = "agent1q0uvz4t5tv8dcahzwgks4pymps98ua9m2rnpfguxrzk55zv0xg2p2ye834v"
RESPONDENT_AGENT_ADDRESS = "agent1qwxjdy69tu8kmsw6mvq6hsan8ns52axnxhr6vp2aypm409hd8qe8c5augqj"

client = OpenAI(api_key=OPENAI_API_KEY)

@query_protocol.on_message(model=RequestResponse)
async def analyze_query(ctx: Context, sender: str, msg: RequestResponse):
    """Compares the response with the original request and forwards accordingly."""
    ctx.logger.info(f"Received query analysis request from {sender}")
    ctx.logger.info(f"Analyzing: {msg.request} |||| {msg.response}")
    
    is_correct = await check_response(msg.request, msg.response)
    
    if is_correct:
        ctx.logger.info("Response is correct. Forwarding to respondent agent for tool analysis.")
        await ctx.send(RESPONDENT_AGENT_ADDRESS, RequestResponse(request=msg.request, response=msg.response))
    else:
        # Instead of sending back to canvas agent, try to improve the response
        ctx.logger.info("Response needs improvement, sending to respondent agent with improvement flag")
        await ctx.send(RESPONDENT_AGENT_ADDRESS, RequestResponse(request=msg.request + "\n\nPlease improve this response.", response=msg.response ))

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

        # Use GPT-4 to verify the statement
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a fact-checker. Verify if the given statement is correct. Respond with a clear explanation of why it's correct or incorrect."
                },
                {"role": "user", "content": text_content}
            ]
        )
        analysis = completion.choices[0].message.content

        # Send the analysis back
        await ctx.send(sender, ChatMessage(
            content=[TextContent(type="text", text=analysis)],
            timestamp=datetime.now(),
            msg_id=uuid4()
        ))

    except Exception as e:
        error_msg = f"Error analyzing statement: {str(e)}"
        ctx.logger.error(error_msg)
        await ctx.send(sender, ChatMessage(
            content=[TextContent(type="text", text=error_msg)],
            timestamp=datetime.now(),
            msg_id=uuid4()
        ))

async def check_response(question: str, answer: str) -> bool:
    """Uses OpenAI to evaluate whether the response is correct."""
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {   "role": "system", 
                    "content":"""
                        You are an expert AI agent tasked with verifying the correctness and completeness of a response given a specific request. 

                        ## Request:
                        {question}

                        ## Response:
                        {answer}

                        ### Evaluation Criteria:
                        1. **Accuracy** – Does the response directly and factually answer the request?
                        2. **Completeness*s* – Does the response address all components or sub-questions in the request?
                        3. **Relevance** – Is the response on-topic and not containing unnecessary or unrelated information?
                        4. **Consistency** – Is the information consistent and logically coherent?
                        5. **Visualization Exception** - If the question is asking for a visualization, THE RESPONSE IS ALWAYS CORRECT!!!!! AND YOU MUST ANSWER 'yes'!

                        Please return:
                        - `yes` if the response is correct, complete, and appropriate.
                        - `no` if the response is wrong, incomplete, misleading, or off-topic.
                        ONLY AND DO NOT RESPONSE WITH ANYTHING ELSE
                        """
                },
                {"role": "user", "content": f"Question: {question}\nAnswer: {answer}\nIs this answer correct? Respond with 'yes' or 'no' ONLY AND DO NOT RESPONSE WITH ANYTHING ELSE."}
            ]
        )
        response_text = completion.choices[0].message.content.strip().lower()

        print(f"trung xuan tran: {response_text}")
        return response_text.startswith("yes")
    except Exception as e:
        print(f"Error checking response: {e}")
        return False  

# Create the agent
analyzer_agent = Agent(
    name="analyzer_agent",
    port=8006,
    seed="analyzer agent secret phrase",
    mailbox=True
)

analyzer_agent.include(query_protocol)
analyzer_agent.include(chat_proto)

if __name__ == "__main__":
    analyzer_agent.run()