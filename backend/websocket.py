import sys
import os
import uuid
import asyncio
import logging
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from fastapi import WebSocket, WebSocketDisconnect
from playback import playback
from auth import verify_token
import json

logger = logging.getLogger("lantunes.websocket")

async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    logger.info(f" Token from query: {token[:20] if token else None}...")
    
    auth_payload = None
    if token:
        auth_payload = verify_token(token)
        logger.info(f" Auth payload: {auth_payload}")
    
    if not auth_payload:
        await websocket.close(code=4001, reason="Authentication required")
        return
    
    await websocket.accept()
    playback.add_connection(websocket)
    
    # Get session_id from frontend's register message, or generate if not provided
    session_id = None
    
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
                    # Client registers with device info - use the session_id they provide
                    session_id = payload.get("session_id")  # Get from frontend, not generated
                    device_id = payload.get("device_id")
                    device_name = payload.get("device_name", "Unknown Device")
                    device_owner = user_id  # This device belongs to the authenticated user
                    
                    # If no session_id provided, generate one
                    if not session_id:
                        session_id = str(uuid.uuid4())
                    
                    logger.info(f" Register: session_id={session_id}, device_id={device_id}, name={device_name}, user={username}")
                    if device_id:
                        # Check if session already exists (reconnection)
                        existing_session = playback._sessions.get(session_id)
                        logger.info(f" Existing session check: {existing_session}")
                        if existing_session and not existing_session.get("ws") and not existing_session.get("connected"):
                            # Reconnect existing session
                            playback.reconnect_session(websocket, session_id)
                            logger.info(f" Reconnected session: {session_id}")
                            # Send current playback state to reconnecting session
                            from database import SessionLocal as DB
                            db2 = DB()
                            state = playback.get_state(db2)
                            db2.close()
                            state_msg = json.dumps({"event": "playback_state", "data": state})
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(websocket.send_text(state_msg))
                                loop.close()
                                logger.info(f" Sent playback state on reconnect to session: {session_id}")
                            except Exception as e:
                                logger.info(f" Error sending state on reconnect: {e}")
                        else:
                            # New registration
                            playback.register_device(websocket, session_id, device_id, device_name, device_owner)
                            logger.info(f" New session registered: {session_id}")
                        
                        # Always send current playback state to newly registered/reconnecting device
                        db2 = SessionLocal()
                        state = playback.get_state(db2)
                        db2.close()
                        state_msg = json.dumps({"event": "playback_state", "data": state})
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(websocket.send_text(state_msg))
                            loop.close()
                            logger.info(f" Sent playback state to device: {session_id}")
                        except Exception as e:
                            logger.info(f" Error sending state: {e}")
                        
                        logger.info(f" Sessions after register: {list(playback._sessions.keys())}")
                        playback.broadcast_sessions()
                
                elif event == "set_player":
                    # Set which device should play audio (by session_id)
                    target_session_id = payload.get("session_id")
                    logger.info(f" set_player called with session: {target_session_id}")
                    if target_session_id and playback.set_player_session(target_session_id):
                        logger.info(f" Player set to session: {target_session_id}")
                        playback.broadcast_sessions()
                
                elif event == "update_device_name":
                    # Update device name
                    target_device_id = payload.get("device_id")
                    device_name = payload.get("device_name")
                    if target_device_id and device_name:
                        playback.update_device_name(target_device_id, device_name)
                        playback.broadcast_sessions()
                
                elif event == "control":
                    try:
                        # Remote control - execute on server side
                        action = payload.get("action")
                        position = payload.get("position")
                        logger.info(f"Control: action={action}, position={position}")
                        
                        # Execute action directly on server
                        if action == 'play':
                            logger.info(f"Executing play with position={position}")
                            playback.play(db, position=position)
                        elif action == 'pause':
                            logger.info(f"Executing pause with position={position}")
                            playback.pause(db, position=position if position else None)
                        elif action == 'stop':
                            playback.stop(db)
                        elif action == 'next':
                            playback.next(db)
                        elif action == 'previous':
                            playback.previous(db)
                        elif action == 'seek' and position is not None:
                            playback.seek(db, position)
                        elif action == 'toggle_shuffle':
                            playback.toggle_shuffle(db)
                        elif action == 'toggle_repeat':
                            playback.toggle_repeat(db)
                        elif action == 'shuffle_play':
                            count = payload.get('count', 50)
                            playback.play_random(db, count)
                        elif action == 'play_next':
                            track_id = payload.get('track_id')
                            if track_id:
                                playback.play_next(db, track_id)
                        elif action == 'add_to_queue':
                            track_id = payload.get('track_id')
                            if track_id:
                                playback.add_to_queue(db, track_id)
                        elif action == 'remove_from_queue':
                            index = payload.get('index')
                            logger.info(f"remove_from_queue: index={index}")
                            if index is not None:
                                playback.remove_from_queue(index)
                        elif action == 'play_queue':
                            track_ids = payload.get('track_ids', [])
                            start_index = payload.get('start_index', 0)
                            logger.info(f"play_queue: track_ids={track_ids}, start_index={start_index}")
                            playback.set_queue(db, track_ids, start_index, session_id=session_id)
                            playback.play(db)
                        elif action == 'update_position':
                            position = payload.get('position')
                            if position is not None:
                                playback.update_position(db, position)
                        elif action == 'clear_queue':
                            playback.set_queue(db, [], 0, session_id=session_id)
                        
                        # Broadcast state to all clients immediately after command
                        playback.broadcast_playback_state()
                    except Exception as e:
                        logger.error(f"Error in control handler: {e}")
                
                elif event == 'set_volume':
                    volume = payload.get('volume', 1.0)
                    playback.set_volume(db, volume, session_id=session_id)
                    playback.broadcast_playback_state()
                
                elif event == 'set_queue':
                    track_ids = payload.get('track_ids', [])
                    start_index = payload.get('start_index', 0)
                    playback.set_queue(db, track_ids, start_index, session_id=session_id)
                    playback.broadcast_playback_state()
                
                elif event == 'play_queue':
                    try:
                        track_ids = payload.get('track_ids', [])
                        start_index = payload.get('start_index', 0)
                        logger.info(f"play_queue: track_ids={track_ids}, start_index={start_index}")
                        if playback.shuffle_mode:
                            playback.toggle_shuffle(db)
                        playback.set_queue(db, track_ids, start_index, session_id=session_id)
                        logger.info("Calling playback.play(db)")
                        playback.play(db)
                        playback.broadcast_playback_state()
                    except Exception as e:
                        logger.error(f"Error in play_queue handler: {e}")
            finally:
                db.close()
            
    except WebSocketDisconnect:
        pass
    finally:
        playback.remove_connection(websocket)