from uagents import Agent, Context, Model
from typing import Dict, List, Any
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from dotenv import load_dotenv
import os
from openai import OpenAI
import re
import asyncio
from query_protocol import query_protocol, QueryRequest, RequestResponse
from visualization_protocol import visualization_protocol, ImageResponse

load_dotenv()

CANVAS_AGENT_ADDRESS = os.getenv("CANVAS_AGENT_ADDRESS")
RESPONDENT_AGENT_ADDRESS = os.getenv("RESPONDENT_AGENT_ADDRESS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VISUALIZATION_AGENT_ADDRESS = os.getenv("VISUALIZATION_AGENT_ADDRESS")

client = OpenAI(api_key=OPENAI_API_KEY)


class ToolRequest(Model):
    params: Dict[str, Any]

class ToolResponse(Model):
    result: Any



respondent_agent = Agent(
    name="respondent_agent",
    port=8007,
    endpoint=["http://127.0.0.1:8007/submit"], 
    mailbox=True
)


async def determine_tool_need(request: str, response: str) -> str:
    """Uses OpenAI to decide if visualization is needed."""
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """You are an AI assistant that determines whether a visualization (e.g., a chart, diagram, graph, or image) is needed to help the student understand the response better.

                Follow these rules when making a decision:
                1. If the response explains concepts, definitions, or theoretical material without any need for visual aid — respond with:
                NO TOOL

                2. If the request involves data, trends, comparisons, processes, categories, diagrams, timelines, charts, or anything that would *clearly benefit* from a visual representation — respond with:
                TOOL , tools is visualization

                Only return **one** of the two responses above exactly — no extra words or punctuation.

                Examples of when to say TOOL:
                - "Can you show me the architecture of this system?"
                - "Create a pie chart of time spent per topic."
                - "Compare CPU and memory usage."

                Examples of when to say NO TOOL:
                - "What is polymorphism in OOP?"
                - "Explain the difference between HTTP and HTTPS."
                - "What are the advantages of unit testing?"
                - "What are my upcoming assignments and their deadline?"
                Do not try to explain your decision — just output the label.
                """},
                {"role": "user", "content": f"Request: {request}\nResponse: {response}\nDo we need visualization?"}
            ]
        )
        decision = completion.choices[0].message.content.strip()
        print(f"Tool Decision: {decision}")
        return decision
    except Exception as e:
        print(f"Error determining tool need: {e}")
        return "NO TOOL"
    


@query_protocol.on_message(model=RequestResponse)
async def handle_response(ctx: Context, sender: str, msg: RequestResponse):
    """Handle incoming responses from the analyzer agent."""
    ctx.logger.info(f"Received response from {sender}")
    ctx.storage.set("last_response", msg.response)
    ctx.storage.set("last_request", msg.request)

    
    try:
        # Check if visualization is needed
        decision = await determine_tool_need(msg.request, msg.response)
        decision = decision.strip().strip("'").strip('"')
        ctx.logger.info(f"Tool decision: {decision}")
        
        if decision.startswith("TOOL"):
            # Extract numbers from response for visualization
            # numbers = [float(num) for num in re.findall(r"\d+\.\d+|\d+", msg.response)]
            
            # Send visualization request

            ctx.logger.info(f"Response type: {type(msg.response)}")
            ctx.logger.info(f"Response content: {msg.response}")

            if msg.response:
                # for now just use pie chart tool anyway when tool is needed
                # will create more tool in the future by ultilizing dictiontionary instead of title and data
                await ctx.send(VISUALIZATION_AGENT_ADDRESS, ToolRequest(
                    params={'data': msg.response, 'title': 'Generated Visualization'}
                ))
            else:
                ctx.logger.warning("Received empty response, skipping visualization")
            
            # ctx.logger.info(f"Sent visualization request for {len(numbers)} numbers")
        else:
            ctx.logger.info("No visualization needed")
            await ctx.send(CANVAS_AGENT_ADDRESS, RequestResponse(
            request=msg.request, 
            response=msg.response
            ))
        
        
    except Exception as e:
        ctx.logger.error(f"Error processing response: {e}")

@respondent_agent.on_message(model=ToolResponse)
async def handle_visualization_response(ctx: Context, sender: str, response: ToolResponse):
    """Handle visualization responses from tool agents."""
    ctx.logger.info(f"Received visualization response from visualization agent")
    
    if response.result:
        # The response.result contains base64 encoded PNG image
        await ctx.send(CANVAS_AGENT_ADDRESS, ImageResponse(
            request=ctx.storage.get("last_request"),
            image_data=response.result,
            image_type='png',
            content_type='image/png'
        ))
    else:
        await ctx.send(CANVAS_AGENT_ADDRESS, RequestResponse(
            request=ctx.storage.get("last_request"),
            response="unable to generate visualization"
        ))


respondent_agent.include(query_protocol)
respondent_agent.include(visualization_protocol)

if __name__ == "__main__":
    respondent_agent.run()

