import React, { useEffect, useState } from 'react';


export default function DeviceCheck({ onReady }){
const [devices, setDevices] = useState([]);
const [error, setError] = useState(null);


useEffect(()=>{
async function fetchDevices(){
try{
// Ensure permissions requested first for labels to appear
await navigator.mediaDevices.getUserMedia({ audio: true, video: true }).catch(()=>{});
const list = await navigator.mediaDevices.enumerateDevices();
setDevices(list);
const hasAudio = list.some(d => d.kind === 'audioinput');
const hasVideo = list.some(d => d.kind === 'videoinput');
onReady && onReady({ audio: hasAudio, video: hasVideo });
}catch(err){
setError(err.message || String(err));
}
}
fetchDevices();
}, [onReady]);


return (
<div className="card">
<h3>Device check</h3>
{error && <p style={{color:'red'}}>Error: {error}</p>}
<ul>
{devices.map(d => (
<li key={d.deviceId}>{d.kind} — {d.label || 'label hidden'} </li>
))}
</ul>
</div>
);
}