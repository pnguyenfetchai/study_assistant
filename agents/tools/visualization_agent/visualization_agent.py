from uagents import Agent, Context, Protocol, Model
from typing import Dict, Any
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
from openai import OpenAI
import sys
sys.path.append('..')
from dotenv import load_dotenv
import json

class ToolRequest(Model):
    params: Dict[str, Any]

class ToolResponse(Model):
    result: Any

# Load OpenAI API

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

visualization_agent = Agent(
    name="visualization_agent",
    port=8009,
    endpoint=["http://127.0.0.1:8009/submit"], 
    mailbox=True
)

visualization_protocol = Protocol("visualization")

async def extract_data_with_llm(instruction: str) -> tuple[list, list]:
    """Use GPT to extract labels and numbers for pie chart."""
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Extract data for a pie chart from the text. Return in this format: {\"labels\": [list of labels], \"values\": [list of numbers]}"},
            {"role": "user", "content": instruction}
        ]
    )
    try:
        text = completion.choices[0].message.content
        print(" LLM raw output:", text)
        
   
        data = json.loads(text)
        
        values = [float(v) for v in data['values']]
        labels = data['labels']
        
        min_len = min(len(values), len(labels))
        return labels[:min_len], values[:min_len]
        
    except Exception as e:
        print(f"Error parsing data: {e}")
        return [], []

@visualization_protocol.on_message(model=ToolRequest)
async def handle_visualization(ctx: Context, sender: str, msg: ToolRequest):
    """Handle visualization requests."""
    try:
        instruction = str(msg.params.get('data'))
        labels, values = await extract_data_with_llm(instruction)
        
        if not values or len(values) == 0:
            raise ValueError("No data provided for visualization")
            
        # Create pie chart
        plt.figure(figsize=(10, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title(msg.params.get('title', 'Data Distribution'))
        plt.legend(labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        result = base64.b64encode(buffer.read()).decode()

        await ctx.send(sender, ToolResponse(result=result))

    except Exception as e:
        ctx.logger.error(f"Error in visualization: {e}")
        await ctx.send(sender, ToolResponse(result=None))

visualization_agent.include(visualization_protocol)

if __name__ == "__main__":
    visualization_agent.run()
