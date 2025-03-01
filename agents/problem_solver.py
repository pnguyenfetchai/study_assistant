from uagents import Agent, Context, Protocol, Model
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

QUERY_AGENT_ADDRESS = os.getenv("QUERY_AGENT_ADDRESS")
PRIME_AGENT_ADDRESS = os.getenv("PRIME_AGENT_ADDRESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


class QueryRequest(Model):
    query: str

class QueryResponse(Model):
    response: str

problem_protocol = Protocol("Problem Solving")
query_protocol = Protocol("Query Handling")

problem_solver_agent = Agent(
    name="problem_solver_agent",
    port=8004,
    endpoint=["http://127.0.0.1:8004/submit"],
)


problem = {}

@problem_protocol.on_message(model=QueryRequest)
async def solve_problem(ctx: Context, sender: str, message: QueryRequest):
    ctx.logger.info(f"Received problem-solving request: {message.query}")

    problem[sender] = message.query
    
    query_text = f"Provide relevant materials for solving: {message.query} DO NOT ATTEMPT TO SOLVE THE PROBLEM AND ONLY PROVIDE THE NECESSARY CONTEXT FROM THE KNOWLEDGE BASE THAT HELP SOLVING THE PROBLEM"
    await ctx.send(QUERY_AGENT_ADDRESS, QueryRequest(query=query_text))

@query_protocol.on_message(model=QueryResponse)
async def receive_query_response(ctx: Context, sender: str, response: QueryResponse):
    ctx.logger.info(f"Received context from Query Agent: {response.response}")

    
    problem_solution = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Solve the given problem using relevant course materials."},
            {"role": "user", "content": f"Original Problem: {problem[PRIME_AGENT_ADDRESS]}\nContext: {response.response}"}
        ]
    )
    solution = problem_solution.choices[0].message.content
    
    ctx.logger.info(f"Sending problem solution: {solution}")
    await ctx.send(PRIME_AGENT_ADDRESS, QueryResponse(response=solution))

problem_solver_agent.include(problem_protocol)
problem_solver_agent.include(query_protocol)

if __name__ == "__main__":
    problem_solver_agent.run()
