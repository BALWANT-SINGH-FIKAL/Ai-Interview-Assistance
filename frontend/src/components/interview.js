import React, { useRef, useEffect, useState } from 'react';
import { getLocalMedia, createLocalPeer } from '../webrtc';


export default function Interview(){
const localVideoRef = useRef(null);
const [status, setStatus] = useState('idle');
const [stream, setStream] = useState(null);


useEffect(()=>{
return ()=>{
if(stream){
stream.getTracks().forEach(t=>t.stop());
}
}
}, [stream]);


async function start(){
setStatus('requesting');
const res = await getLocalMedia({ audio: true, video: true });
if(!res.success){ setStatus('error'); return; }
setStream(res.stream);
if(localVideoRef.current){ localVideoRef.current.srcObject = res.stream; }
setStatus('ready');


// Example: create peer and add tracks (signaling not included)
const pc = createLocalPeer();
res.stream.getTracks().forEach(track => pc.addTrack(track, res.stream));
// TODO: create offer -> send to backend signal server (Phase 3)
}


return (
<div className="card">
<h3>Interview</h3>
<p>Status: {status}</p>
<div>
<video ref={localVideoRef} autoPlay playsInline muted className="video-box" />
</div>
<div style={{marginTop:12}}>
<button onClick={start}>Start local media</button>
</div>
</div>
);
}