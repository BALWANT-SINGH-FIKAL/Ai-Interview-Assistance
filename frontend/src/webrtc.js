// Simple WebRTC helper for Phase 2 — handles local getUserMedia and returns a MediaStream


export async function getLocalMedia({ audio = true, video = true } = {}){
try{
const constraints = { audio, video };
const stream = await navigator.mediaDevices.getUserMedia(constraints);
return { success: true, stream };
}catch(err){
return { success: false, error: err };
}
}


// Placeholder: create RTCPeerConnection and local tracks; actual signaling/WS is Phase 3
export function createLocalPeer(){
const config = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
const pc = new RTCPeerConnection(config);
pc.oniceconnectionstatechange = () => console.log('ICE', pc.iceConnectionState);
return pc;
}