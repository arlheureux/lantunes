import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import WebSocket, WebSocketDisconnect
from playback import playback
import json

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    playback.add_connection(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            event = msg.get("event")
            payload = msg.get("data", {})
            
            from database import SessionLocal
            db = SessionLocal()
            
            if event == "control":
                action = payload.get("action")
                position = payload.get("position")
                
                if action == "play":
                    playback.play(db)
                elif action == "pause":
                    playback.pause(db)
                elif action == "stop":
                    playback.stop(db)
                elif action == "next":
                    playback.next(db)
                elif action == "previous":
                    playback.previous(db)
                elif action == "seek" and position is not None:
                    playback.seek(db, position)
            
            elif event == "set_volume":
                volume = payload.get("volume", 1.0)
                playback.set_volume(db, volume)
            
            elif event == "set_queue":
                track_ids = payload.get("track_ids", [])
                start_index = payload.get("start_index", 0)
                playback.set_queue(db, track_ids, start_index)
            
            db.close()
            
    except WebSocketDisconnect:
        pass
    finally:
        playback.remove_connection(websocket)