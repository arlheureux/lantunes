import sys
import os
import logging
from pathlib import Path
import yaml

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api import library, playback, playlists, config, favorites
from api import auth, users
from websocket import websocket_endpoint
from middleware import AuthMiddleware, PUBLIC_ENDPOINTS
import yaml

logger.info("Starting LanTunes backend")

# Load config
config_path = Path(__file__).parent.parent / "config.yaml"
production_mode = False
if config_path.exists():
    with open(config_path) as f:
        server_config = yaml.safe_load(f)
    production_mode = server_config.get("server", {}).get("production", False)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="LanTunes", docs_url="/docs" if not production_mode else None, redoc_url="/redoc" if not production_mode else None)

# CORS middleware - read origins from config.yaml
from fastapi.middleware.cors import CORSMiddleware
cors_origins = server_config.get("cors", {}).get("origins", ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/health/ready")
async def readiness_check():
    return {"status": "ready"}

# Add auth middleware
app.add_middleware(AuthMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(library.router)
app.include_router(playback.router)
app.include_router(playlists.router)
app.include_router(config.router)
app.include_router(favorites.router)

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket_endpoint(websocket)

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
index_path = os.path.join(frontend_path, "index.html")
login_path = os.path.join(frontend_path, "login.html")

@app.get("/")
async def root():
    return HTMLResponse(open(index_path).read())

@app.get("/login.html")
async def serve_login():
    return HTMLResponse(open(login_path).read())

@app.get("/{path:path}")
async def serve_frontend(path: str):
    if path == "login.html":
        return HTMLResponse(open(login_path).read())
    file_path = os.path.join(frontend_path, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(open(index_path).read())