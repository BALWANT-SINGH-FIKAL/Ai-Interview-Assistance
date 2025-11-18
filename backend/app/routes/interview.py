from fastapi import APIRouter
from app.services.webrtc_manager import webrtc_manager

router = APIRouter()

@router.post("/offer")
async def receive_offer(offer: dict):
    answer = await webrtc_manager.create_answer(offer)
    return answer
