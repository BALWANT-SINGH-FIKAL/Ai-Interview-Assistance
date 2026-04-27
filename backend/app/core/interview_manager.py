# backend/app/core/interview_manager.py
import uuid
import time
import json
import os
import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket

# --- Service Imports (FIX: Use relative imports for sibling folders) ---
from ..services.stt_local import local_stt_service 
from ..services.tts_local import local_tts_service 
from ..services.speaker_verifier import speaker_verifier # PHASE 6: SPEAKER VERIFIER

# Define the local directory path for temporary audio storage
TEMP_AUDIO_DIR = os.path.join(os.getcwd(), 'temp_audio')

# Simple type hint
Question = Dict[str, object]

class Session:
    """
    Holds per-session state, including the WebSocket and last question audio data.
    """
    def __init__(self, websocket: WebSocket, session_id: Optional[str] = None, meta: Optional[Dict] = None):
        self.id = session_id or str(uuid.uuid4())
        self.meta = meta or {}
        self.questions: List[Question] = []
        self.answers: List[Dict] = []
        self.current_index = -1
        self.websocket = websocket
        
        self.last_question_audio_data: Optional[bytes] = None 

    def push_question(self, q: Question):
        self.questions.append(q)
        self.current_index = len(self.questions) - 1

    def push_answer(self, question_id: str, text: str):
        self.answers.append({
            "question_id": question_id,
            "text": text,
            "timestamp": int(time.time())
        })

