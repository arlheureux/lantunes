from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from auth import verify_token

# Public endpoints that don't require auth
PUBLIC_ENDPOINTS = [
    "/api/auth/login",
    "/api/auth/setup",
    "/api/auth/status",
    "/api/config",
    "/api/playback/stream/",
    "/api/library/artwork/",
    "/api/library/tracks/batch",
    "/api/library/scan/stream",
    "/api/library/fetch-artwork/stream",
    "/api/config/migrate",
    "/docs",
    "/openapi.json",
    "/redoc"
]

# Paths that are always public (non-API)
PUBLIC_PATHS = ["/", "/index.html", "/login.html", "/favicon.ico", "/health", "/health/ready"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Handle OPTIONS preflight requests (CORS)
        if request.method == "OPTIONS" and path.startswith("/api/"):
            return JSONResponse(status_code=200, content={})
        
        # Always allow public paths
        if path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Always allow public API endpoints (exact match or prefix for stream)
        is_public = any(path.startswith(public) for public in PUBLIC_ENDPOINTS)
        if is_public:
            return await call_next(request)
        
        # For other API endpoints, check auth
        if path.startswith("/api/"):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )
            
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            if not payload:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"}
                )
        
        return await call_next(request)