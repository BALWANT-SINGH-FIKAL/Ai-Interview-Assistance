# backend/app/services/stt_local.py
import speech_recognition as sr
import os
from pydub import AudioSegment 
from typing import Optional

# FIX 1: Initialize the Recognizer as a global singleton BEFORE the class definition.
# This avoids the 'LocalSTTService' object has no attribute 'recognizer' error.
recognizer_instance = sr.Recognizer()

class LocalSTTService:
    # FIX 2: We no longer need this __init__ method if it was only for sr.Recognizer().
    # If there was other initialization logic, it would remain here.
    def __init__(self):
        pass

    def transcribe_audio_file(self, file_path: str) -> Optional[str]:
        """
        Transcribes the audio file located at file_path, converting it to PCM WAV first.
        """
        # Define the path for the converted file
        temp_wav_path = file_path.replace(".wav", "_converted.wav") 
        
        try:
            # --- 1. Conversion Logic (WebM/OGG -> PCM WAV) ---
            # NOTE: This requires FFmpeg to be installed on the system.
            audio_data = AudioSegment.from_file(file_path)
            audio_data.export(temp_wav_path, format="wav")
            print(f"Audio file successfully converted to WAV: {temp_wav_path}")
            # -------------------------------------------------

            # --- 2. Transcription ---
            # Use the global recognizer instance on the converted file
            with sr.AudioFile(temp_wav_path) as source: 
                audio = recognizer_instance.record(source) 
            
            # Use the global instance to transcribe
            # FIX 3: Remove the 'timeout' argument, as it caused the unexpected keyword argument error.
            transcript = recognizer_instance.recognize_google(
                audio, 
                show_all=False
            )
            
            return transcript
        
        # --- Error Handling (Essential for robust STT) ---
        except sr.UnknownValueError:
            print(f"LocalSTTService: Could not understand audio in file: {file_path}")
            return "Could not understand audio."
        
        except sr.WaitTimeoutError:
            print("LocalSTTService: Transcription request timed out (default timeout used).")
            return "Transcription timed out."

        except sr.RequestError as e:
            print(f"LocalSTTService: Could not request results from Google Speech Recognition service; {e}")
            return "Transcription service error."

        except Exception as e:
            print(f"LocalSTTService: An unexpected error occurred: {e}")
            # This catch handles errors like a missing FFmpeg
            if "ffmpeg" in str(e).lower():
                return "FFmpeg dependency missing or incorrectly configured."
            return "Unexpected transcription error."
        
        finally:
            # Clean up both the original file and the converted file
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            
# Initialize the service instance (This uses the globally defined recognizer_instance)
local_stt_service = LocalSTTService()