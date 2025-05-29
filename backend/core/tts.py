# core/tts.py
import edge_tts
from pydub import AudioSegment
from pydub.playback import play  # ✅ Replaces simpleaudio
import io

async def async_speak(text: str):
    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+30%")
    audio_stream = b""

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream += chunk["data"]

    # Load audio from memory
    audio = AudioSegment.from_file(io.BytesIO(audio_stream), format="mp3")

    # ✅ Safe playback using pydub's internal player
    play(audio)
