import sys
import os
import tempfile
import logging
import atexit
import glob
import subprocess
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db, PlaybackState, Track
from playback import playback
from typing import List, Optional

router = APIRouter(prefix="/api/playback", tags=["playback"])

TRANSCODE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache", "transcode")
os.makedirs(TRANSCODE_DIR, exist_ok=True)


def cleanup_old_transcodes():
    """Remove transcoded files older than 1 hour"""
    import time
    now = time.time()
    for f in glob.glob(os.path.join(TRANSCODE_DIR, "*.mp3")):
        if os.path.getmtime(f) < now - 3600:
            try:
                os.remove(f)
            except OSError:
                pass


atexit.register(cleanup_old_transcodes)

class PlayRequest(BaseModel):
    track_id: Optional[int] = Field(default=None)
    queue: Optional[List[int]] = Field(default=None)

@router.get("/state")
def get_state(session: str = Query(None), db: Session = Depends(get_db)):
    # State is the same for all sessions - they all get stream_url
    return playback.get_state(db)

@router.post("/play")
def play(position: int = Query(None), track_id: int = None, queue: str = None, session: str = Query(None), db: Session = Depends(get_db)):
    """Execute play command on server, broadcast to all sessions"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    
    queue_list = [int(x) for x in queue.split(',')] if queue else None
    result = playback.play(db, position=position, track_id=track_id, queue=queue_list, session_id=player_session)
    playback.broadcast_playback_state()
    return result

@router.post("/pause")
def pause(position: int = Query(None), session: str = Query(None), db: Session = Depends(get_db)):
    """Execute pause command on server, broadcast to all sessions"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    result = playback.pause(db, position=position, session_id=player_session)
    playback.broadcast_playback_state()
    return result

@router.post("/stop")
def stop(session: str = Query(None), db: Session = Depends(get_db)):
    """Execute stop command on server, broadcast to all sessions"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    result = playback.stop(db, session_id=player_session)
    playback.broadcast_playback_state()
    return result

@router.post("/next")
def next_track(session: str = Query(None), db: Session = Depends(get_db)):
    """Execute next command on server, then broadcast state to all sessions"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    # Server executes next - updates state in DB
    result = playback.next(db, session_id=player_session)
    # Broadcast updated state to ALL sessions so UI updates
    playback.broadcast_playback_state()
    return result

@router.post("/previous")
def previous_track(session: str = Query(None), db: Session = Depends(get_db)):
    """Execute previous command on server, then broadcast state to all sessions"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    result = playback.previous(db, session_id=player_session)
    playback.broadcast_playback_state()
    return result

@router.post("/seek")
def seek(position: int = Query(...), session: str = Query(None), db: Session = Depends(get_db)):
    """Execute seek on server, broadcast to all sessions"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    result = playback.seek(db, position, session_id=player_session)
    playback.broadcast_playback_state()
    return result

@router.post("/position")
def update_position(position: int = Query(...), db: Session = Depends(get_db)):
    """Update current position while playing - broadcast to all sessions"""
    playback.update_position(db, position)
    playback.broadcast_playback_state()
    return {"status": "ok"}

@router.post("/volume")
def set_volume(volume: float = Query(..., ge=0.0, le=1.0), session: str = Query(None), db: Session = Depends(get_db)):
    """Execute volume on server, broadcast to all sessions"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    result = playback.set_volume(db, volume, session_id=player_session)
    playback.broadcast_playback_state()
    return result

@router.post("/queue")
def set_queue(track_ids: List[int], start_index: int = 0, session: str = Query(None), db: Session = Depends(get_db)):
    """Set queue on server, broadcast to all sessions"""
    result = playback.set_queue(db, track_ids, start_index, session_id=session)
    playback.broadcast_playback_state()
    return result

@router.post("/queue/play-next")
def play_next(track_id: int, session: str = Query(None), db: Session = Depends(get_db)):
    return playback.play_next(db, track_id)

@router.post("/queue/add")
def add_to_queue(track_id: int, session: str = Query(None), db: Session = Depends(get_db)):
    return playback.add_to_queue(db, track_id)

@router.post("/queue/remove")
def remove_from_queue(index: int, session: str = Query(None), db: Session = Depends(get_db)):
    return playback.remove_from_queue(index)

@router.post("/shuffle")
def toggle_shuffle(session: str = Query(None), db: Session = Depends(get_db)):
    return playback.toggle_shuffle(db, session_id=session)

@router.post("/repeat")
def toggle_repeat(session: str = Query(None), db: Session = Depends(get_db)):
    return playback.toggle_repeat(db, session_id=session)

@router.post("/shuffle-play")
def shuffle_play(count: int = 50, session: str = Query(None), db: Session = Depends(get_db)):
    return playback.play_random(db, count, session_id=session)

@router.get("/stream/{track_id}")
def stream_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    if not os.path.exists(track.path):
        raise HTTPException(status_code=404, detail="File not found")
    
    fmt = track.file_format.upper() if track.file_format else ""
    
    # Transcode M4A/M4B to MP3 using FFmpeg (browser compatible)
    if fmt in ('M4A', 'M4B'):
        temp_path = os.path.join(TRANSCODE_DIR, f"track_{track_id}.mp3")
        
        if not os.path.exists(temp_path):
            cmd = [
                'ffmpeg', '-i', track.path, '-y',
                '-f', 'mp3', '-codec:a', 'libmp3lame',
                '-b:a', '320k', '-nostdin',
                temp_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"FFmpeg transcoding failed: {result.stderr}")
                raise HTTPException(status_code=500, detail="Transcoding failed")
        
        return FileResponse(
            temp_path,
            media_type="audio/mpeg",
            headers={"Accept-Ranges": "bytes"}
        )
    
    # Determine correct MIME type based on format for other formats
    if fmt == "FLAC":
        media_type = "audio/flac"
    elif fmt in ("OGG", "OPUS"):
        media_type = "audio/ogg"
    elif fmt == "WAV":
        media_type = "audio/wav"
    else:
        media_type = "audio/mpeg"
    
    return FileResponse(
        track.path,
        media_type=media_type,
        headers={"Accept-Ranges": "bytes"}
    )