import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db, Playlist, PlaylistTrack, Track
from typing import List, Optional

router = APIRouter(prefix="/api/playlists", tags=["playlists"])

@router.get("")
def get_playlists(db: Session = Depends(get_db)):
    playlists = db.query(Playlist).all()
    result = []
    for p in playlists:
        track_count = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == p.id).count()
        result.append({"id": p.id, "name": p.name, "track_count": track_count, "created_at": p.created_at})
    return result

@router.get("/{playlist_id}")
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    pt_list = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position).all()
    tracks = []
    for pt in pt_list:
        track = db.query(Track).filter(Track.id == pt.track_id).first()
        if track:
            tracks.append(track.as_dict())
    
    return {"id": playlist.id, "name": playlist.name, "tracks": tracks, "created_at": playlist.created_at}

@router.post("")
def create_playlist(request: Request, db: Session = Depends(get_db)):
    data = request.json()
    name = data.get("name")
    track_ids = data.get("track_ids", [])
    
    if not name:
        raise HTTPException(status_code=400, detail="Playlist name required")
    
    playlist = Playlist(name=name)
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    
    # Add tracks if provided
    for i, track_id in enumerate(track_ids):
        pt = PlaylistTrack(playlist_id=playlist.id, track_id=track_id, position=i)
        db.add(pt)
    db.commit()
    
    return {"id": playlist.id, "name": playlist.name}

@router.put("/{playlist_id}")
def update_playlist(playlist_id: int, name: str, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    playlist.name = name
    db.commit()
    return {"id": playlist.id, "name": playlist.name}

@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    db.delete(playlist)
    db.commit()
    return {"deleted": True}

@router.post("/{playlist_id}/tracks")
def add_track_to_playlist(playlist_id: int, track_id: int, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    max_pos = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).count()
    pt = PlaylistTrack(playlist_id=playlist_id, track_id=track_id, position=max_pos)
    db.add(pt)
    db.commit()
    return {"added": True}