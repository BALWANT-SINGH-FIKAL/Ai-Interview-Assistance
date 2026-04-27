# backend/app/routes/interview.py
from fastapi import APIRouter, HTTPException
# CORRECT IMPORTS: Use simple 'app.' prefix
from app.core.interview_manager import interview_manager

router = APIRouter()

@router.post("/summary")
async def get_summary(payload: dict):
    """Retrieves the summary of a completed interview session."""
    session_id = payload.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    summary = interview_manager.get_session_summary(session_id) 
    return {"session_id": session_id, "summary": summary}