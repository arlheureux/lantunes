from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, User
from auth import hash_password, verify_password, create_access_token, create_refresh_token, verify_refresh_token
from dependencies import get_optional_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class SetupAdminRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/setup", response_model=TokenResponse)
def setup_first_admin(req: SetupAdminRequest, db: Session = Depends(get_db)):
    """Setup first admin user - only works when no active admin exists"""
    # Check if there are any ACTIVE admin users
    active_admin_count = db.query(User).filter(
        User.role == "admin",
        User.status == "active"
    ).count()
    
    if active_admin_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin already exists. Please login."
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
    refresh_token = create_refresh_token({"user_id": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "status": user.status
        }
    )


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user - requires admin to approve, except when no active admin exists"""
    # Check if username exists
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if there are any ACTIVE admin users
    active_admin_count = db.query(User).filter(
        User.role == "admin",
        User.status == "active"
    ).count()
    
    if active_admin_count == 0:
        # No active admin exists - make this user admin and active
        user = User(
            username=req.username,
            password_hash=hash_password(req.password),
            role="admin",
            status="active"
        )
    else:
        # Active admin exists - require approval
        user = User(
            username=req.username,
            password_hash=hash_password(req.password),
            role="user",
            status="pending"
        )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Only return token if user is active
    if user.status == "active":
        access_token = create_access_token({"user_id": user.id, "username": user.username})
        refresh_token = create_refresh_token({"user_id": user.id})
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "status": user.status
            }
        )
    
    return TokenResponse(
        access_token="",
        refresh_token="",
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "status": user.status,
            "message": "Registration successful! You are the first user and have been granted admin access."
        }
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login with username and password"""
    user = db.query(User).filter(User.username == req.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if user.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval. Please wait for admin to approve."
        )
    
    if user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated."
        )
    
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    refresh_token = create_refresh_token({"user_id": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "status": user.status
        }
    )


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not active"
        )
    
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    new_refresh_token = create_refresh_token({"user_id": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "status": user.status
        }
    )


@router.get("/status")
def auth_status(db: Session = Depends(get_db)):
    """Check if admin exists - public endpoint for login page"""
    active_admin_count = db.query(User).filter(
        User.role == "admin",
        User.status == "active"
    ).count()
    return {"needs_setup": active_admin_count == 0}


@router.get("/me")
def get_me(current_user: Optional[User] = Depends(get_optional_user)):
    """Get current user info - returns null if not authenticated"""
    if not current_user:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "status": current_user.status
    }