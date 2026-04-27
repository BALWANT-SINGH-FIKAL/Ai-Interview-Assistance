# backend/app/services/tts_local.py (UPDATED FIX)
import pyttsx3
import uuid
import os
from typing import Optional

# Define the absolute path to the new writable temporary directory
# os.path.join handles path separators correctly across Windows/Linux/macOS
TEMP_DIR = os.path.join(os.getcwd(), 'temp_audio')

class LocalTTSService:
    """
    Handles Text-to-Speech using the local 'pyttsx3' library.
    Saves speech to a temporary WAV file in a project-local directory.
    """
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)

            # Ensure the temporary directory exists
            if not os.path.exists(TEMP_DIR):
                os.makedirs(TEMP_DIR)
                
            print("Local TTS Engine initialized successfully.")
        except Exception as e:
            print(f"Warning: pyttsx3 failed to initialize. TTS features disabled. Error: {e}")
            self.engine = None
    
    def synthesize_and_save(self, text: str) -> Optional[str]:
        """
        Synthesizes text to speech and saves it as a temporary WAV file.
        Returns the path to the saved file.
        """
        if not self.engine:
            return None
        
        # FIX: Use the project-local, absolute temporary path
        temp_filename = os.path.join(TEMP_DIR, f"tts_{uuid.uuid4()}.wav")
        
        try:
            self.engine.save_to_file(text, temp_filename)
            self.engine.runAndWait()
            
            if os.path.exists(temp_filename):
                return temp_filename
            else:
                print(f"TTS synthesis failed to create file at: {temp_filename}")
                return None

        except Exception as e:
            print(f"TTS Synthesis Error: {e}")
            return None

# Initialize the service instance
local_tts_service = LocalTTSService()