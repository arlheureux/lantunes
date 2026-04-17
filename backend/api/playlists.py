import sys
import os
import threading
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db, Playlist, PlaylistTrack, Track, DownloadJob
from typing import List, Optional
from datetime import datetime
from dependencies import get_current_user
from models import User

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.get("")
def get_playlists(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        playlists = db.query(Playlist).all()
    else:
        playlists = db.query(Playlist).filter(Playlist.user_id == current_user.id).all()
    result = []
    for p in playlists:
        track_count = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == p.id).count()
        result.append({"id": p.id, "name": p.name, "track_count": track_count, "created_at": p.created_at})
    return result


@router.get("/{playlist_id}")
def get_playlist(playlist_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if current_user.role != "admin" and playlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pt_list = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position).all()
    
    if not pt_list:
        return {"id": playlist.id, "name": playlist.name, "tracks": [], "created_at": playlist.created_at}
    
    track_ids = [pt.track_id for pt in pt_list]
    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
    tracks_map = {t.id: t for t in tracks}
    
    tracks = [tracks_map.get(pt.track_id).as_dict() for pt in pt_list if tracks_map.get(pt.track_id)]
    
    return {"id": playlist.id, "name": playlist.name, "tracks": tracks, "created_at": playlist.created_at}


def stream_zip(job_id: int):
    from database import SessionLocal
    import zipfile
    import io
    
    db = SessionLocal()
    try:
        job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
        if not job:
            return
        
        playlist = db.query(Playlist).filter(Playlist.id == job.playlist_id).first()
        if not playlist:
            job.status = "error"
            job.error = "Playlist not found"
            db.commit()
            return
        
        pt_list = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == job.playlist_id).order_by(PlaylistTrack.position).all()
        job.total = len(pt_list)
        db.commit()
        
        track_ids = [pt.track_id for pt in pt_list]
        tracks = db.query(Track).filter(Track.id.in_(track_ids)).all() if track_ids else []
        tracks_map = {t.id: t for t in tracks}
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, pt in enumerate(pt_list):
                track = tracks_map.get(pt.track_id)
                if track and track.path and os.path.exists(track.path):
                    filename = os.path.basename(track.path)
                    with open(track.path, 'rb') as f:
                        zf.writestr(filename, f.read())
                job.progress = i + 1
                db.commit()
        
        cache_dir = os.path.join(backend_dir, "cache", "downloads")
        os.makedirs(cache_dir, exist_ok=True)
        zip_path = os.path.join(cache_dir, f"playlist_{playlist.id}_{job.id}.zip")
        
        zip_buffer.seek(0)
        with open(zip_path, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        job.zip_path = zip_path
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        try:
            job.status = "error"
            job.error = str(e)
            db.commit()
        except:
            pass
    finally:
        db.close()


@router.post("/{playlist_id}/download/async")
def create_download_job(playlist_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if current_user.role != "admin" and playlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pt_list = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).all()
    if not pt_list:
        raise HTTPException(status_code=400, detail="Playlist is empty")
    
    job = DownloadJob(playlist_id=playlist_id, status="pending", total=len(pt_list))
    db.add(job)
    db.commit()
    db.refresh(job)
    
    thread = threading.Thread(target=stream_zip, args=(job.id,))
    thread.start()
    
    return {"job_id": job.id, "status": "pending"}


@router.get("/download/{job_id}")
def get_download_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "total": job.total,
        "error": job.error
    }


@router.get("/{playlist_id}/download")
def download_playlist(playlist_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import zipfile
    import io
    from fastapi.responses import Response
    
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if current_user.role != "admin" and playlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pt_list = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position).all()
    if not pt_list:
        raise HTTPException(status_code=400, detail="Playlist is empty")
    
    track_ids = [pt.track_id for pt in pt_list]
    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all() if track_ids else []
    tracks_map = {t.id: t for t in tracks}
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for pt in pt_list:
            track = tracks_map.get(pt.track_id)
            if not track:
                continue
            if not track.path or not os.path.exists(track.path):
                raise HTTPException(status_code=404, detail=f"Track file not found: {track.path}")
            filename = os.path.basename(track.path)
            with open(track.path, 'rb') as f:
                zf.writestr(filename, f.read())
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{playlist.name}.zip"'}
    )


@router.get("/{playlist_id}/download/tracks")
def get_download_tracks(playlist_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get list of track URLs for sequential download"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if current_user.role != "admin" and playlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pt_list = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position).all()
    if not pt_list:
        raise HTTPException(status_code=400, detail="Playlist is empty")
    
    track_ids = [pt.track_id for pt in pt_list]
    tracks = db.query(Track).filter(Track.id.in_(track_ids)).all() if track_ids else []
    tracks_map = {t.id: t for t in tracks}
    
    download_tracks = []
    for pt in pt_list:
        track = tracks_map.get(pt.track_id)
        if track and track.path and os.path.exists(track.path):
            download_tracks.append({
                "id": track.id,
                "title": track.title,
                "filename": os.path.basename(track.path),
                "url": f"/api/playback/stream/{track.id}",
                "format": track.file_format,
                "duration": track.duration
            })
    
    if not download_tracks:
        raise HTTPException(status_code=404, detail="No valid tracks found")
    
    return {"playlist": playlist.name, "count": len(download_tracks), "tracks": download_tracks}

@router.post("")
async def create_playlist(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = await request.json()
    name = data.get("name")
    track_ids = data.get("track_ids", [])
    
    if not name:
        raise HTTPException(status_code=400, detail="Playlist name required")
    
    playlist = Playlist(name=name, user_id=current_user.id)
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    
    for i, track_id in enumerate(track_ids):
        pt = PlaylistTrack(playlist_id=playlist.id, track_id=track_id, position=i)
        db.add(pt)
    db.commit()
    
    return {"id": playlist.id, "name": playlist.name}

@router.put("/{playlist_id}")
def update_playlist(playlist_id: int, name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if current_user.role != "admin" and playlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    playlist.name = name
    db.commit()
    return {"id": playlist.id, "name": playlist.name}

@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if current_user.role != "admin" and playlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).delete()
    db.delete(playlist)
    db.commit()
    return {"deleted": True}

@router.post("/{playlist_id}/tracks")
def add_track_to_playlist(playlist_id: int, track_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    if current_user.role != "admin" and playlist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if track already exists in playlist
    existing = db.query(PlaylistTrack).filter(
        PlaylistTrack.playlist_id == playlist_id,
        PlaylistTrack.track_id == track_id
    ).first()
    if existing:
        return {"added": True, "duplicate": True}
    
    max_pos = db.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist_id).count()
    pt = PlaylistTrack(playlist_id=playlist_id, track_id=track_id, position=max_pos)
    db.add(pt)
    db.commit()
    return {"added": True}