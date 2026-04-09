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

router = APIRouter(prefix="/api/playback", tags=["playback"])

class PlayRequest(BaseModel):
    track_id: Optional[int] = Field(default=None)
    queue: Optional[List[int]] = Field(default=None)

@router.get("/state")
def get_state(session: str = Query(None), db: Session = Depends(get_db)):
    # State is the same for all sessions - they all get stream_url
    return playback.get_state(db)

@router.post("/play")
def play(track_id: int = None, queue: str = None, session: str = Query(None), db: Session = Depends(get_db)):
    """Route play command to target session (Jellyfin style)"""
    # Get the player session ID - commands go to the player
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    
    # Route command to player session via WebSocket
    queue_list = [int(x) for x in queue.split(',')] if queue else None
    return playback.route_command(player_session, "play", {
        "track_id": track_id,
        "queue": queue_list
    })

@router.post("/pause")
def pause(session: str = Query(None), db: Session = Depends(get_db)):
    """Route pause command to player session (Jellyfin style)"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    return playback.route_command(player_session, "pause")

@router.post("/stop")
def stop(session: str = Query(None), db: Session = Depends(get_db)):
    """Route stop command to player session (Jellyfin style)"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    return playback.route_command(player_session, "stop")

@router.post("/next")
def next_track(session: str = Query(None), db: Session = Depends(get_db)):
    """Route next command to player session (Jellyfin style)"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    return playback.route_command(player_session, "next")

@router.post("/previous")
def previous_track(session: str = Query(None), db: Session = Depends(get_db)):
    """Route previous command to player session (Jellyfin style)"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    return playback.route_command(player_session, "previous")

@router.post("/seek")
def seek(position: int = Query(...), session: str = Query(None), db: Session = Depends(get_db)):
    """Route seek command to player session (Jellyfin style)"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    return playback.route_command(player_session, "seek", {"position": position})

@router.post("/volume")
def set_volume(volume: float = Query(..., ge=0.0, le=1.0), session: str = Query(None), db: Session = Depends(get_db)):
    """Route volume command to player session (Jellyfin style)"""
    player_session = playback.get_player_session()
    if not player_session:
        return {"error": "No active player session"}
    return playback.route_command(player_session, "set_volume", {"volume": volume})

@router.post("/queue")
def set_queue(track_ids: List[int], start_index: int = 0, player: str = Query(None), db: Session = Depends(get_db)):
    is_player = player == playback.get_player_device_id()
    return playback.set_queue(db, track_ids, start_index, session_id=session)

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