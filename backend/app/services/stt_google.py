from google.cloud import speech

class GoogleSTT:
    def __init__(self):
        self.client = speech.SpeechClient()

    def transcribe(self, audio_bytes):
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US"
        )
        response = self.client.recognize(config=config, audio=audio)
        return response

google_stt = GoogleSTT()
