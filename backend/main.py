import sys
import os
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from api import library, playback, playlists, config
from api import auth, users
from websocket import websocket_endpoint
from database import User
from auth import verify_access_token

app = FastAPI(title="LanTunes")

# Public endpoints that don't require auth
PUBLIC_ENDPOINTS = [
    "/api/auth/login",
    "/api/auth/setup",
    "/api/auth/refresh",
    "/docs",
    "/openapi.json",
    "/redoc"
]

# Static/public paths that don't require auth
PUBLIC_PATHS = [
    "/login.html"
]

# Endpoints that should never require auth (for streaming etc)
ALWAYS_PUBLIC = ["/ws", "/api/playback/stream", "/api/library/artwork"]

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    
    # Always allow certain paths
    if any(path.startswith(p) for p in ALWAYS_PUBLIC):
        return await call_next(request)
    
    # Allow public paths (like login.html)
    if any(path == p or path.startswith(p) for p in PUBLIC_PATHS):
        return await call_next(request)
    
    # Allow public API endpoints
    if any(path == p or path.startswith(p + "/") for p in PUBLIC_ENDPOINTS):
        return await call_next(request)
    
    # For all other endpoints, check auth
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # For HTML pages, redirect to login
        if path.endswith('.html') or path == '/' or not path.startswith('/api'):
            return HTMLResponse(open(os.path.join(frontend_path, 'login.html')).read())
        return HTMLResponse(
            content='{"detail":"Authentication required"}',
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        if path.endswith('.html') or path == '/' or not path.startswith('/api'):
            return HTMLResponse(open(os.path.join(frontend_path, 'login.html')).read())
        return HTMLResponse(
            content='{"detail":"Invalid or expired token"}',
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Attach user to request state for later use
    request.state.user_id = payload.get("user_id")
    request.state.username = payload.get("username")
    
    return await call_next(request)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(library.router)
app.include_router(playback.router)
app.include_router(playlists.router)
app.include_router(config.router)

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket_endpoint(websocket)

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
index_path = os.path.join(frontend_path, "index.html")
login_path = os.path.join(frontend_path, "login.html")

@app.get("/")
async def root():
    # Check if user has valid token, otherwise redirect to login
    return HTMLResponse(open(index_path).read())

@app.get("/login.html")
async def serve_login():
    return HTMLResponse(open(login_path).read())

@app.get("/{path:path}")
async def serve_frontend(path: str):
    file_path = os.path.join(frontend_path, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(open(index_path).read())