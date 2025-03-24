from uagents import Agent, Context, Protocol, Model
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PRIME_AGENT_ADDRESS = os.getenv("PRIME_AGENT_ADDRESS")
RESPONDENT_AGENT_ADDRESS = os.getenv("RESPONDENT_AGENT_ADDRESS")
USER_AGENT_ADDRESS = os.getenv("USER_AGENT_ADDRESS")

client = OpenAI(api_key=OPENAI_API_KEY)

class RequestResponse(Model):
    request: str
    response: str

class QueryRequest(Model):
    query: str

protocol = Protocol("query_analysis")

@protocol.on_message(model=RequestResponse)
async def analyze_query(ctx: Context, sender: str, msg: RequestResponse):
    """Compares the response with the original request and forwards accordingly."""
    ctx.logger.info(f"Received query analysis request from {sender}")
    ctx.logger.info(f"ryan pham: {msg.request} |||| {msg.response}")
    
    is_correct = await check_response(msg.request, msg.response)
    
    if is_correct:
        ctx.logger.info("Response is correct. Forwarding to respondent agent for tool analysis.")
        await ctx.send(RESPONDENT_AGENT_ADDRESS, RequestResponse(request=msg.request, response=msg.response))
    else:
        ctx.logger.info("Response is incorrect. Forwarding to prime agent for reevaluation.")
        await ctx.send(PRIME_AGENT_ADDRESS, RequestResponse(request=msg.request, response=msg.response))

async def check_response(question: str, answer: str) -> bool:
    """Uses OpenAI to evaluate whether the response is correct."""
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that verifies whether an answer correctly addresses a given question."},
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
    endpoint=["http://127.0.0.1:8006/submit"]
)

# Attach the protocol separately
analyzer_agent.include(protocol)

if __name__ == "__main__":
    analyzer_agent.run()