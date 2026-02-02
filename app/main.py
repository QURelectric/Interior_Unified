import asyncio
import json
import threading
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from app.state import vehicle_state, state_lock
from app.canbus import can_loop
from app.mqtt import mqtt_loop

#### main.py ####
# DRIVER'S DISPLAY
# This file holds the async functions and the inline HTML for the Fastapi webpage


app = FastAPI()

templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    threading.Thread(target=can_loop, daemon=True).start()
    threading.Thread(target=mqtt_loop, daemon=True).start()

    
@app.get("/", response_class=HTMLResponse)
async def driver_page(request: Request):
    return templates.TemplateResponse(
        "driver.html",
        {"request": request}
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            with state_lock:
                payload = json.dumps(vehicle_state)

            await websocket.send_text(payload)
            await asyncio.sleep(1/30)  # 30 Hz update
    except Exception:
        pass
