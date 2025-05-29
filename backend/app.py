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


from fastapi import WebSocket
import asyncio


from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv


import uuid
from fastapi import HTTPException


from fastapi.responses import JSONResponse


from bson import ObjectId
from fastapi import BackgroundTasks


from pathlib import Path


import traceback
from starlette.websockets import WebSocketState












import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.playback import play
import io


from fastapi.websockets import WebSocketDisconnect
import simpleaudio as sa


from core.transcription import transcribe_audio_chunk



from fastapi import APIRouter






process = None


app = FastAPI()
router = APIRouter()
client = OpenAI()
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


#mongo db logic-------------------------
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["debatebot"]
conversations = db["conversations"]


#cross ref logic
with open("gpt_response.txt", "r") as f:
   context = f.read().strip()


def reload_backend():
   Path(__file__).touch()


crossref_process = None

@app.post("/start-crossref/")
def start_crossref():
    global crossref_process
    if crossref_process is None:
        crossref_process = subprocess.Popen(["python", "/Users/saahi/Desktop/debate-bot/backend/crossref.py"])
        return {"status": "CrossRef started"}
    return {"status": "CrossRef already running"}


@app.get("/get-crossref-result/")
def get_crossref_result():
    input_path = Path("/Users/saahi/Desktop/debate-bot/backend/cross_ref_input.txt")
    output_path = Path("/Users/saahi/Desktop/debate-bot/backend/crossref_response.txt")

    if not input_path.exists() or not output_path.exists():
        return {"question": "", "answer": "", "ready": False}

    input_text = input_path.read_text().strip()
    output_text = output_path.read_text().strip()

    if input_text and output_text:
        return {"question": input_text, "answer": output_text, "ready": True}

    return {"question": "", "answer": "", "ready": False}





@app.post("/stop-crossref/")
def stop_crossref():
    global crossref_process
    if crossref_process is not None:
        crossref_process.terminate()
        crossref_process = None
        return {"status": "CrossRef stopped"}
    return {"status": "CrossRef not running"}


@app.post("/new-conversation/")
def new_conversation():
   count = conversations.count_documents({})
   convo = {
       "_id": str(uuid.uuid4()),
       "title": f"Convo {count + 1}",
       "transcript": "",
       "response": ""
   }
   conversations.insert_one(convo)
   return {"conversation_id": convo["_id"], "title": convo["title"]}




@app.post("/save-transcript/{convo_id}")
def save_transcript(convo_id: str, data: dict = Body(...)):
   conversations.update_one({"_id": convo_id}, {"$set": {"transcript": data["transcript"]}})
   return {"status": "transcript updated"}


@app.post("/save-response/{convo_id}")
def save_response(convo_id: str, data: dict = Body(...)):
   conversations.update_one({"_id": convo_id}, {"$set": {"response": data["response"]}})
   return {"status": "response saved"}




@app.get("/conversations/")
def get_all_conversations():
   convos = conversations.find({}, {"_id": 1, "title": 1})
   return {"conversations": [{"id": str(c["_id"]), "title": c.get("title", "Untitled") } for c in convos]}




@app.get("/conversation/{convo_id}")
def get_conversation(convo_id: str):
   convo = conversations.find_one({"_id": convo_id})
   if not convo:
       return {"error": "Conversation not found"}
  
   transcript = convo.get("transcript", "")
   if not transcript:
       transcript = transcript_buffer  # fallback


   return {
       "transcript": transcript,
       "response": convo.get("response", ""),
       "hasStarted": convo.get("hasStarted", False)
   }




@app.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
   try:
       result = conversations.delete_one({"_id": conversation_id})
       if result.deleted_count == 0:
           return JSONResponse(status_code=404, content={"error": "Conversation not found"})
       return {"message": "Conversation deleted"}
   except Exception as e:
       return JSONResponse(status_code=500, content={"error": str(e)})
#mongo db logic-------------------------






#tts logic -----------------------------
tts_process = None


tts_task = None
play_obj = None  # 👈 ADD THIS


@app.post("/start-tts/")
async def start_tts():
   global tts_task, play_obj


   with open("gpt_response.txt", "r") as f:
       text = f.read().strip()


   communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+90%")


   async def run_tts():
       global play_obj
       audio_stream = b""
       async for chunk in communicate.stream():
           if chunk["type"] == "audio":
               audio_stream += chunk["data"]


       audio = AudioSegment.from_file(io.BytesIO(audio_stream), format="mp3")
      
       # play and store reference so it can be stopped
       play_obj = sa.play_buffer(
           audio.raw_data,
           num_channels=audio.channels,
           bytes_per_sample=audio.sample_width,
           sample_rate=audio.frame_rate,
       )


       # block in background thread so it doesn't block FastAPI
       await asyncio.get_event_loop().run_in_executor(None, play_obj.wait_done)


   tts_task = asyncio.create_task(run_tts())
  


   return {"status": "started"}


@app.post("/stop-tts/")
async def stop_tts():
   global tts_task, play_obj


   if play_obj:
       play_obj.stop()
       play_obj = None  # Optional: Clear it out


   if tts_task and not tts_task.done():
       tts_task.cancel()
       tts_task = None
  
   reload_backend()


   return {"status": "stopped"}




