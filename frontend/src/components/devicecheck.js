// frontend/src/components/devicecheck.js (UPDATED for better error handling)
import React, { useEffect, useState } from 'react';
import { getLocalMedia } from '../webrtc'; // Assuming you accept the new version needs to import this

export default function DeviceCheck({ onReady }){
    const [devices, setDevices] = useState([]);
    const [error, setError] = useState(null);

    useEffect(()=>{
        async function fetchDevices(){
            let hasAudio = false;
            let hasVideo = false;
            
            try{
                // 1. Try to get the stream directly to check permissions
                const { success, stream, error: mediaError } = await getLocalMedia({ audio: true, video: true });
                
                if (success) {
                    hasAudio = stream.getAudioTracks().length > 0;
                    hasVideo = stream.getVideoTracks().length > 0;
                    
                    // Crucial: Stop tracks immediately after checking to free the mic/camera
                    stream.getTracks().forEach(track => track.stop());
                    
                    // 2. Enumerate devices now that permissions are granted (labels are now available)
                    const list = await navigator.mediaDevices.enumerateDevices();
                    setDevices(list);
                    
                } else {
                    // Log the specific error object received from getLocalMedia
                    setError(mediaError.name || mediaError.message || String(mediaError));
                    console.error("DeviceCheck Failed:", mediaError);
                }
                
                // Update the readiness status
                onReady && onReady({ audio: hasAudio, video: hasVideo });

            }catch(err){
                // Catch any unexpected enumeration errors
                setError(err.message || String(err));
                onReady && onReady({ audio: false, video: false });
            }
        }
        fetchDevices();
    }, [onReady]);

    return (
        <div className="card">
            <h3>Device Check</h3>
            {error && <p style={{color:'red', fontWeight: 'bold'}}>Error: {error}</p>}
            
            {/* Show a clear message based on error type */}
            {error && error.includes('Permission') && (
                <p>⚠️ **Action Required:** Check the lock icon in your browser's address bar and ensure microphone access is set to 'Allow'.</p>
            )}

            <ul>
                {devices.map(d => (
                    <li key={d.deviceId}>{d.kind} — **{d.label || 'label hidden (Permission Needed)'}** </li>
                ))}
            </ul>
        </div>
    );
}