// frontend/src/ws/interviewSocket.js

class InterviewSocket {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectInterval = 3000;
        this.sessionId = null;

        this.onQuestionCallback = null;
        this.onEndCallback = null;
        this.onStatusCallback = null;
    }

    connect() {
        return new Promise((resolve) => {
            // NOTE: URL is already fixed to /session for unique path
            const url = "ws://localhost:8000/session"; 
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                this.connected = true;
                console.log("WebSocket connected to backend");
                resolve(true);
            };

            this.ws.onclose = () => {
                this.connected = false;
                console.warn("WebSocket disconnected. Reconnecting...");
                setTimeout(() => this.connect(), this.reconnectInterval);
            };

            this.ws.onerror = (err) => {
                console.error("WebSocket error:", err);
            };

            this.ws.onmessage = (event) => {
                // --- FIX: Message Type Separation ---
                if (typeof event.data === 'string') {
                    // This is TEXT data (JSON control messages)
                    this.handleMessage(event.data);
                } else if (event.data instanceof Blob) {
                    // This is BINARY data (TTS audio blob)
                    this.handleAudio(event.data);
                } else {
                    console.warn("Received unknown message type:", typeof event.data);
                }
            };
            // -------------------------------------
        });
    }

    // -------------------------
    //    NEW: Audio Handler
    // -------------------------
    // frontend/src/ws/interviewSocket.js (Key Change in handleAudio)

// ... existing connection logic ...

// -------------------------
//    NEW: Audio Handler
// -------------------------
handleAudio(audioBlob) {
    console.log(`Received TTS audio blob of size: ${audioBlob.size} bytes. Playing...`);
    
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    // 1. Attempt Playback
    audio.play().catch(e => {
        // Playback failed due to Autoplay Policy.
        console.warn("Autoplay blocked:", e.name);
        alert("Audio playback failed. Please use the 'Replay Question' button to hear the audio.");
    });

    // 2. Enable the Replay Button (This relies on the onStatus callback in interview.js)
    if (this.onStatusCallback) {
        // Send a custom status that the frontend can use to enable the replay button
        this.onStatusCallback("Audio received and replay enabled."); 
    }

    // 3. Clean up the URL after playback ends
    audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        // We will re-enable the replay button on status update from the backend
    };
}
// ... (rest of the file remains the same) ...
    
    // -------------------------
    //    Message Handlers (Only handles JSON/Text now)
    // -------------------------
    handleMessage(data) {
        try {
            const msg = JSON.parse(data);

            switch (msg.event) {
                case "connected":
                    console.log("Connected event:", msg.message);
                    // Store session ID if it comes in the connected message
                    if (msg.session_id) this.sessionId = msg.session_id;
                    break;

                case "ai_question":
                    if (this.onQuestionCallback) {
                        this.onQuestionCallback(msg);
                    }
                    break;

                case "session_ended":
                    if (this.onEndCallback) {
                        this.onEndCallback(msg.presentation, msg.report);
                    }
                    break;

                case "status":
                    if (this.onStatusCallback) {
                        this.onStatusCallback(msg.message);
                    }
                    break;

                case "ack":
                    console.log("ACK:", msg.message);
                    break;

                case "error":
                    console.error("Backend Error:", msg.message);
                    break;

                default:
                    console.log("Unknown event:", msg);
            }
        } catch (err) {
            // This catch block is for invalid JSON strings only
            console.error("Invalid WS message (JSON parse error):", err);
        }
    }

    // -------------------------
    //     API Calls (unchanged)
    // -------------------------

    startInterview(sessionId, category) {
        this.sessionId = sessionId;

        console.log("Starting interview:", sessionId, category);

        this.ws.send(
            JSON.stringify({
                event: "start_interview",
                session_id: sessionId,
                interview_type: category, 
            })
        );
    }

    sendTranscript(text) {
        if (!this.sessionId) {
            console.error("Session ID missing when sending transcript");
            return;
        }

        this.ws.send(
            JSON.stringify({
                event: "audio_transcript",
                session_id: this.sessionId,
                text: text,
            })
        );
    }

    endInterview() {
        if (!this.sessionId) return;

        this.ws.send(
            JSON.stringify({
                event: "end_interview",
                session_id: this.sessionId,
            })
        );
    }

    // -------------------------
    //  Callback Registrations (unchanged)
    // -------------------------
    onQuestion(callback) {
        this.onQuestionCallback = callback;
    }

    onEnd(callback) {
        this.onEndCallback = callback;
    }

    onStatus(callback) {
        this.onStatusCallback = callback;
    }
    replayQuestion() {
        if (!this.sessionId) {
            console.error("Session ID missing for replay");
            return;
        }

        this.ws.send(
            JSON.stringify({
                event: "replay_question",
                session_id: this.sessionId,
            })
        );
    }
}

export const interviewSocket = new InterviewSocket();