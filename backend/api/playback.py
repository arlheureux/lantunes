import sys
import os
import logging
import atexit
import glob
import subprocess
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, Track
from playback import playback
from auth import verify_token

router = APIRouter(prefix='/api/playback', tags=['playback'])

TRANSCODE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', 'transcode')
os.makedirs(TRANSCODE_DIR, exist_ok=True)


def cleanup_old_transcodes():
    import time
    now = time.time()
    for f in glob.glob(os.path.join(TRANSCODE_DIR, '*.mp3')):
        if os.path.getmtime(f) < now - 3600:
            try:
                os.remove(f)
            except OSError:
                pass


atexit.register(cleanup_old_transcodes)


@router.get('/state')
def get_state(session: str = Query(None), db: Session = Depends(get_db)):
    return playback.get_state(db)


@router.get('/stream/{track_id}')
def stream_track(track_id: int, token: str = Query(None), db: Session = Depends(get_db)):
    # Token can be passed as query param for direct stream URLs
    # If not provided, middleware will require Bearer token in header
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail='Track not found')
    if not os.path.exists(track.path):
        raise HTTPException(status_code=404, detail='File not found')
    
    fmt = track.file_format.upper() if track.file_format else ''
    
    if fmt in ('M4A', 'M4B'):
        temp_path = os.path.join(TRANSCODE_DIR, f'track_{track_id}.mp3')
        
        if not os.path.exists(temp_path):
            cmd = [
                'ffmpeg', '-i', track.path, '-y',
                '-f', 'mp3', '-codec:a', 'libmp3lame',
                '-b:a', '320k', '-nostdin',
                temp_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f'FFmpeg transcoding failed: {result.stderr}')
                raise HTTPException(status_code=500, detail='Transcoding failed')
        
        return FileResponse(
            temp_path,
            media_type='audio/mpeg',
            headers={'Accept-Ranges': 'bytes'}
        )
    
    if fmt == 'FLAC':
        media_type = 'audio/flac'
    elif fmt in ('OGG', 'OPUS'):
        media_type = 'audio/ogg'
    elif fmt == 'WAV':
        media_type = 'audio/wav'
    else:
        media_type = 'audio/mpeg'
    
    return FileResponse(
        track.path,
        media_type=media_type,
        headers={'Accept-Ranges': 'bytes'}
    )