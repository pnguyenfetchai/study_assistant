from uagents import Agent, Context, Model
from dotenv import load_dotenv
import os
from openai import OpenAI
from chat_protocol import chat_proto, create_text_chat
from problem_protocol import problem_protocol
from query_protocol import query_protocol, QueryRequest, RequestResponse
from visualization_protocol import visualization_protocol, ImageResponse
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
    
    if sender == ANALYZER_AGENT_ADDRESS:
        # Response from analyzer needs to be re-routed based on query type
        classification = classify_query_with_llm(msg.request)
        if classification == "general":
            ctx.logger.info(f"Re-routing to Query Agent: {msg.request}")
            await ctx.send(QUERY_AGENT_ADDRESS, msg)
        else:
            ctx.logger.info(f"Re-routing to Problem Solver Agent: {msg.request}")
            await ctx.send(PROBLEM_SOLVER_AGENT_ADDRESS, QueryRequest(query=msg.request))
    else:
        # This is a response from other agents (query/problem/respondent), send to user
        await send_response_to_user(ctx, msg.response)

async def send_response_to_user(ctx: Context, response_text: str):
    """Helper function to send final response to user"""
    original_sender = ctx.storage.get("current_sender")
    if original_sender:
        ctx.logger.info(f"Sending final response to {original_sender}")
        try:
            await ctx.send(
                original_sender,
                create_text_chat(response_text, end_session=True)
            )
        except Exception as e:
            ctx.logger.error(f"Failed to send response to {original_sender}: {e}")
            # Here you could implement a fallback mechanism if needed
    else:
        ctx.logger.warning("No original sender found for response")

@visualization_protocol.on_message(model=ImageResponse)
async def handle_image_response(ctx: Context, sender: str, msg: ImageResponse):
    """Handle image responses from visualization agent"""
    ctx.logger.info(f"Received visualization from {sender}")
    original_sender = ctx.storage.get("current_sender")
    if original_sender:
        ctx.logger.info(f"Sending visualization to {original_sender}")
        # Create a message with image data in a structured format
        response = {
            "type": "image",
            "content": {
                "data": msg.image_data,
                "content_type": msg.content_type
            }
        }
        await ctx.send(
            original_sender,
            create_text_chat(str(response), end_session=True)
        )
    else:
        ctx.logger.warning("No original sender found for visualization response")

canvas_agent.include(chat_proto, publish_manifest=True)
canvas_agent.include(problem_protocol)
canvas_agent.include(query_protocol)
canvas_agent.include(visualization_protocol)

if __name__ == "__main__":
    canvas_agent.run()
