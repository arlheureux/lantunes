from sqlalchemy.orm import Session
from database import get_db, PlaybackState, Track
from datetime import datetime
from typing import List, Optional
import json

class PlaybackController:
    def __init__(self):
        self.queue: List[int] = []
        self.current_index: int = 0
        self._ws_connections: List = []
    
    def add_connection(self, ws):
        self._ws_connections.append(ws)
    
    def remove_connection(self, ws):
        if ws in self._ws_connections:
            self._ws_connections.remove(ws)
    
    def broadcast(self, event: str, data: dict):
        msg = json.dumps({"event": event, "data": data})
        for ws in self._ws_connections[:]:
            try:
                import asyncio
                asyncio.create_task(ws.send_text(msg))
            except:
                self._ws_connections.remove(ws)
    
    def get_state(self, db: Session) -> dict:
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if not state:
            state = PlaybackState(id=1)
            db.add(state)
            db.commit()
        
        track = None
        if state.current_track_id:
            track = db.query(Track).filter(Track.id == state.current_track_id).first()
        
        return {
            "track": {
                "id": track.id,
                "title": track.title,
                "artist": track.artist_id,
                "album": track.album_id,
                "duration": track.duration,
                "path": track.path,
                "file_format": track.file_format,
                "bitrate": track.bitrate,
                "sample_rate": track.sample_rate
            } if track else None,
            "position": state.position,
            "is_playing": state.is_playing,
            "volume": state.volume,
            "queue": self.queue,
            "queue_index": self.current_index
        }
    
    def play(self, db: Session, track_id: int = None, queue: List[int] = None):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if not state:
            state = PlaybackState(id=1)
            db.add(state)
        
        if queue is not None:
            self.queue = queue
            self.current_index = 0
        
        if track_id is not None:
            if track_id not in self.queue:
                self.queue.append(track_id)
            self.current_index = self.queue.index(track_id)
        
        if self.queue:
            state.current_track_id = self.queue[self.current_index]
            state.is_playing = True
            state.position = 0
            state.updated_at = datetime.utcnow()
            db.commit()
            
            track = db.query(Track).filter(Track.id == state.current_track_id).first()
            self.broadcast("playback_state", self.get_state(db))
        
        return self.get_state(db)
    
    def pause(self, db: Session):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.is_playing = False
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db)
    
    def stop(self, db: Session):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.is_playing = False
            state.current_track_id = None
            state.position = 0
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db)
    
    def next(self, db: Session):
        if not self.queue:
            return self.get_state(db)
        
        if self.current_index < len(self.queue) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        state.current_track_id = self.queue[self.current_index]
        state.position = 0
        state.updated_at = datetime.utcnow()
        db.commit()
        
        self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db)
    
    def previous(self, db: Session):
        if not self.queue:
            return self.get_state(db)
        
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.queue) - 1
        
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        state.current_track_id = self.queue[self.current_index]
        state.position = 0
        state.updated_at = datetime.utcnow()
        db.commit()
        
        self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db)
    
    def seek(self, db: Session, position: int):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.position = position
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db)
    
    def set_volume(self, db: Session, volume: float):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.volume = max(0.0, min(1.0, volume))
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db)
    
    def set_queue(self, db: Session, track_ids: List[int], start_index: int = 0):
        self.queue = track_ids
        self.current_index = start_index if start_index < len(track_ids) else 0
        
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state and self.queue:
            state.current_track_id = self.queue[self.current_index]
            state.is_playing = True
            state.position = 0
            state.updated_at = datetime.utcnow()
            db.commit()
        
        self.broadcast("playback_state", self.get_state(db))
        self.broadcast("queue_updated", {"queue": self.queue})
        return self.get_state(db)
    
    def play_next(self, db: Session, track_id: int):
        """Add a track to play next (after current track)"""
        if track_id not in self.queue:
            # Insert right after current position
            insert_pos = self.current_index + 1
            self.queue.insert(insert_pos, track_id)
        else:
            # Already in queue, move to just after current
            self.queue.remove(track_id)
            insert_pos = self.current_index + 1
            self.queue.insert(insert_pos, track_id)
        
        self.broadcast("queue_updated", {"queue": self.queue})
        return {"added": True, "position": self.queue.index(track_id)}
    
    def add_to_queue(self, db: Session, track_id: int):
        """Add a track to the end of the queue"""
        if track_id not in self.queue:
            self.queue.append(track_id)
        
        self.broadcast("queue_updated", {"queue": self.queue})
        return {"added": True}

playback = PlaybackController()