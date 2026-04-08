from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db, User
from auth import create_access_token, verify_password, hash_password

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class SetupRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """Login with username and password"""
    user = db.query(User).filter(User.username == req.username).first()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active"
        )
    
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    )

@router.post("/setup", response_model=TokenResponse)
@limiter.limit("3/minute")
def setup(request: Request, req: SetupRequest, db: Session = Depends(get_db)):
    """Create first admin user - only when no admin exists"""
    admin_count = db.query(User).filter(User.role == "admin", User.status == "active").count()
    if admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin already exists"
        )
    
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role="admin",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    )

@router.get("/status")
def auth_status(db: Session = Depends(get_db)):
    """Check if admin exists - public endpoint"""
    admin_count = db.query(User).filter(User.role == "admin", User.status == "active").count()
    return {"needs_setup": admin_count == 0}