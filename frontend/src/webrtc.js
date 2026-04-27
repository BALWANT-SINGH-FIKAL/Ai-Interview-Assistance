// frontend/src/webrtc.js (UPDATED & COMPLETED)

// Note: getLocalMedia remains the same.
export async function getLocalMedia({ audio = true, video = true } = {}){
    try{
        // FIX: Ensure video is requested here for Phase 5
        const constraints = { audio, video }; 
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        return { success: true, stream };
    }catch(err){
        return { success: false, error: err };
    }
}

// ------------------------------------------
// WebRTC Signaling Handlers (for backend /offer and /ice routes)
// ------------------------------------------

// Reuses the placeholder function, now adding media tracks.
export function createLocalPeer(stream, onCandidateCallback, onAnswerCallback){
    const config = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
    const pc = new RTCPeerConnection(config);
    
    // 1. Add tracks from the media stream
    stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
    });
    
    // 2. Event: When a local ICE candidate is generated, send it to the backend.
    pc.onicecandidate = (event) => {
        if (event.candidate) {
            onCandidateCallback(event.candidate.toJSON());
        }
    };
    
    // 3. Event: Log connection state changes
    pc.oniceconnectionstatechange = () => console.log('ICE state:', pc.iceConnectionState);
    pc.onconnectionstatechange = () => console.log('WebRTC state:', pc.connectionState);

    // 4. Create the Offer once ICE gathering completes
    pc.onnegotiationneeded = async () => {
        try {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);
            onAnswerCallback(pc.localDescription.toJSON()); // Send the OFFER to the backend
        } catch (e) {
            console.error('Error during negotiation:', e);
        }
    };

    return pc;
}

// Helper to send data via HTTP POST
async function sendSignal(endpoint, data) {
    const url = `http://localhost:8000/api/webrtc/${endpoint}`; // Uses the /api/webrtc prefix
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.json();
}

// Functions to be used by the React component:
export async function sendOffer(offerData) {
    // This sends the OFFER and receives the ANSWER from the backend
    return sendSignal('offer', offerData);
}

export async function sendIceCandidate(candidateData) {
    return sendSignal('ice', candidateData);
}