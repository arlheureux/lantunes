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
        self.shuffle_mode: bool = False
        self.last_played_track_id: int = None
        # Device management for "cast play to" feature
        self._devices: dict = {}  # {device_id: {"ws": websocket, "name": str, "is_player": bool}}
        self._player_device_id: str = None  # Which device plays audio
    
    def register_device(self, ws, device_id: str, device_name: str):
        """Register a new device or update existing"""
        self._devices[device_id] = {"ws": ws, "name": device_name, "is_player": False}
        # If first device, make it the player
        if not self._player_device_id:
            self._player_device_id = device_id
            self._devices[device_id]["is_player"] = True
    
    def update_device_name(self, device_id: str, device_name: str):
        """Update device name"""
        if device_id in self._devices:
            self._devices[device_id]["name"] = device_name
    
    def remove_device(self, ws):
        """Remove device on disconnect"""
        device_id_to_remove = None
        for dev_id, dev_info in self._devices.items():
            if dev_info["ws"] == ws:
                device_id_to_remove = dev_id
                break
        
        if device_id_to_remove:
            del self._devices[device_id_to_remove]
            # If removed device was player, assign new player
            if self._player_device_id == device_id_to_remove:
                self._player_device_id = None
                # Assign first available device as player
                if self._devices:
                    self._player_device_id = next(iter(self._devices.keys()))
                    if self._player_device_id:
                        self._devices[self._player_device_id]["is_player"] = True
    
    def set_player_device(self, device_id: str):
        """Set which device should play audio"""
        # Disable current player
        if self._player_device_id and self._player_device_id in self._devices:
            self._devices[self._player_device_id]["is_player"] = False
        
        # Enable new player
        if device_id in self._devices:
            self._player_device_id = device_id
            self._devices[device_id]["is_player"] = True
            return True
        return False
    
    def get_devices(self) -> List[dict]:
        """Get list of connected devices"""
        return [
            {"id": dev_id, "name": dev_info["name"], "is_player": dev_info["is_player"]}
            for dev_id, dev_info in self._devices.items()
        ]
    
    def get_player_device_id(self) -> str:
        """Get the current player device ID"""
        return self._player_device_id
    
    def is_device_player(self, device_id: str) -> bool:
        """Check if device is the player"""
        return device_id == self._player_device_id
    
    def add_connection(self, ws):
        self._ws_connections.append(ws)
    
    def add_connection(self, ws):
        self._ws_connections.append(ws)
    
    def remove_connection(self, ws):
        if ws in self._ws_connections:
            self._ws_connections.remove(ws)
        # Also remove device on disconnect
        self.remove_device(ws)
    
    def broadcast(self, event: str, data: dict, for_player_only: bool = False):
        msg = json.dumps({"event": event, "data": data})
        disconnected = []
        
        # If this is for player only, we need to track which ws is which device
        if for_player_only and hasattr(self, '_device_ws_map'):
            # Only send to player device
            for dev_id, dev_info in self._devices.items():
                if dev_info.get("is_player") and dev_info.get("ws"):
                    ws = dev_info["ws"]
                    try:
                        import asyncio
                        asyncio.create_task(ws.send_text(msg))
                    except Exception:
                        pass
        else:
            # Send to all (for regular broadcasts like pause, next, etc - no stream_url)
            for ws in self._ws_connections:
                try:
                    import asyncio
                    asyncio.create_task(ws.send_text(msg))
                except Exception:
                    disconnected.append(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            if ws in self._ws_connections:
                self._ws_connections.remove(ws)
    
    def broadcast_playback_state(self):
        """Broadcast playback state to all devices, with stream_url only for player"""
        from database import SessionLocal
        import asyncio
        
        db = SessionLocal()
        
        # Pre-compute state for each device
        device_states = {}
        for dev_id, dev_info in self._devices.items():
            is_this_player = dev_info.get("is_player", False)
            device_states[dev_id] = self.get_state(db, is_this_player)
        
        db.close()
        
        # Send to each device
        for dev_id, state in device_states.items():
            try:
                ws = self._devices.get(dev_id, {}).get("ws")
                if ws:
                    msg = json.dumps({"event": "playback_state", "data": state})
                    asyncio.run(ws.send_text(msg))
            except Exception as e:
                print(f"Error sending playback state to {dev_id}: {e}")
    
    def broadcast_devices(self):
        """Broadcast list of connected devices to all clients"""
        import asyncio
        
        devices = self.get_devices()
        print(f"[Broadcast] Broadcasting devices: {devices}")
        msg = json.dumps({"event": "devices", "data": {"devices": devices}})
        
        for ws in self._ws_connections:
            try:
                asyncio.run(ws.send_text(msg))
            except Exception as e:
                print(f"Error broadcasting devices: {e}")
    
    def get_state(self, db: Session, is_player: bool = True) -> dict:
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if not state:
            state = PlaybackState(id=1)
            db.add(state)
            db.commit()
        
        track = None
        if state.current_track_id:
            track = db.query(Track).filter(Track.id == state.current_track_id).first()
        
        result = {
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
            "queue_index": self.current_index,
            "shuffle_mode": self.shuffle_mode,
            "player_device_id": self._player_device_id
        }
        
        # Only include stream URL for the player device
        if is_player and track:
            result["track"]["stream_url"] = f"/api/playback/stream/{track.id}"
        
        return result
    
    def play(self, db: Session, track_id: int = None, queue: List[int] = None, player_device_id: str = None, is_player: bool = True):
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
            
            self.broadcast_playback_state()
        
        return self.get_state(db, is_player)
    
    def pause(self, db: Session, is_player: bool = True):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.is_playing = False
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db, is_player)
    
    def stop(self, db: Session, is_player: bool = True):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.is_playing = False
            state.current_track_id = None
            state.position = 0
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db, is_player)
    
    def next(self, db: Session, is_player: bool = True):
        if not self.queue:
            return self.get_state(db, is_player)
        
        if self.shuffle_mode and len(self.queue) > 1:
            # Pick random track, avoiding the last played one
            available_indices = [i for i in range(len(self.queue)) if i != self.current_index]
            if available_indices:
                import random
                self.current_index = random.choice(available_indices)
        else:
            if self.current_index < len(self.queue) - 1:
                self.current_index += 1
            else:
                self.current_index = 0
        
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        state.current_track_id = self.queue[self.current_index]
        state.position = 0
        state.updated_at = datetime.utcnow()
        db.commit()
        
        self.last_played_track_id = self.queue[self.current_index]
        self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db, is_player)
    
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
    
    def seek(self, db: Session, position: int, is_player: bool = True):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.position = position
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db, is_player)
    
    def set_volume(self, db: Session, volume: float, is_player: bool = True):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.volume = max(0.0, min(1.0, volume))
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast("playback_state", self.get_state(db))
        return self.get_state(db, is_player)
    
    def set_queue(self, db: Session, track_ids: List[int], start_index: int = 0, is_player: bool = True):
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
        return self.get_state(db, is_player)
    
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
    
    def toggle_shuffle(self, db: Session, is_player: bool = True):
        """Toggle shuffle mode on/off"""
        self.shuffle_mode = not self.shuffle_mode
        self.broadcast("playback_state", self.get_state(db))
        return {"shuffle_mode": self.shuffle_mode, "is_player": is_player}
    
    def play_random(self, db: Session, count: int = 50, is_player: bool = True):
        """Fill queue with random tracks from library"""
        import random
        
        all_tracks = db.query(Track).all()
        if not all_tracks:
            return {"error": "No tracks in library"}
        
        # Shuffle and pick 'count' tracks
        track_ids = [t.id for t in all_tracks]
        random.shuffle(track_ids)
        self.queue = track_ids[:count]
        self.current_index = 0
        
        # Start playing
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.current_track_id = self.queue[self.current_index]
            state.is_playing = True
            state.position = 0
            state.updated_at = datetime.utcnow()
            db.commit()
        
        self.last_played_track_id = self.queue[self.current_index]
        self.broadcast("playback_state", self.get_state(db))
        self.broadcast("queue_updated", {"queue": self.queue})
        return self.get_state(db, is_player)

playback = PlaybackController()