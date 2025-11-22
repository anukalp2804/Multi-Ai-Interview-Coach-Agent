# stt_agent.py
# In our architecture, STT runs in the browser. This agent provides utilities and fallback.
class STTAgent:
    def __init__(self):
        pass

    def transcribe_audio_blob(self, blob_bytes: bytes) -> str:
        # In mock mode we do no audio processing.
        return "<transcribed-text-placeholder>"

    # Browser handles speech recognition via Web Speech API; this class is placeholder for future server-side STT.
