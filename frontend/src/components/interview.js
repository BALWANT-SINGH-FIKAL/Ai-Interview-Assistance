import React, { useEffect, useState, useRef } from "react";
import { useLocation } from "react-router-dom";
import { interviewSocket } from "../ws/interviewsocket"; // Fix casing
import { getLocalMedia } from "../webrtc"; 
import AudioStreamer from "./audiostreamer"; 
// NEW IMPORTS for WebRTC Signaling:
import { createLocalPeer, sendOffer, sendIceCandidate } from '../webrtc'; 

export default function Interview() {
    const location = useLocation();
    const selectedCategoryFromEntry = location.state?.selectedCategory;

    const [status, setStatus] = useState("idle");
    const [question, setQuestion] = useState(null);
    const [category, setCategory] = useState(selectedCategoryFromEntry || "technical");
    
    // NEW STATES
    const [isRecording, setIsRecording] = useState(false);
    const [micReady, setMicReady] = useState(false);
    const [micError, setMicError] = useState(null);
    const [canReplay, setCanReplay] = useState(false); 
    const [videoReady, setVideoReady] = useState(false); // Track video status

    const mediaStreamRef = useRef(null);
    const audioStreamerRef = useRef(null);
    const videoRef = useRef(null); // Ref for the video element
    const peerConnectionRef = useRef(null); // Ref for RTCPeerConnection

    // -------------------------------
    //  INIT: Connect WebSocket & Media Stream
    // -------------------------------
    useEffect(() => {
        // 1. Connect WebSocket
        interviewSocket.connect().then(() => {
            console.log("WS ready");
        });

        const setupMediaAndSignaling = async () => {
            // NOTE: Requesting BOTH audio and video here for Phase 5 setup
            const { success, stream, error: mediaError } = await getLocalMedia({ video: true, audio: true });
            
            if (success) {
                mediaStreamRef.current = stream;
                
                // 1. Setup Audio & UI States (Phase 4)
                audioStreamerRef.current = new AudioStreamer(stream); 
                setMicReady(true);
                setVideoReady(true); // Assuming video is ready if mic is ready
                console.log("Mic stream ready and AudioStreamer initialized.");
                
                // Attach stream to the local video element for user preview
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }

                // 2. PHASE 5: START WEBRTC SIGNALING (CRITICAL LOGIC ADDED HERE)
                const pc = createLocalPeer(
                    stream, 
                    // onCandidateCallback: Send ICE candidate to backend
                    (candidate) => sendIceCandidate(candidate), 
                    // onOfferCallback: Send SDP offer to backend
                    async (offer) => {
                        try {
                            const answerData = await sendOffer(offer);
                            // Receive the answer and set it as remote description
                            await pc.setRemoteDescription(new RTCSessionDescription(answerData));
                            console.log("WebRTC Answer received and set.");
                        } catch (error) {
                            console.error("Error processing WebRTC answer:", error);
                        }
                    }
                );
                peerConnectionRef.current = pc;
                console.log("WebRTC Signaling initiated (Offer Sent).");
                
            } else {
                setMicReady(false);
                setVideoReady(false);
                setMicError(mediaError.name || mediaError.message || "Unknown media error.");
                console.error("❌ Media Access Failed! Error:", mediaError);
            }
        };
        
        setupMediaAndSignaling();

        // 3. Register WS Callbacks
        interviewSocket.onQuestion((msg) => {
            console.log("Received new question:", msg.question.text);
            setQuestion(msg.question);
            setCanReplay(true); // ENABLE REPLAY BUTTON
        });

        interviewSocket.onEnd((presentation, report) => {
            console.log("Interview ended");
            setStatus("ended");
        });
        
        interviewSocket.onStatus((message) => {
            console.log("Status update:", message);
            if (message === "Audio received and replay enabled." || message === "Question replayed.") {
                setCanReplay(true); 
            }
        });

        // Cleanup function
        return () => {
            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach(track => track.stop());
            }
            // Close the PeerConnection on unmount
            if (peerConnectionRef.current) {
                peerConnectionRef.current.close();
            }
        };
    }, []);

    // -------------------------------
    //  REPLAY CONTROL
    // -------------------------------
    const handleReplay = () => {
        if (canReplay) {
            setCanReplay(false);
            interviewSocket.replayQuestion();
        }
    };
    
    // -------------------------------
    //  AUDIO CONTROL FUNCTIONS
    // -------------------------------
    const startRecording = () => {
        if (!audioStreamerRef.current) {
            console.error("AudioStreamer not initialized. Cannot record without mic access.");
            return;
        }
        audioStreamerRef.current.startRecording();
        setIsRecording(true);
    };

    const stopRecordingAndSubmit = () => {
        if (!audioStreamerRef.current || !isRecording) {
            console.warn("Not currently recording or streamer is missing.");
            return;
        }
        audioStreamerRef.current.stopRecording();
        setIsRecording(false);
        setStatus("processing");
    };

    // -------------------------------
    //  Interview Control
    // -------------------------------
    const startInterview = () => {
        if (interviewSocket.connected) {
            interviewSocket.startInterview("TEST_ID", category);
            setStatus("started");
        } else {
            alert("WebSocket is not connected. Please refresh.");
        }
    };

    const endInterview = () => {
        if (isRecording) {
            stopRecordingAndSubmit(); 
        }
        interviewSocket.endInterview();
        setStatus("ended");
    };

    return (
        <div className="card" style={{ padding: 30, display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2>AI Interview Assistant</h2>
            <p>Status: **{status}** {isRecording && " (Recording/Listening)"}</p>

            {/* VIDEO FEED (User Preview for Phase 5) */}
            <div style={{ position: 'relative', width: '100%', maxWidth: '400px', margin: '0 auto' }}>
                <video 
                    ref={videoRef} 
                    autoPlay 
                    muted 
                    style={{ width: '100%', borderRadius: '8px', border: videoReady ? '3px solid green' : '3px solid gray' }}
                />
                <div style={{ position: 'absolute', bottom: '5px', left: '10px', color: 'white', background: 'rgba(0,0,0,0.5)', padding: '5px', borderRadius: '4px' }}>
                    {videoReady ? "Camera Active (Phase 5)" : "Waiting for Camera..."}
                </div>
            </div>


            {/* IDLE: BEFORE START */}
            {status === "idle" && (
                <div style={{ marginTop: 10 }}>
                    <label>Select interview type: </label>
                    <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        style={{ marginLeft: 10 }}
                    >
                        <option value="technical">Technical</option>
                        <option value="hr">HR</option>
                        <option value="behavioral">Behavioral</option>
                        <option value="resume_based">Resume Based</option>
                    </select>

                    <button 
                        onClick={startInterview} 
                        style={{ marginLeft: 10 }} 
                        disabled={!micReady || !interviewSocket.connected} 
                    >
                        Start Interview
                    </button>
                    
                    {/* MEDIA STATUS DISPLAY */}
                    <p style={{ marginTop: 10 }}>
                        Media Status: {micReady && videoReady ? "✅ Audio/Video Ready" : micError ? `❌ Failed: ${micError}` : "⏳ Checking..."}
                    </p>
                    
                    {micError && (
                        <p style={{color: 'orange', fontWeight: 'bold'}}>
                            Cannot start recording. Grant mic/camera access and reload.
                        </p>
                    )}
                </div>
            )}

            {/* ACTIVE INTERVIEW */}
            {(status === "started" || status === "processing") && (
                <div style={{ marginTop: 20 }}>
                    <h3>AI Question:</h3>
                    <div
                        style={{ padding: 10, background: "#f0f0f0", borderRadius: 8, minHeight: 60, }}
                    >
                        {question ? question.text : "Waiting for question..."}
                    </div>

                    {/* Replay Button */}
                    <button 
                        onClick={handleReplay} 
                        disabled={!canReplay}
                        style={{ marginTop: 10, marginRight: 10, background: '#1e90ff', color: 'white' }}
                    >
                        Replay Question 🔊
                    </button>

                    {/* Recording Controls */}
                    <div style={{ marginTop: 20 }}>
                        {micReady && !isRecording && status === "started" && (
                            <button onClick={startRecording} disabled={!audioStreamerRef.current}>
                                Start Recording Answer 🎤
                            </button>
                        )}
                        
                        {micReady && isRecording && (
                            <button onClick={stopRecordingAndSubmit} style={{ backgroundColor: 'red', color: 'white' }}>
                                Stop Recording & Submit Answer ⏹️
                            </button>
                        )}
                        
                        {status === "processing" && (
                            <p style={{ color: 'blue' }}>Submitting audio for transcription...</p>
                        )}
                        
                        {!micReady && (
                             <p style={{ color: 'red' }}>Recording is disabled due to Microphone error.</p>
                        )}
                    </div>
                    
                    <div style={{ marginTop: 20 }}>
                        <button onClick={endInterview}>End Interview</button>
                    </div>
                </div>
            )}
            {/* FINISHED (unchanged) */}
            {status === "ended" && (
                <div style={{ marginTop: 20 }}>
                    <h3>Interview Ended</h3>
                </div>
            )}
        </div>
    );
}