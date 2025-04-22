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
# Load environment variables
load_dotenv()

# Get OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class RequestResponse(Model):
    request: str
    response: str


def clear_storage(ctx: Context):
    """Clear all stored credentials"""
    ctx.storage.set("canvas_token", None)
    ctx.storage.set("school_domain", None)
    ctx.storage.set("current_sender", None)
    ctx.storage.set("current_msg_id", None)
    ctx.logger.info("Storage cleared")

canvas_agent = Agent(
    name="canvas_agent",
    port=8003,
    seed="canvas agent secret phrase",
    mailbox=True
)

@canvas_agent.on_event("startup")
async def startup(ctx: Context):
    clear_storage(ctx)
    ctx.logger.info("Canvas agent started with fresh storage")

def extract_canvas_credentials(text: str) -> tuple[str, str]:
    """Extract Canvas API token and school domain from user's message"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    system_prompt = (
        "You are an AI assistant that extracts Canvas API credentials from text. "
        "You need to extract:\n"
        "1. Canvas API token (typically a long string that looks like '1234~abcd...')\n"
        "2. School domain (e.g., 'berkeley' for berkeley.instructure.com)\n\n"
        "Return the results in this exact format: 'token: <token>\ndomain: <domain>'\n"
        "If either is not found, use 'none' for that field."
    )
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract Canvas credentials from this text: {text}"}
        ]
    )
    result = completion.choices[0].message.content.strip()
    
    # Parse the result
    token = None
    domain = None
    
    for line in result.split('\n'):
        if line.startswith('token:'):
            token = line.replace('token:', '').strip()
            token = None if token.lower() == 'none' else token
        elif line.startswith('domain:'):
            domain = line.replace('domain:', '').strip()
            domain = None if domain.lower() == 'none' else domain
    
    return token, domain
 
def classify_query_with_llm(query: str) -> str:
    """Classify the query using an LLM model."""
    print(f"Debug - Classifying query: {query}")
    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant that classifies user queries into 'general' or 'problem'. Return ONLY 'general' or 'problem' as response."},
            {"role": "user", "content": f"Classify this query: {query}"}
        ]
    )
    result = completion.choices[0].message.content.strip().lower()
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
            
            # Check if we have Canvas credentials stored
            canvas_token = ctx.storage.get("canvas_token")
            school_domain = ctx.storage.get("school_domain")
            
            if not canvas_token or not school_domain:
                # Try to extract credentials from the query
                canvas_token, school_domain = extract_canvas_credentials(query)
                ctx.logger.info(f"Extracted credentials: {canvas_token}, {school_domain}")
                if canvas_token and school_domain:
                    # Store the credentials
                    ctx.storage.set("canvas_token", canvas_token)
                    ctx.storage.set("school_domain", school_domain)
                    ctx.logger.info("Canvas credentials extracted and stored")
                    
                    # Store initialization state
                    ctx.storage.set("waiting_for_init", "true")
                    
                    # Initialize RAG system with both token and domain
                    await send_response_to_user(ctx, "Canvas credentials received and stored. Initializing RAG system...")
                    
                    # Send initialization request
                    await ctx.send(
                        QUERY_AGENT_ADDRESS,
                        RequestResponse(
                            request=f"init_rag,{canvas_token},{school_domain}",
                            response=""
                        )
                    )
                    return
                else:
                    # Ask user for credentials with example
                    await send_response_to_user(
                        ctx,
                        "I need your Canvas API token and school domain to help you. For example:\n\n"
                        "My token is 1234~abcd... and my school is berkeley"
                    )
            else:
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
    
    # Check if we're waiting for initialization response
    if ctx.storage.get("waiting_for_init") == "true" and sender == QUERY_AGENT_ADDRESS:
        ctx.storage.set("waiting_for_init", "")
        if "successfully" in msg.response:
            await send_response_to_user(
                ctx,
                "Thanks for providing your Canvas credentials! I'm setting up the system to help you with your coursework. Please ask me anything about your courses!"
            )
        else:
            await send_response_to_user(
                ctx,
                "There was an issue initializing the system. Please try again later."
            )
        return
    
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
