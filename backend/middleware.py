from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from auth import verify_token

# Public endpoints that don't require auth (keep minimal!)
PUBLIC_ENDPOINTS = [
    "/api/auth/login",       # REQUIRED: users must login
    "/api/auth/setup",      # REQUIRED: first-time setup
]

# Paths that are always public (non-API)
PUBLIC_PATHS = ["/", "/index.html", "/login.html", "/favicon.ico", "/health", "/health/ready"]

# Media paths that can use token as query param
MEDIA_PATHS = [
    "/api/playback/stream/",
    "/api/library/artwork/",
    "/api/library/artwork/artist/",
]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Always allow public paths
        if path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Always allow public API endpoints
        is_public = any(path.startswith(public) for public in PUBLIC_ENDPOINTS)
        if is_public:
            return await call_next(request)
        
        # For media paths, also allow token as query param
        is_media = any(path.startswith(media) for media in MEDIA_PATHS)
        
        # For other API endpoints, check auth
        if path.startswith("/api/"):
            auth_header = request.headers.get("Authorization")
            token = None
            
            # Try query param for media
            if is_media:
                token = request.query_params.get("token")
            
            # Or try Bearer header
            if not token and auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )
            
            payload = verify_token(token)
            if not payload:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"}
                )
        
        return await call_next(request)