import sys
import os
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from api import library, playback, playlists, config
from websocket import websocket_endpoint

app = FastAPI(title="LanTunes")

app.include_router(library.router)
app.include_router(playback.router)
app.include_router(playlists.router)
app.include_router(config.router)

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket_endpoint(websocket)

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
index_path = os.path.join(frontend_path, "index.html")

@app.get("/")
async def root():
    return HTMLResponse(open(index_path).read())

@app.get("/{path:path}")
async def serve_frontend(path: str):
    file_path = os.path.join(frontend_path, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(open(index_path).read())