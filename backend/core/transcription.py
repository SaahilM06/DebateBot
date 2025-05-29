import io
import whisper
import numpy as np
import soundfile as sf

# Load the model once
model = whisper.load_model("base")

def transcribe_audio_chunk(audio_bytes: bytes) -> str:
    try:
        # Convert raw bytes to numpy array
        audio_np, samplerate = sf.read(io.BytesIO(audio_bytes))
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)  # Convert to mono

        # Run Whisper model
        result = model.transcribe(audio_np, fp16=False, language="en", verbose=False)
        return result.get("text", "").strip()
    except Exception as e:
        print("❌ Transcription error:", e)
        return ""
