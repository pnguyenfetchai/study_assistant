from uagents import Agent, Context, Protocol, Model
from dotenv import load_dotenv
import os


load_dotenv()

QUERY_AGENT_ADDRESS = os.getenv("QUERY_AGENT_ADDRESS")

class QueryRequest(Model):
    query: str

class QueryResponse(Model):
    response: str

prime_agent = Agent(
    name="prime_agent",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"],
)

query_protocol = Protocol("Query Prime Agent")

@query_protocol.on_message(model=QueryResponse) 
async def receive_query_response(ctx: Context, sender: str, response: QueryResponse):
    ctx.logger.info(f"Prime Agent received response: {response.response}")

prime_agent.include(query_protocol)

@prime_agent.on_event("startup")  
async def send_initial_query(ctx: Context):
    query_text = "what are the classes I am taking this semester"
    ctx.logger.info(f"Sending initial query: {query_text}")
    await ctx.send(QUERY_AGENT_ADDRESS, QueryRequest(query=query_text))

if __name__ == "__main__":
    prime_agent.run()
