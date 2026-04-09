import sys
import os
import uuid
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import WebSocket, WebSocketDisconnect
from playback import playback
from auth import verify_token
import json

async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    print(f"[WS] Token from query: {token[:20] if token else None}...")
    
    auth_payload = None
    if token:
        auth_payload = verify_token(token)
        print(f"[WS] Auth payload: {auth_payload}")
    
    if not auth_payload:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    await websocket.accept()
    playback.add_connection(websocket)
    
    # Generate unique session ID for this connection
    session_id = str(uuid.uuid4())
    print(f"[WS] New session: {session_id}")
    
    # Store user info from token
    user_id = auth_payload.get("user_id")
    username = auth_payload.get("username")
    
    # Initialize device_id as None until registered
    device_id = None
    device_owner = None  # user_id that owns this device
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            event = msg.get("event")
            payload = msg.get("data", {})
            
            from database import SessionLocal
            db = SessionLocal()
            try:
                if event == "register":
                    # Client registers with device info
                    device_id = payload.get("device_id")
                    device_name = payload.get("device_name", "Unknown Device")
                    device_owner = user_id  # This device belongs to the authenticated user
                    print(f"[WS] Register: session_id={session_id}, device_id={device_id}, name={device_name}, user={username}")
                    if device_id:
                        playback.register_device(websocket, session_id, device_id, device_name, device_owner)
                        print(f"[WS] Sessions after register: {list(playback._sessions.keys())}")
                        playback.broadcast_sessions()
                
                elif event == "set_player":
                    # Set which device should play audio (by session_id)
                    target_session_id = payload.get("session_id")
                    print(f"[WS] set_player called with session: {target_session_id}")
                    if target_session_id and playback.set_player_session(target_session_id):
                        print(f"[WS] Player set to session: {target_session_id}")
                        playback.broadcast_sessions()
                
                elif event == "update_device_name":
                    # Update device name
                    target_device_id = payload.get("device_id")
                    device_name = payload.get("device_name")
                    if target_device_id and device_name:
                        playback.update_device_name(target_device_id, device_name)
                        playback.broadcast_sessions()
                
                elif event == "control":
                    # Remote control - control the player session
                    action = payload.get("action")
                    position = payload.get("position")
                    player_session = playback.get_player_session()
                    
                    # Any session can send control commands - server routes to player
                    if action == "play":
                        playback.play(db, session_id=session_id)
                    elif action == "pause":
                        playback.pause(db, session_id=session_id)
                    elif action == "stop":
                        playback.stop(db, session_id=session_id)
                    elif action == "next":
                        playback.next(db, session_id=session_id)
                    elif action == "previous":
                        playback.previous(db, session_id=session_id)
                    elif action == "seek" and position is not None:
                        playback.seek(db, position, session_id=session_id)
                
                elif event == "set_volume":
                    volume = payload.get("volume", 1.0)
                    playback.set_volume(db, volume, session_id=session_id)
                
                elif event == "set_queue":
                    track_ids = payload.get("track_ids", [])
                    start_index = payload.get("start_index", 0)
                    playback.set_queue(db, track_ids, start_index, session_id=session_id)
            finally:
                db.close()
            
    except WebSocketDisconnect:
        pass
    finally:
        playback.remove_connection(websocket)