class InterviewManager:
    """
    Manages interview sessions, state transitions, question generation, and service integration.
    """
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.question_bank = {
            "technical": [
                {"category": "technical", "difficulty": "easy", "text": "Explain the difference between a stack and a queue."},
                {"category": "technical", "difficulty": "medium", "text": "How does a hash table handle collisions?"},
                {"category": "technical", "difficulty": "hard", "text": "Design a URL shortener. Explain data model and scaling concerns."},
            ],
            "hr": [
                {"category": "hr", "difficulty": "easy", "text": "Tell me about yourself and your strengths."},
                {"category": "hr", "difficulty": "medium", "text": "Describe a conflict at work and how you resolved it."},
                {"category": "hr", "difficulty": "medium", "text": "Why do you want to work at this company?"}
            ],
        }

    # ... (Utility methods _make_question_obj and _select_question remain the same) ...
    def _make_question_obj(self, category: str, difficulty: str, text: str) -> Question:
        return {
            "id": str(uuid.uuid4()),
            "category": category,
            "difficulty": difficulty,
            "text": text,
            "timestamp": int(time.time())
        }

    def _select_question(self, interview_type: str, step: int, resume_data: Optional[Dict] = None, skills: Optional[List[str]] = None) -> Question:
        bank = self.question_bank.get(interview_type, self.question_bank["technical"])
        template = bank[step % len(bank)]
        return self._make_question_obj(template["category"], template["difficulty"], template["text"])


    async def _send_question_with_tts(self, session: Session, question: Question):
        """
        Generates TTS audio for the question, stores it, and sends both text and audio to the client.
        """
        await session.websocket.send_json({"event": "ai_question", "question": question})
        
        loop = asyncio.get_event_loop()
        audio_file_path = await loop.run_in_executor(None, local_tts_service.synthesize_and_save, question["text"])

        if audio_file_path and os.path.exists(audio_file_path):
            try:
                with open(audio_file_path, "rb") as f:
                    audio_data = f.read()
                
                session.last_question_audio_data = audio_data 
                
                await session.websocket.send_bytes(audio_data)
                print(f"Sent TTS audio file of size {len(audio_data)} bytes.")

            except Exception as e:
                print(f"Error sending TTS audio: {e}")
            finally:
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
        else:
            await session.websocket.send_json({"event": "status", "message": "TTS audio unavailable."})

    async def run_stt_transcription(self, file_path: str) -> Optional[str]:
        """Runs the transcription service in a thread pool executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, local_stt_service.transcribe_audio_file, file_path)


    # -----------------------------
    # Public API (ASYNCHRONOUS)
    # -----------------------------
    
    def create_session(self, websocket: WebSocket) -> str:
        """Create a new Session and link the WebSocket."""
        session = Session(websocket=websocket)
        self.sessions[session.id] = session
        return session.id
    
    async def handle_user_message(self, session_id: str, text_data: str):
        """
        Handles incoming JSON (text) control messages from the client.
        """
        session = self.sessions.get(session_id)
        if not session:
            return 
    
        try:
            msg = json.loads(text_data)
            event = msg.get("event")
            
            if event == "start_interview":
                interview_type = msg.get("interview_type", "technical")
                await self.start_interview(interview_type=interview_type, session_id=session_id)
                return 
            
            # --- Replay Question Handler ---
            if event == "replay_question":
                if session.last_question_audio_data:
                    await session.websocket.send_bytes(session.last_question_audio_data)
                    await session.websocket.send_json({"event": "status", "message": "Question replayed."})
                else:
                    await session.websocket.send_json({"event": "status", "message": "No audio available to replay."})
                return 
            # ------------------------------------
            
            if event == "end_interview":
                self.end_session(session_id)
                await session.websocket.send_json({"event": "session_ended", "message": "Interview terminated by user."})
                return 
    
        except json.JSONDecodeError:
            print(f"Received non-JSON text data in manager: {text_data}")
            return 
        
        return None


    async def process_audio_chunk(self, session_id: str, audio_data: bytes):
        """
        Handles incoming audio data, saves it temporarily, transcribes it, 
        and performs SPEAKER VERIFICATION.
        """
        session = self.sessions.get(session_id)
        if not session:
            print(f"Audio received for non-existent session: {session_id}")
            return
        
        # FIX: Construct the file path using the correct, writable directory (TEMP_AUDIO_DIR)
        temp_filename = os.path.join(TEMP_AUDIO_DIR, f"stt_{uuid.uuid4()}.wav") 
        
        try:
            # Ensure the directory exists before attempting to write
            if not os.path.exists(TEMP_AUDIO_DIR):
                os.makedirs(TEMP_AUDIO_DIR)
                
            # 1. Save the audio blob to a temporary file
            with open(temp_filename, "wb") as f:
                f.write(audio_data)
        
        except Exception as e:
            # The client receives this error message
            await session.websocket.send_json({"event": "error", "message": f"Server failed to save audio: {e}"})
            return
        
        await session.websocket.send_json({"event": "status", "message": "Audio received. Transcribing and verifying..."})
        
        # ----------------------------------------------------
        # PHASE 6: SPEAKER VERIFICATION (Step 15)
        # ----------------------------------------------------
        
        # 1. Run Verification / Enrollment check
        if speaker_verifier.is_user_enrolled:
            loop = asyncio.get_event_loop()
            verification_result = await loop.run_in_executor(None, speaker_verifier.verify_speaker, temp_filename)
            
            if not verification_result["is_verified"]:
                await session.websocket.send_json({"event": "warning", "message": f"Speaker Mismatch Detected! Score: {verification_result['score']}. Please re-verify your identity."})
            else:
                await session.websocket.send_json({"event": "status", "message": f"Speaker Verified. Score: {verification_result['score']}"})
        else:
            # 2. Automatically enroll the first spoken answer as the reference
            loop = asyncio.get_event_loop()
            enroll_success = await loop.run_in_executor(None, speaker_verifier.enroll_user, temp_filename)
            if enroll_success:
                 await session.websocket.send_json({"event": "status", "message": "Speaker profile created (first answer used for enrollment)." })
            else:
                 await session.websocket.send_json({"event": "warning", "message": "Speaker enrollment failed." })

        # ----------------------------------------------------
        # PHASE 4: STT (Transcription)
        # ----------------------------------------------------
        transcript = await self.run_stt_transcription(temp_filename)
        
        # 3. Process the answer (after verification)
        if transcript:
            await session.websocket.send_json({"event": "status", "message": f"Transcript: '{transcript}'"})
            await self.process_answer(transcript, session_id)
        else:
            await session.websocket.send_json({"event": "status", "message": "Could not understand audio. Please try again."})


    async def start_interview(self, interview_type: str = "technical", resume_data: Optional[Dict] = None, skills: Optional[List[str]] = None, session_id: Optional[str] = None):
        """
        Set up the session parameters and send the first question.
        """
        session = self.sessions.get(session_id)
        if not session: return

        session.meta.update({"interview_type": interview_type, "resume_data": resume_data or {}, "skills": skills or []})

        q = self._select_question(interview_type, step=0, resume_data=resume_data, skills=skills)
        session.push_question(q)
        
        await self._send_question_with_tts(session, q)


    async def process_answer(self, answer_text: str, session_id: Optional[str] = None):
        """
        Accept a user's answer, store it, and produce the next question (and TTS audio).
        """
        session = self.sessions.get(session_id)
        if not session: return

        # Store the answer
        last_q = session.questions[session.current_index] if session.current_index >= 0 else None
        if last_q:
            session.push_answer(last_q["id"], answer_text)
        else:
            session.push_answer("none", answer_text)

        next_step = len(session.answers)
        interview_type = session.meta.get("interview_type", "technical")
        
        next_q = self._select_question(interview_type, step=next_step)
        session.push_question(next_q)
        
        await self._send_question_with_tts(session, next_q)


    def end_session(self, session_id: str):
        """Terminate and cleanup a session, including any stored WebSocket connection."""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Define the global manager instance for use in the router
interview_manager = InterviewManager()