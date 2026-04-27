// frontend/src/components/audiostreamer.js
import { interviewSocket } from '../ws/interviewsocket';

class AudioStreamer {
    constructor(stream) {
        if (!stream) {
            throw new Error("MediaStream must be provided to AudioStreamer.");
        }
        
        this.stream = stream;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        // Removed hardcoded mimeType from constructor
        this.isRecording = false;
        
        this.onStopCallback = null; 
    }
    
    /**
     * Finds the most supported audio MIME type by the browser.
     * @returns {string} The supported MIME type.
     */
    _getSupportedMimeType() {
        const preferredTypes = ['audio/webm', 'audio/ogg', 'audio/mp4'];
        
        for (const type of preferredTypes) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        // Fallback to the original default if none of the preferred are found
        return 'audio/webm';
    }


    /**
     * Prepares and starts the MediaRecorder.
     */
    startRecording() {
        if (this.isRecording) {
            console.warn("Recording already in progress.");
            return;
        }

        try {
            const supportedMimeType = this._getSupportedMimeType();
            const options = { mimeType: supportedMimeType }; 
            
            // --- CRITICAL FIX: Isolate the Audio Track ---
            // 1. Get the current audio track from the stream.
            const audioTrack = this.stream.getAudioTracks()[0];
            
            if (!audioTrack) {
                 throw new Error("No audio track found in media stream.");
            }
            
            // 2. Create a new stream containing ONLY the audio track.
            const cleanAudioStream = new MediaStream([audioTrack]);
            
            // 3. Initialize MediaRecorder with the clean audio stream.
            this.mediaRecorder = new MediaRecorder(cleanAudioStream, options);
            // ----------------------------------------------------
            
            this.recordedChunks = [];
            const currentMimeType = supportedMimeType; 

            // 1. Data available event: collect audio chunks
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };

            // 2. Stop event: finalize the blob and send it
            this.mediaRecorder.onstop = () => {
                this._sendRecordedBlob(currentMimeType);
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            console.log("Audio recording started with MIME type:", supportedMimeType);
            
        } catch (error) {
            console.error("Failed to start MediaRecorder:", error);
            this.isRecording = false;
            // Provide better feedback to the user
            alert(`Recording Failed: ${error.name}. Please check your browser's audio settings.`);
        }
    }

    /**
     * Stops the MediaRecorder and triggers the sending process.
     */
    stopRecording() {
        if (this.isRecording && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            this.isRecording = false;
            console.log("Audio recording stopped. Preparing to send data.");
        }
    }

    /**
     * Combines chunks into a single Blob and sends it via WebSocket.
     */
    _sendRecordedBlob(mimeType) {
        if (this.recordedChunks.length === 0) {
            console.warn("No audio data recorded to send.");
            return;
        }
        
        // FIX: Use the MIME type determined during startRecording
        const audioBlob = new Blob(this.recordedChunks, { type: mimeType }); 
        console.log(`Sending audio blob of size: ${audioBlob.size} bytes`);
        
        // WebSocket send for binary data
        if (interviewSocket.ws && interviewSocket.ws.readyState === WebSocket.OPEN) {
            interviewSocket.ws.send(audioBlob); 
        } else {
            console.error("WebSocket is not open. Cannot send audio.");
        }

        // Clean up
        this.recordedChunks = [];
        
        if (this.onStopCallback) {
            this.onStopCallback(audioBlob);
        }
    }
    
    /**
     * Allows the parent component (interview.js) to listen for the stop event.
     */
    onRecordingStopped(callback) {
        this.onStopCallback = callback;
    }

    get state() {
        return this.mediaRecorder ? this.mediaRecorder.state : 'inactive';
    }
}

export default AudioStreamer;