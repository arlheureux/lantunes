from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Favorite, Track
from auth import get_current_user
from models import User

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
def get_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    result = []
    for f in favorites:
        track = db.query(Track).filter(Track.id == f.track_id).first()
        if track:
            result.append({
                "id": track.id,
                "title": track.title,
                "artist_id": track.artist_id,
                "album_id": track.album_id,
                "duration": track.duration,
                "created_at": f.created_at.isoformat() if f.created_at else None
            })
    return result


@router.post("/{track_id}")
def add_favorite(track_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.track_id == track_id
    ).first()
    
    if existing:
        return {"favorite": True}
    
    favorite = Favorite(user_id=current_user.id, track_id=track_id)
    db.add(favorite)
    db.commit()
    return {"favorite": True}


@router.delete("/{track_id}")
def remove_favorite(track_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.track_id == track_id
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    db.delete(favorite)
    db.commit()
    return {"favorite": False}


@router.get("/check/{track_id}")
def check_favorite(track_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.track_id == track_id
    ).first()
    return {"is_favorite": favorite is not None}