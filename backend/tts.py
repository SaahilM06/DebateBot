import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.playback import play
import io

async def speak_file():
    # Load text
    with open("gpt_response.txt", "r") as f:
        text = f.read().strip()

    # Create TTS stream
    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+30%")

    # Collect audio stream into buffer
    audio_stream = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream += chunk["data"]

    # Play the audio using pydub
    audio = AudioSegment.from_file(io.BytesIO(audio_stream), format="mp3")
    play(audio)

asyncio.run(speak_file())
