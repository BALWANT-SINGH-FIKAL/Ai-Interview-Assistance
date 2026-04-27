// frontend/src/pages/startinterview.js (UPDATED)
import React, { useState } from 'react';
import DeviceCheck from '../components/devicecheck';
import Interview from './interview'; // Changed to use relative path for pages

export default function StartInterview(){
    // Track the readiness of both audio and video
    const [ready, setReady] = useState({ audio: false, video: false });

    // Condition to proceed: We need AT LEAST audio to run the voice interview.
    const isReady = ready.audio; 

    return (
        <div className="container">
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
                
                {/* 1. Device Check Component */}
                <DeviceCheck onReady={setReady} />

                {/* 2. Status & Start Area */}
                <div className="card">
                    <h3>Interview Status</h3>
                    <p>Audio Status: {ready.audio ? '✅ Ready' : '❌ Missing'}</p>
                    <p>Video Status: {ready.video ? '✅ Ready' : '❌ Missing'}</p>
                    
                    {!isReady && (
                        <p style={{color: 'red', fontWeight: 'bold'}}>
                            Please grant microphone access to start the interview.
                        </p>
                    )}
                    
                    {/* Render the Interview component only if audio is ready */}
                    {isReady && (
                        <div style={{marginTop: 20}}>
                            <p style={{color: 'green', fontWeight: 'bold'}}>Devices ready. Starting Interview...</p>
                            {/* The Interview component will handle the WS connection and audio stream setup */}
                            <Interview /> 
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}