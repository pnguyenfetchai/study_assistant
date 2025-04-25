from uagents import Agent, Context, Protocol, Model
from dotenv import load_dotenv
import os
from fastapi import HTTPException


load_dotenv()

# Agent addresses
CANVAS_AGENT_ADDRESS = "agent1q0uvz4t5tv8dcahzwgks4pymps98ua9m2rnpfguxrzk55zv0xg2p2ye834v"

class QueryRequest(Model):
    query: str

class RequestResponse(Model):
    request: str
    response: str


user_agent = Agent(
    name="user_agent",
    seed="user_agent_seed",
    port=8080,
    endpoint=["http://localhost:8080/submit"],
    mailbox=True
)

@user_agent.on_rest_post("/query",RequestResponse, RequestResponse)
async def submit_query(ctx: Context, data: RequestResponse) -> RequestResponse: 
    ctx.logger.info(f"Sending query to Canvas Agent: {data.request}")
    
    try:
        response, _ = await ctx.send_and_receive(
            destination=CANVAS_AGENT_ADDRESS,
            message=RequestResponse(request=data.request, response=""),
            response_type=RequestResponse,
            timeout=300
        )

        ctx.logger.info(f"Received response from Canvas Agent: {response.response}")
        return RequestResponse(request=data.request, response=response.response)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout from Canvas Agent")

# Run with REST enabled
if __name__ == "__main__":
    user_agent.run()

