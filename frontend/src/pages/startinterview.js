import React, { useState } from 'react';
import DeviceCheck from '../components/devicecheck';
import Interview from '../components/interview';


export default function StartInterview(){
const [ready, setReady] = useState({ audio:false, video:false });
return (
<div className="container">
<div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
<DeviceCheck onReady={setReady} />
<div className="card">
<h3>Start</h3>
<p>Audio: {ready.audio ? 'OK' : 'Missing'}</p>
<p>Video: {ready.video ? 'OK' : 'Missing'}</p>
<Interview />
</div>
</div>
</div>
);
}