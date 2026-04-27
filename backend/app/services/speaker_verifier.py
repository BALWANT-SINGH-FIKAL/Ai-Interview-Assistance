# backend/app/services/speaker_verifier.py
import torch
import numpy as np
import os
from speechbrain.pretrained import EncoderClassifier
from typing import Optional, Dict, Any

class SpeakerVerifierService:
    """
    Manages voice biometrics using a pre-trained SpeechBrain model (Phase 6).
    Performs enrollment and runtime verification against an audio file path.
    """
    def __init__(self):
        self.enrolled_embedding: Optional[torch.Tensor] = None
        self.is_user_enrolled = False
        
        # --- SpeechBrain Model Setup (Step 14) ---
        try:
            # We use a widely recognized speaker verification model (ECAPA-TDNN)
            self.classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                run_opts={"device":"cpu"} # Force CPU usage for broad compatibility
            )
            print("Speaker Verification Model initialized successfully.")
        except Exception as e:
            self.classifier = None
            print(f"Warning: Speaker Verifier initialization failed. Error: {e}")

    def _extract_embedding(self, audio_file_path: str) -> Optional[torch.Tensor]:
        """Extracts the d-vector embedding (voice fingerprint) from an audio file."""
        if self.classifier is None or not os.path.exists(audio_file_path):
            return None
        
        # SpeechBrain returns output (embeddings) and prediction (ignored here)
        with torch.no_grad():
            output_tensor = self.classifier.encode_file(audio_file_path)
            # Embedding is typically the first element after unsqueezing batch dimension
            return output_tensor.squeeze(0).squeeze(0) 

    def enroll_user(self, audio_file_path: str) -> bool:
        """Stores the user's voice embedding for future comparison (Enrollment Phase)."""
        embedding = self._extract_embedding(audio_file_path)
        if embedding is not None:
            self.enrolled_embedding = embedding
            self.is_user_enrolled = True
            print("Speaker enrolled successfully.")
            return True
        return False

    def verify_speaker(self, audio_file_path: str, threshold: float = 0.5) -> Dict[str, Any]:
        """Verifies a live audio sample against the enrolled speaker (Step 15)."""
        if not self.is_user_enrolled:
            return {"is_verified": False, "score": 0.0, "message": "No speaker enrolled."}
        
        live_embedding = self._extract_embedding(audio_file_path)
        
        if live_embedding is None:
            return {"is_verified": False, "score": 0.0, "message": "Could not extract live voice features."}
        
        # --- Calculate Cosine Similarity (Verification Score) ---
        # Cosine Similarity is: dot_product / (norm_enrolled * norm_live)
        similarity_score = torch.nn.functional.cosine_similarity(
            self.enrolled_embedding.unsqueeze(0), 
            live_embedding.unsqueeze(0)
        ).item() # .item() converts the single tensor value to a float

        is_verified = similarity_score > threshold
        
        return {
            "is_verified": is_verified,
            "score": round(similarity_score, 4),
            "message": "Match successful." if is_verified else "Voice mismatch detected."
        }

# Global singleton instance
speaker_verifier = SpeakerVerifierService()