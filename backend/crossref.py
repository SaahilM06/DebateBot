import os
import time
import openai
import speech_recognition as sr
from openai import OpenAI
import asyncio
import edge_tts
from pydub import AudioSegment
import io
from pathlib import Path
import subprocess

client = OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load debate context
with open("gpt_response.txt", "r") as f:
    context = f.read().strip()

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.5
recognizer.energy_threshold = 300
mic = sr.Microphone()

output_path = Path("/Users/saahi/Desktop/debate-bot/backend/crossref_response.txt")
input_path = Path("/Users/saahi/Desktop/debate-bot/backend/cross_ref_input.txt")  # ✅ NEW

# 🔊 Safe TTS playback using afplay
async def speak_file(path: Path):
    if not path.exists():
        print("❌ TTS error: File not found.")
        return

    with open(path, "r") as f:
        text = f.read().strip()

    communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+40%")
    audio_stream = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream += chunk["data"]

    audio = AudioSegment.from_file(io.BytesIO(audio_stream), format="mp3")
    wav_path = Path("temp_response.wav")
    audio.export(wav_path, format="wav")

    subprocess.run(["afplay", str(wav_path)])
    wav_path.unlink(missing_ok=True)

print("🎤 Cross-Ex mode initialized for 60 seconds.")
print("Press Ctrl+C to exit manually.\n")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

start_time = time.time()

while True:
    if time.time() - start_time >= 60:
        print("⏱️ 60 seconds reached. Ending Cross-Ex.")
        break

    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🟢 Listening...")
            audio = recognizer.listen(source, timeout=10)

        if time.time() - start_time >= 60:
            print("⏱️ 60 seconds reached after listening. Ending.")
            break

        print("🧠 Transcribing...")
        try:
            query = recognizer.recognize_whisper(audio)
        except sr.UnknownValueError:
            print("❓ Could not understand audio.")
            continue
        except sr.WaitTimeoutError:
            print("⌛ Timed out.")
            continue

        print(f"🗣 You said: {query}")

        # ✅ Save user input
        input_path.write_text(query)

        messages = [
            {
                "role": "system",
                "content": f"You are an expert Congressional debater. Reference this prior speech for context: \"{context}\". Keep responses concise, 50-60 words, and relevant.",
            },
            {"role": "user", "content": query},
        ]

        print("🤖 GPT thinking...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        answer = response.choices[0].message.content.strip()

        # 💾 Save response
        output_path.write_text(answer)
        print(f"📁 Saved GPT response to {output_path}")

        if time.time() - start_time >= 60:
            print("⏱️ 60 seconds reached before TTS. Skipping playback.")
            break

        # 🔊 Speak the response
        loop.run_until_complete(speak_file(output_path))

    except KeyboardInterrupt:
        print("\n👋 Exiting manually.")
        break
    except Exception as e:
        print(f"⚠️ Error: {e}")
