# backend/app/services/face_processor.py
import numpy as np
import time
import os
from typing import Dict, Any, Optional

# Import the necessary libraries for Computer Vision and InsightFace
import cv2
from insightface.app import FaceAnalysis
# Note: For DeepFace liveness/spoofing, you would import DeepFace here.

class FaceProcessorService:
    """
    Manages real-time processing of video frames for identity verification and liveness checks (Phase 5).
    """
    def __init__(self):
        self.enrolled_embedding: Optional[np.ndarray] = None
        self.is_user_enrolled = False
        
        # --- InsightFace Model Setup (Step 10) ---
        try:
            # Initialize the FaceAnalysis app (uses buffalo_l model for high accuracy)
            self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            # Prepare the model for inference
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            print("InsightFace Model initialized successfully.")
        except Exception as e:
            self.app = None
            print(f"Warning: InsightFace initialization failed. Face analysis disabled. Error: {e}")

    def enroll_user(self, frame_np: np.ndarray) -> bool:
        """
        Extracts embedding from a user's frame and stores it for verification (Step 10).
        """
        if self.app is None: return False
        
        # 1. Detect and get features from the frame
        faces = self.app.get(frame_np)
        
        if faces and len(faces) == 1:
            # Assume the first detected face is the correct one for enrollment
            self.enrolled_embedding = faces[0].normed_embedding
            self.is_user_enrolled = True
            print("User face enrolled successfully.")
            return True
        return False

    def process_frame(self, frame_np: np.ndarray) -> Dict[str, Any]:
        """
        Receives an image frame (NumPy array) and performs real-time face analysis (Step 11 & 12).
        """
        if self.app is None or frame_np is None:
            # Ensures a full dictionary is returned on initialization error
            return {"status": "error", "message": "Processor not initialized or empty frame.", 
                    "is_live": False, "match_score": 0.0, "face_detected": False}
            
        faces = self.app.get(frame_np)
        
        # --- FIX 1: Return a complete, safe dictionary if NO face is detected ---
        if not faces:
            return {
                "timestamp": time.time(),
                "face_detected": False,
                "match_score": 0.0,
                "liveness_score": 0.0,
                "is_verified": False,
                "is_live": False,  # CRITICAL: Always include 'is_live'
                "status": "no_face"
            }
        
        # Assume we only care about the largest/first detected face
        live_embedding = faces[0].normed_embedding
        
        # --- Placeholder Liveness Check (Step 12) ---
        is_live = True # Placeholder: Assume live for now
        liveness_score = 1.0 

        # --- Identity Verification (Step 11) ---
        match_score = 0.0
        if self.is_user_enrolled and self.enrolled_embedding is not None:
            # Calculate cosine similarity (standard for face verification)
            dot_product = np.dot(self.enrolled_embedding, live_embedding)
            norm_product = np.linalg.norm(self.enrolled_embedding) * np.linalg.norm(live_embedding)
            match_score = dot_product / norm_product if norm_product else 0.0
        
        # --- FIX 2: Ensure 'is_live' is included in the successful result dictionary ---
        return {
            "timestamp": time.time(),
            "face_detected": True,
            "match_score": float(match_score),
            "liveness_score": float(liveness_score),
            "is_verified": match_score > 0.4 and is_live, 
            "is_live": is_live,  # CRITICAL: Include the is_live status
            "status": "verified" if match_score > 0.4 else "unmatched"
        }
# Global singleton instance
face_processor = FaceProcessorService()