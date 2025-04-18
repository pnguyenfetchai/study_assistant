from uagents import Agent, Context, Protocol, Model
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

QUERY_AGENT_ADDRESS = os.getenv("QUERY_AGENT_ADDRESS")
PROBLEM_SOLVER_AGENT_ADDRESS = os.getenv("PROBLEM_SOLVER_AGENT_ADDRESS")
USER_AGENT_ADDRESS = os.getenv("USER_AGENT_ADDRESS")
ANALYZER_AGENT_ADDRESS = os.getenv("ANALYZER_AGENT_ADDRESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

class QueryRequest(Model):
    query: str

class RequestResponse(Model):
    request: str
    response: str


query_protocol = Protocol("Query Handling")
problem_protocol = Protocol("Problem Solving")



prime_agent = Agent(
    name="prime_agent",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"],
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



@prime_agent.on_message(model=RequestResponse)
async def handle_user_query(ctx: Context, sender: str, message: RequestResponse):
    print(f"Debug - Handler received message from {sender}: {message}")
    ctx.logger.info(f"Received query: {message}")
    classification = classify_query_with_llm(message.request)
    ctx.logger.info(f"grimace egg: {classification}")    

    if message.response and sender != ANALYZER_AGENT_ADDRESS:
        ctx.logger.info(f"Received response from {sender}: {message.request}")
        await ctx.send(USER_AGENT_ADDRESS, message)
    elif classification == "general":
        ctx.logger.info(f"Forwarding general query to Query Agent: {message.request}")
        await ctx.send(QUERY_AGENT_ADDRESS, message)
    else:
        ctx.logger.info(f"Forwarding problem-solving query to Problem Solver Agent: {message.request}")
        await ctx.send(PROBLEM_SOLVER_AGENT_ADDRESS, QueryRequest(query=message.request))

prime_agent.include(query_protocol)
prime_agent.include(problem_protocol)

if __name__ == "__main__":
    prime_agent.run()
