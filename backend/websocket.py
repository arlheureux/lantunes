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
    
    # Initialize device_id as None until registered
    device_id = None
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            event = msg.get("event")
            payload = msg.get("data", {})
            
            from database import SessionLocal
            db = SessionLocal()
            
            if event == "register":
                # Client registers with device info
                device_id = payload.get("device_id")
                device_name = payload.get("device_name", "Unknown Device")
                if device_id:
                    playback.register_device(websocket, device_id, device_name)
                    playback.broadcast_devices()
            
            elif event == "set_player":
                # Set which device should play audio
                target_device_id = payload.get("device_id")
                if target_device_id and playback.set_player_device(target_device_id):
                    playback.broadcast_devices()
            
            elif event == "update_device_name":
                # Update device name
                device_id = payload.get("device_id")
                device_name = payload.get("device_name")
                if device_id and device_name:
                    playback.update_device_name(device_id, device_name)
                    playback.broadcast_devices()
            
            elif event == "control":
                action = payload.get("action")
                position = payload.get("position")
                player = playback.get_player_device_id()
                
                if action == "play":
                    is_player = device_id == player
                    playback.play(db, player_device_id=device_id, is_player=is_player)
                elif action == "pause":
                    is_player = device_id == player
                    playback.pause(db, is_player)
                elif action == "stop":
                    is_player = device_id == player
                    playback.stop(db, is_player)
                elif action == "next":
                    is_player = device_id == player
                    playback.next(db, is_player)
                elif action == "previous":
                    is_player = device_id == player
                    playback.previous(db, is_player)
                elif action == "seek" and position is not None:
                    is_player = device_id == player
                    playback.seek(db, position, is_player)
            
            elif event == "set_volume":
                volume = payload.get("volume", 1.0)
                player = playback.get_player_device_id()
                is_player = device_id == player
                playback.set_volume(db, volume, is_player)
            
            elif event == "set_queue":
                track_ids = payload.get("track_ids", [])
                start_index = payload.get("start_index", 0)
                player = playback.get_player_device_id()
                is_player = device_id == player
                playback.set_queue(db, track_ids, start_index, is_player)
            
            db.close()
            
    except WebSocketDisconnect:
        pass
    finally:
        playback.remove_connection(websocket)