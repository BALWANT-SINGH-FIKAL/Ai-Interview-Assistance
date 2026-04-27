# backend/api/ws_endpoint.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
import json

# Correctly import the global manager instance from the core module
# NOTE: Using 'app.core' because you run the server from the parent directory ('backend').
from app.core.interview_manager import interview_manager 

router = APIRouter()
session_manager = interview_manager # Use the global singleton instance

# FIX: Changed endpoint path to /session to avoid 403 conflicts (as resolved earlier)
@router.websocket("/session")
async def interview_ws(websocket: WebSocket):
    session_id = None
    try:
        await websocket.accept()
        
        # FIX: Create session and link the WebSocket object
        session_id = session_manager.create_session(websocket) 
        print(f"WebSocket connected, Session ID: {session_id}")

        # Send initial confirmation back to the client
        await websocket.send_json({"event": "connected", "session_id": session_id, "message": "Connection established. Ready to start interview."})
        
        while True:
            # FIX: Use receive() to handle BOTH text (JSON) and bytes (Audio Blob)
            message = await websocket.receive()
            
            if "text" in message:
                # 1. Handle JSON Control Messages (start_interview, end_interview, replay_question)
                text_data = message["text"]
                print(f"Received TEXT data: {text_data[:50]}...")
                
                # Manager handles decoding, routing, and sending responses internally
                response_to_send = await session_manager.handle_user_message(session_id, text_data)
                
                # Only send a response if the manager explicitly returned one
                if response_to_send: 
                    await websocket.send_json(response_to_send)

            elif "bytes" in message:
                # 2. Handle Binary Audio Blobs (STT Input)
                audio_chunk = message["bytes"]
                print(f"Received BINARY audio blob of size: {len(audio_chunk)} bytes")
                
                # Manager handles saving, transcription, and follow-up
                await session_manager.process_audio_chunk(session_id, audio_chunk)

            else:
                print("Received message of unknown type.")
                
    except WebSocketDisconnect:
        # Standard graceful closure handled by Starlette
        print(f"WebSocket disconnected for Session ID: {session_id}")
    except Exception as e:
        # FIX: Send error message first, then allow the framework to handle closure.
        # This prevents the double-close error (RuntimeError).
        print(f"An error occurred in interview_ws: {e}")
        try:
            await websocket.send_json({"event": "error", "message": f"Server error: {e}"})
        except Exception:
            pass # Ignore errors during cleanup
        
    finally:
        # Clean up the session regardless of disconnect type
        if session_id:
            session_manager.end_session(session_id)