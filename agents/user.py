from uagents import Agent, Context, Protocol, Model
from dotenv import load_dotenv
import os
load_dotenv()

PRIME_AGENT_ADDRESS = os.getenv("PRIME_AGENT_ADDRESS")

class QueryRequest(Model):
    query: str

class RequestResponse(Model):
    request: str
    response: str


user_agent = Agent(
    name="user_agent",
    port=8005,
    endpoint=["http://127.0.0.1:8005/submit"],
)

@user_agent.on_event("startup")  
async def send_initial_query(ctx: Context):
    query_text = "tell me about the time of the internship fair in spring 2026"
    ctx.logger.info(f"Sending query to Prime Agent: {query_text}")
    await ctx.send(PRIME_AGENT_ADDRESS, RequestResponse(request=query_text, response=""))

@user_agent.on_message(model=RequestResponse)
async def receive_query_response(ctx: Context, sender: str, response: RequestResponse):
    ctx.logger.info(f"Received response: {response.response}")


if __name__ == "__main__":
    user_agent.run()