@app.post("/speak-instruction/")
async def speak_instruction(data: dict = Body(...)):
   text = data.get("text", "")
   if not text:
       return {"error": "No text provided"}



   communicate = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="+15%")
   audio_stream = b""
   async for chunk in communicate.stream():
       if chunk["type"] == "audio":
           audio_stream += chunk["data"]


   audio = AudioSegment.from_file(io.BytesIO(audio_stream), format="mp3")
   play_obj = sa.play_buffer(
       audio.raw_data,
       num_channels=audio.channels,
       bytes_per_sample=audio.sample_width,
       sample_rate=audio.frame_rate,
   )
   play_obj.wait_done()
  
   return {"status": "played"}




#tts logic -----------------------------








class Choice(BaseModel):
   choice: str






@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
   await websocket.accept()
   print("✅ WebSocket accepted")


   try:
       while True:
           try:
               data = await asyncio.wait_for(run_audio_transcription_queue.get(), timeout=2)
               await websocket.send_text(data)
           except asyncio.TimeoutError:
               await websocket.send_text("🔁 Still waiting...")


               # 🔒 Optional safety check:
               if process is None:  # transcription process not running
                   print("🛑 Transcription ended, closing WebSocket.")
                   await websocket.close()
                   break
   except WebSocketDisconnect:
       print("❌ Client disconnected WebSocket.")
   except Exception as e:
       print("❌ WebSocket error:", e)
  


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


@app.post("/run-vectorize/{convo_id}")
def run_vectorize(convo_id: str):
   try:
       result = subprocess.run(
           ["python", "/Users/saahi/Desktop/debate-bot/backend/vectorize.py"],
           capture_output=True,
           text=True
       )
       if result.returncode != 0:
           raise Exception(result.stderr)


       # Save state that it's been processed
       conversations.update_one({"_id": convo_id}, {"$set": {"hasStarted": True}})
      
       return {"message": "Vectorization complete", "output": result.stdout}
   except Exception as e:
       return {"error": str(e)}


@app.post("/reload-backend/")
def reload_backend_route():
   try:
       reload_backend()  # wherever this is defined
       return {"message": "Backend reloaded successfully"}
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
   print("🔗 URLs used for research:")
   for url in urls:
       print("   -", url)
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
   model_speech = "In 1961, a civil rights group known as CORE founded the Freedom Riders. In one of the era's final acts of protests, they traveled the South by bus in order to defy segregation. Upon arriving in Jackson, Mississippi, they encountered brutality, indignation, and imprisonment. In an attempt to hold their officers accountable, they saw judicial relief through the KKK act. And in response, this government birthed qualified immunity. That takes us to today. As America, a chance, say their name, seeking the same relief that the Freedom Riders fought for, all we've met them with is silence. Principally, pass this legislation to reform police training in America. The National Conference of State Legislators writes on August 22, 2022, that only 11 states require police to learn the various forms of de-escalation training, meaning in the other 39 states, there are no accountability methods to ensure that the right techniques are taught. Yet in half of the 8,514 federal police shootings, the subject of a rest never possessed a fire arm. Unarmed in half of shootings. We need accountability, and today's legislation delivers that. Senator Stevenson, Senator Wilkins, you tell us it does nothing. This removes illegal protection, meaning there's more accountability. As the Institute of Justice found on January 23, 2022, the removal of qualified immunity would raise liability to the point where departments would be forced to embrace de-escalation techniques. That's why the Washington Post wrote in June 23, 2021, that when the NYPD lost their qualified immunity, it only took them two months to establish de-escalation techniques. The only question left in this debate is does this training work? Yes, it does. First, it holds officers and protects them. As the American Psychological Association writes on October 1, 2020, the training I mentioned earlier in Las Vegas reduced officer injuries by 11%, as the DOJ found in September 6, 2022, and Louisville, it reduced officer injuries by 36%. The best of us choose to serve and protect us. Today, let the best of us serve and protect them. Secondly, it protects the community. That same APA report found that the de-escalation training led to safer community interactions. In Las Vegas, the use of force dropped by 23% in Louisville, by 26%, and in Seattle, by 40%, behind every statistic is a story. Don't let anyone's be cut short. Say their name by passing. We can finally require every department and this government to acknowledge them with action or go with Senator Stevens' plan, strike down this legislation and give them the same response that we've issued for generations. That silence."
   user_prompt = (
       f"Bill:\n{bill_text_raw.strip()}\n\n"
       f"Opponent Speech:\n{transcript_buffer.strip()}\n\n"
       "Below is an example of a high-quality Congressional debate speech. It uses strong rhetoric, historical framing, impact weighing, and structured clash (Contention, Warrant, Impact)."
       " Model your style, tone, and argumentative structure after it:\n\n"
       f"{model_speech}\n\n"
       f"Research:\n{research_context}\n\n"
       "Directly rebut at least two key points. Provide an 800-word 3-minute speech. Focus on clash and weighing."
       "After you make a general argument such as, The notion that these proxy groups are so weakened that they pose no threat is dangerously optimistic and naïve, you have to explain WHY and HOW"
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



