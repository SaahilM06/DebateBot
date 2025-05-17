import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
from typing import List 
from pathlib import Path
from transcribe import transcribe_audio
import subprocess

process = None

UPLOAD_DIR = Path("uploads/audio-uploads")
UPLOAD_DIR1 = Path("uploads/submission_uploads")
UPLOAD_DIR2 = Path("uploads/pdf-uploads")

app = FastAPI()

origins = [
    "http://localhost:3000"
]

class Choice(BaseModel): 
    choice: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/start-transcription/')
def start_transcription():
    global process
    if process is None:
        process = subprocess.Popen(["python", "/Users/saahi/Desktop/debate-bot/backend/record_and_transcribe.py"])
        return {"status": "started"}
    else:
        return {"status": "already running"}

@app.post("/stop-transcription/")
def stop_transcription():
    global process
    if process is not None:
        process.terminate()
        process = None
        return {"status": "stopped"}
    else:
        return {"status": "not running"}

@app.post('/uploadfile/')
async def create_upload_file(file_upload: UploadFile):
    data = await file_upload.read()
    save_to = UPLOAD_DIR / file_upload.filename
    with open(save_to, 'wb') as f:
        f.write(data)
    transcript = transcribe_audio(str(save_to))
    with open("output_transcribe.txt", 'w') as f:
        f.write(transcript + "\n")
    return {
        "filenames": file_upload.filename,
        "transcript": transcript
    }

@app.post('/submit-choice/')
async def submit_choice(data: Choice):
    UPLOAD_DIR1.mkdir(parents=True, exist_ok=True) 
    save_to = UPLOAD_DIR1 / "submission.txt"
    with open(save_to, 'w') as f:
        f.write(data.choice)
    return {"message": f"Choice '{data.choice}' submitted successfully."}

@app.post('/file-choice/')
async def create_upload_file(file_upload: UploadFile):
    data = await file_upload.read()
    save_to = UPLOAD_DIR2 / file_upload.filename
    with open(save_to, 'wb') as f:
        f.write(data)
    return {
        "filenames": file_upload.filename,
    }

@app.post("/run-vectorize/")
def run_vectorize():
    try:
        result = subprocess.run(
            ["python", "/Users/saahi/Desktop/debate-bot/backend/vectorize.py"],
            capture_output=True,
            text=True
        )
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        if result.returncode != 0:
            raise Exception(result.stderr)
        return {"message": "Vectorization complete", "output": result.stdout}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
