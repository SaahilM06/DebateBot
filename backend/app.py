import uvicorn
from fastapi import FastAPI, UploadFile, Body, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
from typing import List 
from pathlib import Path
import subprocess
import time
import socket
import os
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber
from threading import Thread
from fastapi.responses import StreamingResponse
from io import StringIO
from search_and_scrape import scrape_text_from_url
import pytesseract
from PIL import Image, ImageOps
import requests

process = None

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads/audio-uploads")
UPLOAD_DIR1 = Path("uploads/submission_uploads")
UPLOAD_DIR2 = Path("uploads/pdf-uploads")
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR3 = BASE_DIR / "uploads" / "bill_uploads"
UPLOAD_DIR3.mkdir(parents=True, exist_ok=True)

class Choice(BaseModel): 
    choice: str

# ✅ Transcription Start/Stop (WebSocket-based)
@app.post("/start-transcription/")
def start_transcription():
    global process
    if process is None:
        process = subprocess.Popen(["python", "/Users/saahi/Desktop/debate-bot/backend/record_and_transcribe.py"])
        while True:
            try:
                with socket.create_connection(("localhost", 8766), timeout=1):
                    break
            except OSError:
                time.sleep(0.5)
        return {"status": "started"}
    return {"status": "already running"}

@app.post("/stop-transcription/")
def stop_transcription():
    global process
    if process is not None:
        process.terminate()
        process = None
        return {"status": "stopped"}
    return {"status": "not running"}

# ✅ File Uploads
@app.post("/uploadfile/")
async def create_upload_file(file_upload: UploadFile):
    data = await file_upload.read()
    save_to = UPLOAD_DIR / file_upload.filename
    with open(save_to, 'wb') as f:
        f.write(data)
    return {"filenames": file_upload.filename}

@app.post("/submit-choice/")
async def submit_choice(data: Choice):
    UPLOAD_DIR1.mkdir(parents=True, exist_ok=True)
    save_to = UPLOAD_DIR1 / "submission.txt"
    with open(save_to, 'w') as f:
        f.write(data.choice)
    return {"message": f"Choice '{data.choice}' submitted successfully."}

@app.post("/file-choice/")
async def create_upload_file_2(file_upload: UploadFile):
    data = await file_upload.read()
    save_to = UPLOAD_DIR2 / file_upload.filename
    with open(save_to, 'wb') as f:
        f.write(data)
    return {"filenames": file_upload.filename}

@app.post("/bill-choice/")
async def create_bill_upload(file_upload: UploadFile = File(...)):
    data = await file_upload.read()
    for existing in UPLOAD_DIR3.iterdir():
        existing.unlink()
    save_to = UPLOAD_DIR3 / file_upload.filename
    with open(save_to, 'wb') as f:
        f.write(data)
    return {"message": f"Successfully uploaded: {file_upload.filename}"}

@app.post("/run-vectorize/")
def run_vectorize():
    try:
        result = subprocess.run(
            ["python", "/Users/saahi/Desktop/debate-bot/backend/vectorize.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        return {"message": "Vectorization complete", "output": result.stdout}
    except Exception as e:
        return {"error": str(e)}

# ✅ Transcript + GPT Rebuttal Logic
load_dotenv()
transcript_path = "output_transcribe.txt"
transcript_buffer = ""

def extract_text_from_file(filepath: str) -> str:
    try:
        ext = Path(filepath).suffix.lower()
        if ext == ".pdf":
            with pdfplumber.open(filepath) as pdf:
                return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        elif ext in [".png", ".jpg", ".jpeg"]:
            image = Image.open(filepath).convert("L")
            image = ImageOps.autocontrast(image)
            return pytesseract.image_to_string(image)
    except Exception as e:
        print("Extract error:", e)
    return ""

def clean_text(text: str, max_words: int = 50) -> str:
    lines = text.splitlines()
    cleaned = [line.strip() for line in lines if len(line.strip()) > 5 and any(c.isalpha() for c in line)]
    return " ".join(" ".join(cleaned).split()[:max_words])

def serper_search(query: str, api_key: str):
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query})
    if res.status_code != 200:
        print("Serper error:", res.text)
        return []
    return [r["link"] for r in res.json().get("organic", [])]

def live_transcript_reader():
    global transcript_buffer
    last_seen = ""
    while True:
        try:
            with open(transcript_path, "r") as f:
                content = f.read().strip()
                if content != last_seen:
                    transcript_buffer = content
                    last_seen = content
        except FileNotFoundError:
            transcript_buffer = ""
        time.sleep(10)

@app.on_event("startup")
def start_background_reader():
    Thread(target=live_transcript_reader, daemon=True).start()

@app.get("/live-read/")
def live_read():
    return {"transcript": transcript_buffer}

@app.post("/final-speech/")
def final_speech(data: dict = Body(...)):
    global transcript_buffer
    user_side = data["side"].upper()
    base_dir = os.path.dirname(__file__)
    submission_file = os.path.join(base_dir, "../uploads/submission_uploads/submission.txt")
    if os.path.exists(submission_file):
        with open(submission_file, "r") as f:
            user_side = f.read().strip().upper()

    bill_folder = os.path.join(base_dir, "uploads", "bill_uploads")
    bill_files = [f for f in os.listdir(bill_folder) if f.lower().endswith((".pdf", ".jpeg", ".jpg", ".png"))]
    if not bill_files:
        return {"error": "No bill file found in uploads/bill_uploads."}

    bill_path = os.path.join(bill_folder, bill_files[0])
    bill_text_raw = extract_text_from_file(bill_path)
    if not bill_text_raw:
        return {"error": "Failed to extract text from bill."}

    search_input = clean_text(bill_text_raw)
    serper_api_key = os.getenv("SERPER_API_KEY")
    urls = serper_search(search_input, serper_api_key)
    scraped_articles = []
    for url in urls[:2]:
        try:
            scraped_articles.append(scrape_text_from_url(url))
        except Exception as e:
            print(f"[ERROR] Failed to scrape {url} — {e}")
    research_context = "\n\n".join(scraped_articles)

    gpt_side = "NEGATIVE" if user_side == "AFFIRMATIVE" else "AFFIRMATIVE"

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system_prompt = (
        f"You are a top-tier TFA Congressional debater tasked with arguing the {gpt_side} side. "
        "Clash with the opponent's arguments using Contention, Warrant, and Impact. Be confident, formal, and parliamentary. "
    )

    user_prompt = (
        f"Bill:\n{bill_text_raw.strip()}\n\n"
        f"Opponent Speech:\n{transcript_buffer.strip()}\n\n"
        f"Research:\n{research_context}\n\n"
        "Directly rebut at least two key points. Provide an 800-word 3-minute speech. Focus on clash and weighing."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        stream=True
    )

    full_reply = StringIO()
    def stream_and_save():
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            full_reply.write(content)
            yield content

    streamed_output = "".join(stream_and_save())
    with open("gpt_response.txt", "w") as f:
        f.write(streamed_output)
    return {"speech": streamed_output}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
