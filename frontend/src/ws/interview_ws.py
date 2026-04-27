# backend/app/ws/interview_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.interview_manager import interview_manager

router = APIRouter()

active_clients = {}   # session_id → websocket


@router.websocket("/ws/interview")
async def interview_socket(ws: WebSocket):
    await ws.accept()
    print("Client connected")

    try:
        while True:
            raw = await ws.receive_text()
            msg = interview_manager.safe_json(raw)

            event = msg.get("event")

            # ------------------------
            #   START INTERVIEW
            # ------------------------
            if event == "start_interview":
                session_id = msg["session_id"]
                category = msg["category"]

                active_clients[session_id] = ws

                print(f"Interview started: {session_id}, {category}")

                await ws.send_json({
                    "event": "ack",
                    "message": "Interview started"
                })

                # first question
                question = interview_manager.start_interview(session_id, category)

                await ws.send_json({
                    "event": "ai_question",
                    "text": question
                })

            # ------------------------
            #   TRANSCRIPT RECEIVED
            # ------------------------
            elif event == "audio_transcript":
                session_id = msg["session_id"]
                text = msg["text"]

                print("Transcript:", text)

                # Ask manager for next question or update
                reply = interview_manager.process_answer(session_id, text)

                if reply.get("finished"):
                    # send final report
                    await ws.send_json({
                        "event": "session_ended",
                        "presentation": reply["presentation"],
                        "report": reply["report"]
                    })
                else:
                    await ws.send_json({
                        "event": "ai_question",
                        "text": reply["question"]
                    })

            # ------------------------
            #   END INTERVIEW
            # ------------------------
            elif event == "end_interview":
                session_id = msg["session_id"]

                final_data = interview_manager.end_interview(session_id)

                await ws.send_json({
                    "event": "session_ended",
                    "presentation": final_data["presentation"],
                    "report": final_data["report"]
                })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print("WebSocket error:", e)
