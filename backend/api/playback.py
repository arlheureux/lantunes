import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db, PlaybackState, Track
from playback import playback
from typing import List, Optional
import subprocess

router = APIRouter(prefix="/api/playback", tags=["playback"])

class PlayRequest(BaseModel):
    track_id: Optional[int] = Field(default=None)
    queue: Optional[List[int]] = Field(default=None)

@router.get("/state")
def get_state(db: Session = Depends(get_db)):
    return playback.get_state(db)

@router.post("/play")
def play(req: PlayRequest, db: Session = Depends(get_db)):
    return playback.play(db, req.track_id, req.queue)

@router.post("/pause")
def pause(db: Session = Depends(get_db)):
    return playback.pause(db)

@router.post("/stop")
def stop(db: Session = Depends(get_db)):
    return playback.stop(db)

@router.post("/next")
def next_track(db: Session = Depends(get_db)):
    return playback.next(db)

@router.post("/previous")
def previous_track(db: Session = Depends(get_db)):
    return playback.previous(db)

@router.post("/seek")
def seek(position: int = Query(...), db: Session = Depends(get_db)):
    return playback.seek(db, position)

@router.post("/volume")
def set_volume(volume: float = Query(..., ge=0.0, le=1.0), db: Session = Depends(get_db)):
    return playback.set_volume(db, volume)

@router.post("/queue")
def set_queue(track_ids: List[int], start_index: int = 0, db: Session = Depends(get_db)):
    return playback.set_queue(db, track_ids, start_index)

@router.post("/queue/play-next")
def play_next(track_id: int, db: Session = Depends(get_db)):
    return playback.play_next(db, track_id)

@router.post("/queue/add")
def add_to_queue(track_id: int, db: Session = Depends(get_db)):
    return playback.add_to_queue(db, track_id)

@router.post("/shuffle")
def toggle_shuffle(db: Session = Depends(get_db)):
    return playback.toggle_shuffle(db)

@router.post("/shuffle-play")
def shuffle_play(count: int = 50, db: Session = Depends(get_db)):
    return playback.play_random(db, count)

@router.get("/stream/{track_id}")
def stream_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    if not os.path.exists(track.path):
        raise HTTPException(status_code=404, detail="File not found")
    
    fmt = track.file_format.upper() if track.file_format else ""
    
    # Transcode M4A/M4B to FLAC on-the-fly using FFmpeg
    if fmt in ('M4A', 'M4B'):
        process = subprocess.Popen(
            ['ffmpeg', '-i', track.path, '-f', 'flac', 
             '-codec:a', 'flac', '-compression_level', '0',
             '-nostdin', '-loglevel', 'quiet'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return StreamingResponse(process.stdout, media_type="audio/flac")
    
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