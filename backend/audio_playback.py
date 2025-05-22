import asyncio
import edge_tts
import os

async def speak():
    with open("gpt_response.txt", "r") as f:
        text = f.read()

    communicate = edge_tts.Communicate(
    text=text,
    voice="en-US-AriaNeural",
    rate="+40%"  
)
    await communicate.save("gpt_speech.mp3")

    # Play it using macOS's built-in audio player
    os.system("afplay gpt_speech.mp3")

asyncio.run(speak())
