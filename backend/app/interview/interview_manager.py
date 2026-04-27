# backend/app/core/interview_manager.py (FINAL FIX FOR MODULE RESOLUTION)
import uuid
import time
import json
import os
import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket

# --- Service Imports ---
# CORRECT FIX: Use relative import (..) to step up one directory (to 'app') 
# and then down into the 'services' package.

# Corrected STT Import
from ..services.stt_local import local_stt_service 
# Corrected TTS Import
from ..services.tts_local import local_tts_service 

# Simple type hint
Question = Dict[str, object]

class Session:
    """
    Holds per-session state: question history, answers, meta, and the WebSocket connection.
    """
    def __init__(self, websocket: WebSocket, session_id: Optional[str] = None, meta: Optional[Dict] = None):
        self.id = session_id or str(uuid.uuid4())
        self.meta = meta or {}
        self.questions: List[Question] = []
        self.answers: List[Dict] = []  # each: {"question_id":..., "text":..., "timestamp":...}
        self.current_index = -1  # index into questions of the last asked
        self.websocket = websocket # Store the active WebSocket connection

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
        # session_id -> Session
        self.sessions: Dict[str, Session] = {}

        # Seeded question bank
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
            # ... (other question types omitted for brevity, but they follow the same structure)
        }

    # -----------------------------
    # Utilities
    # -----------------------------
    def _make_question_obj(self, category: str, difficulty: str, text: str) -> Question:
        return {
            "id": str(uuid.uuid4()),
            "category": category,
            "difficulty": difficulty,
            "text": text,
            "timestamp": int(time.time())
        }

    def _select_question(self, interview_type: str, step: int, resume_data: Optional[Dict] = None, skills: Optional[List[str]] = None) -> Question:
        """Simple question selection policy: cycles through seeded bank."""
        bank = self.question_bank.get(interview_type, self.question_bank["technical"])
        template = bank[step % len(bank)]
        # Simplified logic: resume_data templating removed for brevity, using only seeded bank
        return self._make_question_obj(template["category"], template["difficulty"], template["text"])

    async def _send_question_with_tts(self, session: Session, question: Question):
        """
        Generates TTS audio for the question, sends both text and audio to the client.
        """
        # 1. Send the question text (JSON)
        await session.websocket.send_json({"event": "ai_question", "question": question})
        
        # 2. Run the synchronous TTS synthesis in an executor (non-blocking)
        loop = asyncio.get_event_loop()
        audio_file_path = await loop.run_in_executor(None, local_tts_service.synthesize_and_save, question["text"])

        # 3. Send the TTS audio (Binary)
        if audio_file_path and os.path.exists(audio_file_path):
            try:
                with open(audio_file_path, "rb") as f:
                    audio_data = f.read()
                
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
        # Call the synchronous transcribe_audio_file function
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
            return await session.websocket.send_json({"event": "error", "message": f"Session {session_id} not found."})

        try:
            msg = json.loads(text_data)
            
            if msg.get("event") == "start_interview":
                interview_type = msg.get("interview_type", "technical")
                # Resume data/skills handling omitted for brevity
                await self.start_interview(interview_type=interview_type, session_id=session_id)
            
            if msg.get("event") == "end_interview":
                # Clean up and notify client
                # In a full setup, this would generate and send the final report
                self.end_session(session_id)
                await session.websocket.send_json({"event": "session_ended", "message": "Interview terminated by user."})

        except json.JSONDecodeError:
            print(f"Received non-JSON text data in manager: {text_data}")


    async def process_audio_chunk(self, session_id: str, audio_data: bytes):
        """
        Handles incoming audio data, saves it temporarily, transcribes it, 
        and calls process_answer with the resulting text.
        (Assumes audio_data is the complete audio blob from the client)
        """
        session = self.sessions.get(session_id)
        if not session:
            print(f"Audio received for non-existent session: {session_id}")
            return
        
        # 1. Save the audio blob to a temporary file
        temp_filename = f"/tmp/{uuid.uuid4()}.wav" # Save as WAV for speech_recognition
        try:
            with open(temp_filename, "wb") as f:
                f.write(audio_data)
        except Exception as e:
            await session.websocket.send_json({"event": "error", "message": f"Server failed to save audio: {e}"})
            return
        
        await session.websocket.send_json({"event": "status", "message": "Audio received. Transcribing..."})
        
        # 2. Transcribe the audio file asynchronously
        transcript = await self.run_stt_transcription(temp_filename)
        
        # 3. Process the answer
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
            # NOTE: This is where LLM analysis (Phase 7) would occur before storing
            session.push_answer(last_q["id"], answer_text)
        else:
            session.push_answer("none", answer_text)

        next_step = len(session.answers)
        interview_type = session.meta.get("interview_type", "technical")
        
        next_q = self._select_question(interview_type, step=next_step) # Simplified selection
        session.push_question(next_q)
        
        await self._send_question_with_tts(session, next_q)


    def end_session(self, session_id: str):
        """Terminate and cleanup a session, including any stored WebSocket connection."""
        if session_id in self.sessions:
            # We would also clean up any database/storage objects here
            del self.sessions[session_id]

# Define the global manager instance for use in the router
interview_manager = InterviewManager()