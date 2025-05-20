#! python3.7

import argparse
import asyncio
import io
import os
import speech_recognition as sr
import websockets
import whisper
import torch

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform

# Output file to store transcript
OUTPUT_FILE = "output_transcript.txt"
open(OUTPUT_FILE, "w").close()  # clear it at the start

CHAT_WAKE_UP_PHRASE = ["mike", "mic", "mikie", "michael", "mikee", "miky", "mik", "miky", "mikey"]
TERMINAL_WAKE_UP_PHRASE = "Hey Terminal"

async def run_audio_transcription():
    parser = argparse.ArgumentParser()
    #look here to see what model to select, small for speed medium for accuracy change default accordingly, small works better after testing
    parser.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true')
    parser.add_argument("--energy_threshold", default=1000, type=int)
    parser.add_argument("--record_timeout", default=2, type=float)
    parser.add_argument("--phrase_timeout", default=3, type=float)
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse', type=str)
    args = parser.parse_args()

    phrase_time = None
    last_sample = bytes()
    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False

    if 'linux' in platform:
        mic_name = args.default_microphone
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if mic_name in name:
                source = sr.Microphone(sample_rate=16000, device_index=index)
                break
    else:
        source = sr.Microphone(sample_rate=16000)

    model_name = args.model + ("" if args.model == "large" or args.non_english else ".en")
    print("Loading Whisper model:", model_name)
    audio_model = whisper.load_model(model_name)
    print("Model loaded successfully.")

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout
    temp_file = NamedTemporaryFile().name

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()
        data_queue.put(data)

    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)

    transcription = ['']
    while True:
        try:
            now = datetime.utcnow()
            if not data_queue.empty():
                phrase_complete = False
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                phrase_time = now

                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                text = result['text'].strip()
                last_write_time = datetime.utcnow()
                if text:
                    if phrase_complete:
                        transcription.append(text)
                    else:
                        transcription[-1] = text

                    with open(OUTPUT_FILE, "a") as f:
                        f.write(text + "\n")

                    await run_audio_transcription_queue.put(text)

                sleep(0.25)
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            break

    print("\n\nTranscription:")
    for line in transcription:
        print(line)

async def websocket_handler(websocket, path):
    await websocket.send("Hello, client!")
    try:
        while True:
            try:
                data = await asyncio.wait_for(run_audio_transcription_queue.get(), timeout=1)
                await websocket.send(data)
            except asyncio.TimeoutError:
                continue
    except websockets.exceptions.ConnectionClosed:
        pass

async def run_websockets_server():
    async with websockets.serve(websocket_handler, 'localhost', 8766):
        print("WebSocket server running at ws://localhost:8766")
        await asyncio.Future()

async def main():
    global run_audio_transcription_queue
    run_audio_transcription_queue = asyncio.Queue()
    tasks = [
        asyncio.create_task(run_websockets_server()),
        asyncio.create_task(run_audio_transcription())
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
