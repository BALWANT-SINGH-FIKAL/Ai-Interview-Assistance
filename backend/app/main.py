from fastapi import FastAPI
from app.routes.interview import router as interview_router

app = FastAPI(title="AI Interview Backend")

app.include_router(interview_router, prefix="/api/interview")


@app.get("/")
def root():
    return {"message": "Backend running"}
