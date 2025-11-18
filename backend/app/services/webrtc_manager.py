from aiortc import RTCPeerConnection

class WebRTCManager:
    def __init__(self):
        self.pc = RTCPeerConnection()

    async def create_answer(self, offer_sdp):
        offer = RTCSessionDescription(sdp=offer_sdp["sdp"], type="offer")
        await self.pc.setRemoteDescription(offer)

        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        return {
            "sdp": self.pc.localDescription.sdp,
            "type": self.pc.localDescription.type
        }

webrtc_manager = WebRTCManager()
