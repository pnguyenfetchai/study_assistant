import json
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from uagents.query import query
from uagents.envelope import Envelope
from uagents import Model
from dotenv import load_dotenv
import asyncio


# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_ADDRESS = os.getenv("PRIME_AGENT_ADDRESS")

class RequestResponse(Model):
    request: str
    response: str
    user: str = None

async def agent_query(req):
    try:
        print(f"Sending query to agent at {AGENT_ADDRESS}...")

        if not AGENT_ADDRESS:
            raise HTTPException(status_code=500, detail="PRIME_AGENT_ADDRESS is not set.")

        response = await query(destination=AGENT_ADDRESS, message=req, timeout=10)
        # if isinstance(response, Envelope):
        #     data = json.loads(response.decode_payload())
        #     return data["text"]
        
        return response

    except Exception as e:
        print(f"Error during agent query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit")
async def submit_query(request: Request):
    if os.path.exists("response.txt"):
        os.remove("response.txt")
    if os.path.exists("visualization.txt"):
        os.remove("visualization.txt")
    res = None
    try:
        print("Received request:", request)    
        model = RequestResponse.model_validate(await request.json())
        task = asyncio.create_task(agent_query(model))

        for _ in range(1000):  
            if os.path.exists("response.txt") or os.path.exists("visualization.txt"):
                print("File appeared! Cancelling agent query.")
                task.cancel()  # Cancel the background agent_query
                break
            await asyncio.sleep(0.1)

        # if not task.done():
        #     try:
        #         response = await task
        #         print("Agent returned response:", response)
        #     except asyncio.CancelledError:
        #         print("agent_query was cancelled because file appeared early.")


        if os.path.exists("response.txt"):
            with open("response.txt", "r") as file:
                res = file.read()
            print("Response read from file:", res)
            return {"type": "text", "data": res}
        elif os.path.exists("visualization.txt"):
            with open("visualization.txt", "r") as file:
                res = file.read()
                return {"type": "image", "data": res} 
            
        else:
            raise HTTPException(status_code=500, detail="Response file not found.")        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
