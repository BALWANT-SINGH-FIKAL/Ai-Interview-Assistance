# backend/api/ws_endpoint.py (FINAL CORRECTED VERSION)
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
import json

# FIX 1 & 6: Import the global instance of the manager using the explicit path
# NOTE: Replace 'backend.app.core' with the correct path if your previous fix used different relative imports.
from app.core.interview_manager import interview_manager 

router = APIRouter()
session_manager = interview_manager # Use the global singleton instance

@router.websocket("/session")
async def interview_ws(websocket: WebSocket):
    session_id = None
    try:
        await websocket.accept()
        
        # FIX 3: Create a session and link the WebSocket object
        session_id = session_manager.create_session(websocket) 
        print(f"WebSocket connected, Session ID: {session_id}")

        # Send initial confirmation back to the client
        await websocket.send_json({"event": "connected", "session_id": session_id, "message": "Connection established. Ready to start interview."})
        
        while True:
            # FIX 4: Use receive() to handle both text (JSON) and bytes (Audio Blob)
            message = await websocket.receive()
            
            if "text" in message:
                # 1. Handle JSON Control Messages (start_interview, end_interview, etc.)
                text_data = message["text"]
                print(f"Received TEXT data: {text_data[:50]}...")
                
                # FIX 7: Manager handles JSON decoding and routing (includes await)
                response_to_send = await session_manager.handle_user_message(session_id, text_data)
                
                # The manager sends 'ai_question' responses internally (TTS). 
                # We only send messages back if the manager explicitly returns one.
                if response_to_send: 
                    await websocket.send_json(response_to_send)

            elif "bytes" in message:
                # 2. Handle Binary Audio Blobs (Phase 4 STT)
                audio_chunk = message["bytes"]
                print(f"Received BINARY audio blob of size: {len(audio_chunk)} bytes")
                
                # Manager handles transcription and response (includes await)
                await session_manager.process_audio_chunk(session_id, audio_chunk)

            else:
                print("Received message of unknown type.")
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for Session ID: {session_id}")
    except Exception as e:
        print(f"An error occurred in interview_ws: {e}")
        # Send an error code before closing
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"Server error: {e}")
    finally:
        # Clean up the session
        if session_id:
            session_manager.end_session(session_id)