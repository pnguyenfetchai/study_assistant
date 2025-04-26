from uagents import Agent, Context
from dotenv import load_dotenv
import os
from openai import OpenAI
import sys
sys.path.append('..')
from query_protocol import query_protocol, RequestResponse
from problem_protocol import problem_protocol, QueryRequest

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent addresses
QUERY_AGENT_ADDRESS = "agent1qvejzzpsu5zxqhm6elej0a9g680ayadg7a4hnsvw20qf3kqhtqrhg3qjwq6"
CANVAS_AGENT_ADDRESS = "agent1q0uvz4t5tv8dcahzwgks4pymps98ua9m2rnpfguxrzk55zv0xg2p2ye834v"
ANALYZER_AGENT_ADDRESS = "agent1qdkma7e770uq64u8zkcyvcum2sgzz6k5vj3xf5mt97wd63fpp9w6zedrr7z"

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

problem_solver_agent.include(problem_protocol)
problem_solver_agent.include(query_protocol)

if __name__ == "__main__":
    problem_solver_agent.run()
