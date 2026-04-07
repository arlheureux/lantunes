from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User
from dependencies import get_current_admin
from datetime import datetime

router = APIRouter(prefix="/api/auth/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    status: str
    created_at: datetime
    approved_by: int | None
    approved_at: datetime | None

    class Config:
        from_attributes = True


@router.get("")
def list_users(
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all users (admin only)"""
    query = db.query(User)
    
    if status_filter:
        query = query.filter(User.status == status_filter)
    
    users = query.order_by(User.created_at.desc()).all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "status": u.status,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "approved_by": u.approved_by,
            "approved_at": u.approved_at.isoformat() if u.approved_at else None
        }
        for u in users
    ]


@router.post("/{user_id}/approve")
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Approve a pending user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already active"
        )
    
    user.status = "active"
    user.approved_by = current_user.id
    user.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"User {user.username} approved successfully"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete/reject a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    return {"message": f"User {username} deleted successfully"}