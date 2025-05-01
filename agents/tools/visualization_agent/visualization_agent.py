from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol, Model
from typing import Dict, Any
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
from openai import OpenAI
import sys
sys.path.append('../..')
from dotenv import load_dotenv
import json
from chat_protocol import chat_proto
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent, ChatAcknowledgement

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
    seed="visualization agent secret phrase deployment",
    mailbox=True
)

visualization_protocol = Protocol("visualization")

@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    try:
        # Send acknowledgment first
        await ctx.send(
            sender,
            ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id)
        )

        # Extract text content from the message
        text_content = next((content.text for content in msg.content if isinstance(content, TextContent)), None)
        if not text_content:
            error_msg = "No text content found in the message"
            ctx.logger.error(error_msg)
            await ctx.send(sender, ChatMessage(
                content=[TextContent(type="text", text=error_msg)],
                timestamp=datetime.now(),
                msg_id=uuid4()
            ))
            return

        ctx.logger.info(f"Received visualization request from {sender}: {text_content}")

        try:
            # Extract data for visualization
            labels, values = await extract_data_with_llm(text_content)
            
            # Create visualization
            plt.figure(figsize=(10, 6))
            plt.pie(values, labels=labels, autopct='%1.1f%%')
            plt.title('Data Visualization')
            
            # Save plot to bytes
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            plt.close()
            
            # Convert to base64
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            graphic = base64.b64encode(image_png).decode()
            
            # Send back the visualization
            response = f"Here's your visualization:\n![Visualization](data:image/png;base64,{graphic})"
            await ctx.send(sender, ChatMessage(
                content=[TextContent(type="text", text=response)],
                timestamp=datetime.now(),
                msg_id=uuid4()
            ))

        except Exception as e:
            error_msg = f"Error creating visualization: {str(e)}"
            ctx.logger.error(error_msg)
            await ctx.send(sender, ChatMessage(
                content=[TextContent(type="text", text=error_msg)],
                timestamp=datetime.now(),
                msg_id=uuid4()
            ))

    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        ctx.logger.error(error_msg)
        await ctx.send(sender, ChatMessage(
            content=[TextContent(type="text", text=error_msg)],
            timestamp=datetime.now(),
            msg_id=uuid4()
        ))

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
visualization_agent.include(chat_proto)

if __name__ == "__main__":
    visualization_agent.run()
