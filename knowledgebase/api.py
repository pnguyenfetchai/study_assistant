from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import json


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CanvasCredentials(BaseModel):
    token: str
    school: str


@app.post("/api/canvas-token")
async def save_canvas_credentials(credentials: CanvasCredentials) -> Dict[str, str]:
    try:


        # Save credentials to file
        creds_data = {
            "token": credentials.token,
            "school": credentials.school
        }
        
        # Save to credentials.txt in JSON format
        with open("credentials.txt", "w") as f:
            json.dump(creds_data, f, indent=4)
        
        return {
            "status": "success", 
            "message": f"Successfully connected to Canvas for {credentials.school} and saved credentials"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to Canvas: {str(e)}"
        )

@app.get("/")
async def root():
    return {"message": "Study Assistant API"}
