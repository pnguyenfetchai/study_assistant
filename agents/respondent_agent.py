from uagents import Agent, Context, Protocol, Model
from typing import Dict, List, Any
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from dotenv import load_dotenv
import os
from openai import OpenAI
import re
import asyncio

load_dotenv()

USER_AGENT_ADDRESS = os.getenv("USER_AGENT_ADDRESS")
RESPONDENT_AGENT_ADDRESS = os.getenv("RESPONDENT_AGENT_ADDRESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VISUALIZATION_AGENT_ADDRESS = os.getenv("VISUALIZATION_AGENT_ADDRESS")

client = OpenAI(api_key=OPENAI_API_KEY)

# Message models
class RequestResponse(Model):
    request: str
    response: str

class ToolRequest(Model):
    params: Dict[str, Any]

class ToolResponse(Model):
    result: Any



# Create the respondent agent instance
respondent_agent = Agent(
    name="respondent_agent",
    port=8007,
    endpoint=["http://127.0.0.1:8007/submit"]
)

# Respondent agent setup
respondent_protocol = Protocol("response_analysis")

async def determine_tool_need(request: str, response: str) -> str:
    """Uses OpenAI to decide if visualization is needed."""
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that decides whether visualization is needed. Respond in this format only:\n\n'NO TOOL' (if no visualization is needed)\n\nOR\n\n'TOOL , tools is visualization' (if visualization is needed)."},
                {"role": "user", "content": f"Request: {request}\nResponse: {response}\nDo we need visualization?"}
            ]
        )
        decision = completion.choices[0].message.content.strip()
        print(f"Tool Decision: {decision}")
        return decision
    except Exception as e:
        print(f"Error determining tool need: {e}")
        return "NO TOOL"

@respondent_protocol.on_message(model=RequestResponse)
async def handle_response(ctx: Context, sender: str, msg: RequestResponse):
    """Handle incoming responses from the analyzer agent."""
    ctx.logger.info(f"Received response from {sender}")
    
    try:
        # Check if visualization is needed
        decision = await determine_tool_need(msg.request, msg.response)
        decision = decision.strip().strip("'").strip('"')
        
        if decision.startswith("TOOL"):
            # Extract numbers from response for visualization
            # numbers = [float(num) for num in re.findall(r"\d+\.\d+|\d+", msg.response)]
            
            # Send visualization request

            ctx.logger.info("radindra", type(msg.response))
            await ctx.send(VISUALIZATION_AGENT_ADDRESS, ToolRequest(
                params={'data': msg.response, 'title': 'Generated Visualization'}
            ))
            
            # ctx.logger.info(f"Sent visualization request for {len(numbers)} numbers")
        else:
            ctx.logger.info("No visualization needed")
            await ctx.send(USER_AGENT_ADDRESS, RequestResponse(
            request=msg.request, 
            response=msg.response
        ))
        
        
    except Exception as e:
        ctx.logger.error(f"Error processing response: {e}")

@respondent_agent.on_message(model=ToolResponse)
async def handle_visualization_response(ctx: Context, sender: str, response: ToolResponse):
    """Handle visualization responses from tool agents."""
    ctx.logger.info(f"Received visualization response from  visualization agent")

    img_data = base64.b64decode(response.result)
    with open("visualization_output.png", "wb") as f:
        f.write(img_data)

    ctx.logger.info("Saved visualization image as visualization_output.png")

    await ctx.send(USER_AGENT_ADDRESS, RequestResponse(request="filler", response=response.result))

respondent_agent.include(respondent_protocol)

if __name__ == "__main__":
    respondent_agent.run()

