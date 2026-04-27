# backend/app/services/webrtc_manager.py
from fastapi import APIRouter, HTTPException
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaBlackhole
import json
import asyncio
import time
import av 
import traceback # ADDED: For printing full error stack

# FIX: Import the face processor service using the correct path
from app.services.face_processor import face_processor 

router = APIRouter()

# --- Placeholder to store the active PeerConnection (Needed for signaling) ---
pcs = set()

class WebRTCManager:
    """
    Manages the WebRTC PeerConnection for signaling and receiving the media tracks.
    """
    def __init__(self):
        # We initialize the PC inside the route handler now to link it to a session.
        pass

    @staticmethod
    def create_peer_connection():
        """Creates and configures a new RTCPeerConnection."""
        pc = RTCPeerConnection()
        pcs.add(pc) # Track the connection
        
        # ... (icecandidate and connectionstatechange handlers remain the same) ...
        @pc.on("icecandidate")
        def on_icecandidate(candidate):
            if candidate:
                print(f"🧊 ICE candidate found: {candidate.candidate[:20]}...")

        @pc.on("connectionstatechange")
        async def on_state_change():
            print("🔄 WebRTC state:", pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                pcs.discard(pc)
                print("WebRTC connection failed and closed.")

        @pc.on("track")
        async def on_track(track):
            print(f"🎤 Track received: {track.kind}")
            
            if track.kind == "video":
                print("🎥 Video track received. Starting real-time frame processing.")
                
                # Loop to pull frames from the video track
                while True:
                    try:
                        # 1. Read the next video frame
                        frame = await track.recv() 
                        
                        # CRITICAL FIX: Convert the VideoFrame to a NumPy array
                        frame_np = frame.to_ndarray(format="bgr24") 
                        
                        # 2. Pass the NumPy array to the face processor service
                        # NOTE: This call is the suspected source of the crash
                        analysis_result = face_processor.process_frame(frame_np) 
                        
                        # 3. LOGGING: Print the verification status every second (for debugging)
                        if analysis_result.get("face_detected"):
                            if int(time.time() * 10) % 10 == 0: 
                                # This line will only execute if the processor returns the dict keys
                                print(f"👁️‍🗨️ Face Analysis: Live={analysis_result['is_live']}, Score={analysis_result['match_score']:.2f}")

                    except Exception as e:
                        # --- CRITICAL DEBUGGING LOGIC ---
                        if str(e) == 'Track ended':
                            print("Video track ended gracefully.")
                        else:
                            print("-" * 60)
                            print(f"FATAL VIDEO PROCESSING CRASH: {e}")
                            traceback.print_exc() # <--- Prints the exact line of the Python error
                            print("-" * 60)
                        break
            
            # Audio track is read to prevent pipeline blockage
            if track.kind == "audio":
                while True:
                    try:
                        await track.recv()
                    except Exception:
                        break
        
        return pc

# -----------------------------
# FastAPI Routes for Signaling (remain the same)
# -----------------------------
@router.post("/offer")
async def webrtc_offer(offer: dict):
    pc = WebRTCManager.create_peer_connection()
    # ... (rest of the offer/answer logic) ...
    try:
        offer_sdp = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        await pc.setRemoteDescription(offer_sdp)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }

    except Exception as e:
        pcs.discard(pc)
        raise HTTPException(status_code=400, detail=f"WebRTC Answer Error: {e}")


@router.post("/ice")
async def webrtc_ice(candidate: dict):
    if not pcs:
         raise HTTPException(status_code=400, detail="No active PeerConnection found.")
    
    pc = next(iter(pcs))
    
    try:
        candidate_obj = RTCIceCandidate(
            sdpMid=candidate["sdpMid"],
            sdpMLineIndex=candidate["sdpMLineIndex"],
            candidate=candidate["candidate"],
        )
        await pc.addIceCandidate(candidate_obj)
        return {"status": "ok"}

    except Exception as e:
        print(f"Error adding ICE candidate: {e}") 
        return {"status": "error", "detail": str(e)}