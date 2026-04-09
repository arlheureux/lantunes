from sqlalchemy.orm import Session
from database import get_db, PlaybackState, Track, Artist, Album
from datetime import datetime
from typing import List, Optional
import json
import uuid

class PlaybackController:
    def __init__(self):
        self.queue: List[int] = []
        self.current_index: int = 0
        self._ws_connections: List = []
        self.shuffle_mode: bool = False
        self.repeat_mode: str = "off"  # off, all, one
        self.last_played_track_id: int = None
        
        # Session-based device management (Jellyfin-style)
        # Sessions map: session_id -> {ws, device_id, device_name, is_player, owner}
        self._sessions: dict = {}
        self._player_session_id: str = None  # Which session's device plays audio
    
    def register_device(self, ws, session_id: str, device_id: str, device_name: str, device_owner: str = None):
        """Register a new session with device info"""
        # Store both session_id and device_id mapping
        self._sessions[session_id] = {
            "ws": ws,
            "session_id": session_id,
            "device_id": device_id,
            "name": device_name,
            "is_player": False,
            "owner": device_owner,
            "connected": True
        }
        # If first session, make it the player
        if not self._player_session_id:
            self._player_session_id = session_id
            self._sessions[session_id]["is_player"] = True
    
    def update_device_name(self, device_id: str, device_name: str):
        """Update device name"""
        for session in self._sessions.values():
            if session["device_id"] == device_id:
                session["name"] = device_name
    
    def set_player_session(self, session_id: str):
        """Set which session's device should play audio"""
        from database import SessionLocal
        db = SessionLocal()
        
        # Pause current player before switching
        if self._player_session_id and self._player_session_id in self._sessions:
            self._sessions[self._player_session_id]["is_player"] = False
            state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
            if state:
                state.is_playing = False
                db.commit()
        
        # Enable new player session
        if session_id in self._sessions:
            self._player_session_id = session_id
            self._sessions[session_id]["is_player"] = True
            db.close()
            self.broadcast_playback_state()
            return True
        db.close()
        return False
    
    def get_player_session(self) -> str:
        """Get the current player session ID"""
        return self._player_session_id
    
    def get_sessions(self) -> List[dict]:
        """Get list of all connected sessions with their device info"""
        return [
            {
                "id": session_id,
                "session_id": session_id,
                "device_id": session["device_id"],
                "name": session["name"],
                "is_player": session["is_player"]
            }
            for session_id, session in self._sessions.items()
        ]
    
    def get_player_device_id(self) -> str:
        """Get the device ID of the player session (for backward compatibility)"""
        if self._player_session_id and self._player_session_id in self._sessions:
            return self._sessions[self._player_session_id]["device_id"]
        return None
    
    def is_device_player(self, device_id: str) -> bool:
        """Check if device is the player (for backward compatibility)"""
        return self.get_player_device_id() == device_id
    
    def add_connection(self, ws):
        """Add WebSocket connection"""
        if ws not in self._ws_connections:
            self._ws_connections.append(ws)
    
    def remove_connection(self, ws):
        """Remove WebSocket connection and associated session"""
        if ws in self._ws_connections:
            self._ws_connections.remove(ws)
        # Also clean up session
        session_to_remove = None
        for session_id, session_info in self._sessions.items():
            if session_info["ws"] == ws:
                session_to_remove = session_id
                break
        if session_to_remove:
            del self._sessions[session_to_remove]
            if self._player_session_id == session_to_remove:
                self._player_session_id = None
                if self._sessions:
                    self._player_session_id = next(iter(self._sessions.keys()))
                    if self._player_session_id:
                        self._sessions[self._player_session_id]["is_player"] = True
    
    def broadcast_sessions(self):
        """Broadcast session list to all connected clients"""
        import asyncio
        import concurrent.futures
        
        sessions_data = {"sessions": self.get_sessions()}
        msg = json.dumps({"event": "sessions", "data": sessions_data})
        
        def send_msg(ws):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(ws.send_text(msg))
                loop.close()
            except Exception as e:
                print(f"Error sending sessions: {e}")
                return ws
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for session in self._sessions.values():
                if session.get("ws"):
                    executor.submit(send_msg, session["ws"])
        
        # Also send to any other connections
        for ws in self._ws_connections:
            if ws and ws not in [s.get("ws") for s in self._sessions.values()]:
                executor.submit(send_msg, ws)
    
    def get_player_device_id(self) -> str:
        """Get the current player device ID (from player session)"""
        if self._player_session_id and self._player_session_id in self._sessions:
            return self._sessions[self._player_session_id].get("device_id")
        return None
    
    def is_device_player(self, device_id: str) -> bool:
        """Check if device is the player"""
        return device_id == self.get_player_device_id()
    
    def add_connection(self, ws):
        self._ws_connections.append(ws)
    
    def remove_connection(self, ws):
        """Remove WebSocket connection but keep session for reconnection"""
        if ws in self._ws_connections:
            self._ws_connections.remove(ws)
        
        # Mark session as disconnected but keep it for reconnection
        for session_id, session_info in self._sessions.items():
            if session_info.get("ws") == ws:
                session_info["ws"] = None
                session_info["connected"] = False
                print(f"[Playback] Session {session_id} disconnected but kept for reconnection")
                break
        
        # If player session disconnected, reassign player to another connected session
        if self._player_session_id:
            player_session = self._sessions.get(self._player_session_id)
            if not player_session or not player_session.get("connected"):
                # Player disconnected - find another connected session
                for sid, sess in self._sessions.items():
                    if sess.get("connected"):
                        self._player_session_id = sid
                        sess["is_player"] = True
                        print(f"[Playback] Reassigned player to session: {sid}")
                        break
                else:
                    # No connected sessions - player becomes None
                    self._player_session_id = None
    
    def reconnect_session(self, ws, session_id: str):
        """Reconnect a session that was previously disconnected"""
        if session_id in self._sessions:
            self._sessions[session_id]["ws"] = ws
            self._sessions[session_id]["connected"] = True
            print(f"[Playback] Session {session_id} reconnected")
            # If no player session, make this one the player
            if not self._player_session_id:
                self._player_session_id = session_id
                self._sessions[session_id]["is_player"] = True
            return True
        return False
    
    def broadcast(self, event: str, data: dict):
        """Broadcast message to all sessions"""
        msg = json.dumps({"event": event, "data": data})
        disconnected = []
        
        import concurrent.futures
        import asyncio
        
        def send_msg(ws):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(ws.send_text(msg))
                loop.close()
            except Exception as e:
                print(f"Error sending broadcast: {e}")
                return ws
            return None
        
        # Send to all sessions via their WebSocket
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for session in self._sessions.values():
                ws = session.get("ws")
                if ws:
                    result = executor.submit(send_msg, ws)
                    if result.result():
                        disconnected.append(ws)
        
        # Clean up disconnected
        for ws in disconnected:
            if ws in self._ws_connections:
                self._ws_connections.remove(ws)
    
    def broadcast_playback_state(self):
        """Broadcast playback state to all sessions - ALL sessions get stream_url"""
        from database import SessionLocal
        import asyncio
        import concurrent.futures
        
        db = SessionLocal()
        
        # Get current playback state
        state = self.get_state(db)
        
        db.close()
        
        # Broadcast same state to ALL sessions - they all get stream_url
        msg = json.dumps({"event": "playback_state", "data": state})
        
        def send_msg(ws):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(ws.send_text(msg))
                loop.close()
            except Exception as e:
                print(f"Error sending: {e}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for session in self._sessions.values():
                if session.get("ws"):
                    executor.submit(send_msg, session["ws"])
    
    def get_state(self, db: Session) -> dict:
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if not state:
            state = PlaybackState(id=1)
            db.add(state)
            db.commit()
        
        # Load queue from DB if not in memory (for persistence across restarts)
        if not self.queue:
            try:
                if state.queue:
                    self.queue = [int(x) for x in state.queue.split(',') if x]
            except:
                self.queue = []
        
        # Sync shuffle mode from DB (handle if column doesn't exist yet)
        try:
            self.shuffle_mode = getattr(state, 'shuffle_mode', False) if state else False
        except:
            self.shuffle_mode = False
        
        track = None
        if state.current_track_id:
            track = db.query(Track).filter(Track.id == state.current_track_id).first()
        
        # Handle case where track might not exist
        if not track:
            return {
                "track": None,
                "position": 0,
                "is_playing": False,
                "volume": 1.0,
                "queue": [],
                "queue_index": 0,
                "shuffle_mode": self.shuffle_mode,
                "repeat_mode": self.repeat_mode,
                "player_device_id": self.get_player_device_id()
            }
        
        # Get artist and album names
        artist_name = track.artist_id
        album_title = track.album_id
        if track.artist_id:
            artist = db.query(Artist).filter(Artist.id == track.artist_id).first()
            if artist:
                artist_name = artist.name
        if track.album_id:
            album = db.query(Album).filter(Album.id == track.album_id).first()
            if album:
                album_title = album.title
        
        result = {
            "track": {
                "id": track.id,
                "title": track.title,
                "artist": artist_name,
                "artist_id": track.artist_id,
                "album": album_title,
                "album_id": track.album_id,
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
            "repeat_mode": self.repeat_mode,
            "player_session_id": self._player_session_id,
            "player_device_id": self.get_player_device_id()
        }
        
        # ALL sessions get stream_url - they decide locally whether to play
        if track:
            result["track"]["stream_url"] = f"/api/playback/stream/{track.id}"
        
        return result
    
    def play(self, db: Session, position: int = None, track_id: int = None, queue: List[int] = None, session_id: str = None):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if not state:
            state = PlaybackState(id=1)
            db.add(state)
        
        current_track_id = state.current_track_id
        new_track = False
        resume_play = False
        
        if queue is not None:
            self.queue = queue
            self.current_index = 0
            state.queue = ','.join(map(str, self.queue))
            new_track = True
        
        if track_id is not None:
            if track_id == current_track_id and current_track_id:
                resume_play = True
            elif track_id not in self.queue:
                self.queue.append(track_id)
                self.current_index = self.queue.index(track_id)
                new_track = True
            else:
                self.current_index = self.queue.index(track_id)
                new_track = True
        
        # Resume case: no new track, just resume current
        if track_id is None and queue is None and current_track_id:
            resume_play = True
        
        if self.queue:
            state.current_track_id = self.queue[self.current_index]
            state.is_playing = True
            if new_track and not resume_play:
                state.position = 0
            elif position is not None:
                state.position = position
            # else: keep existing position (from pause)
            if not state.queue:
                state.queue = ','.join(map(str, self.queue))
            state.updated_at = datetime.utcnow()
            db.commit()
            
            self.broadcast_playback_state()
        
        return self.get_state(db)
    
    def pause(self, db: Session, position: int = None, session_id: str = None):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.is_playing = False
            if position is not None:
                state.position = position
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast_playback_state()
        return self.get_state(db)
    
    def stop(self, db: Session, session_id: str = None):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.is_playing = False
            state.current_track_id = None
            state.position = 0
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast_playback_state()
        return self.get_state(db)
    
    def next(self, db: Session, session_id: str = None):
        if not self.queue:
            return self.get_state(db)
        
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
        state.queue = ','.join(map(str, self.queue)) if self.queue else None
        state.updated_at = datetime.utcnow()
        db.commit()
        
        self.last_played_track_id = self.queue[self.current_index]
        self.broadcast_playback_state()
        return self.get_state(db)
    
    def previous(self, db: Session, session_id: str = None):
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
        
        self.last_played_track_id = self.queue[self.current_index]
        self.broadcast_playback_state()
        return self.get_state(db)
    
    def seek(self, db: Session, position: int, session_id: str = None):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.position = position
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast_playback_state()
        return self.get_state(db)
    
    def set_volume(self, db: Session, volume: float, session_id: str = None):
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.volume = max(0.0, min(1.0, volume))
            state.updated_at = datetime.utcnow()
            db.commit()
            self.broadcast_playback_state()
        return self.get_state(db)
    
    def set_queue(self, db: Session, track_ids: List[int], start_index: int = 0, session_id: str = None):
        self.queue = track_ids
        self.current_index = start_index if start_index < len(track_ids) else 0
        
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state and self.queue:
            state.current_track_id = self.queue[self.current_index]
            state.is_playing = True
            state.position = 0
            state.queue = ','.join(map(str, self.queue)) if self.queue else None
            state.shuffle_mode = self.shuffle_mode
            state.updated_at = datetime.utcnow()
            db.commit()
        
        self.broadcast_playback_state()
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
    
    def remove_from_queue(self, index: int):
        """Remove a track from the queue by index"""
        if 0 <= index < len(self.queue):
            self.queue.pop(index)
            self.broadcast("queue_updated", {"queue": self.queue})
            return {"removed": True}
        return {"removed": False}
    
    def toggle_shuffle(self, db: Session, session_id: str = None):
        """Toggle shuffle mode on/off"""
        self.shuffle_mode = not self.shuffle_mode
        # Persist shuffle mode
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.shuffle_mode = self.shuffle_mode
            if self.queue:
                state.queue = ','.join(map(str, self.queue))
            db.commit()
        self.broadcast_playback_state()
        return {"shuffle_mode": self.shuffle_mode}
    
    def toggle_repeat(self, db: Session, session_id: str = None):
        """Toggle repeat mode: off -> all -> one -> off"""
        if self.repeat_mode == "off":
            self.repeat_mode = "all"
        elif self.repeat_mode == "all":
            self.repeat_mode = "one"
        else:
            self.repeat_mode = "off"
        
        state = db.query(PlaybackState).filter(PlaybackState.id == 1).first()
        if state:
            state.repeat_mode = self.repeat_mode
            db.commit()
        
        self.broadcast_playback_state()
        return {"repeat_mode": self.repeat_mode}
    
    def play_random(self, db: Session, count: int = 50, session_id: str = None):
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
        self.broadcast_playback_state()
        self.broadcast("queue_updated", {"queue": self.queue})
        return self.get_state(db)
    
    def route_command(self, target_session_id: str, action: str, data: dict = None):
        """Route command to target session via WebSocket - Jellyfin style"""
        import asyncio
        import concurrent.futures
        
        if target_session_id not in self._sessions:
            return {"error": f"Session {target_session_id} not found", "sessions": list(self._sessions.keys())}
        
        session = self._sessions[target_session_id]
        ws = session.get("ws")
        
        if not ws:
            return {"error": f"Session {target_session_id} has no WebSocket connection"}
        
        # Build command message
        msg_data = {"action": action}
        if data:
            msg_data.update(data)
        
        msg = json.dumps({"event": "command", "data": msg_data})
        
        def send_ws(ws, msg):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(ws.send_text(msg))
                loop.close()
                return True
            except Exception as e:
                print(f"Error sending command to session: {e}")
                return False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            success = executor.submit(send_ws, ws, msg)
        
        if success.result():
            return {"status": "routed", "session": target_session_id, "action": action}
        return {"error": "Failed to send command"}
    
    def broadcast_command_result(self, action: str):
        """Broadcast that a command was executed - all clients update their state"""
        self.broadcast_playback_state()

playback = PlaybackController()