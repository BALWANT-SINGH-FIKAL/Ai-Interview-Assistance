# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# CORRECT IMPORTS: Use simple 'app.' prefix since we run from the backend directory.
from app.routes.interview import router as interview_router
from app.services.webrtc_manager import router as webrtc_router
from app.routes.ws_endpoint import router as ws_router

app = FastAPI(title="AI Interview Backend")

# -----------------------------
# CORS Setup 
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"], 
    allow_credentials=True,
    allow_methods=["*", "GET", "OPTIONS"], # Necessary for WebSocket Handshake
    allow_headers=["*"],
)

# -----------------------------
# Routers (FIX: WS must be included first)
# -----------------------------
# FIX: Include WebSocket router (with prefix) first to prevent 403 route conflict.
app.include_router(ws_router) 

app.include_router(interview_router, prefix="/api/interview")
app.include_router(webrtc_router, prefix="/api/webrtc")

# Root endpoint (most general route, kept at the bottom)
@app.get("/")
def root():
    return {"message": "Backend running"}