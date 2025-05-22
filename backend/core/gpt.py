import os
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber
from fastapi import FastAPI, Body
from threading import Thread

load_dotenv()

transcript_path = "output_transcribe.txt"
transcript_buffer = ""

def read_file_to_variable(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    return file_content


root_dir = "uploads/pdf-uploads"
def iterate_folder(folder_path):
    aff_text = ""
    neg_text = ""

    for dirpath, dirnames, filenames in os.walk(folder_path):
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            if fname.lower().endswith(".pdf"):
                with pdfplumber.open(full_path) as pdf:
                    combined_text = "\n".join(
                        page.extract_text() for page in pdf.pages if page.extract_text()
                    )
                    if "aff" in fname.lower():
                        aff_text += combined_text + "\n"
                    else:
                        neg_text += combined_text + "\n"

    return aff_text, neg_text 


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
    print("transcript reading started")

@app.get("/live-read/")
def live_read():
    return {"transcript": transcript_buffer}

@app.post("/final-speech/")
def final_speech(data: dict = Body(...)):
    global transcript_buffer
    user_side = data["side"].upper()
    base_dir = os.path.dirname(__file__)
    submission_file = os.path.abspath(os.path.join(base_dir, "../uploads/submission_uploads/submission.txt"))
    if os.path.exists(submission_file):
        with open(submission_file, "r") as f:
            user_side = f.read().strip().upper()

    folder_path = "../uploads/pdf-uploads"
    aff_text, neg_text = iterate_folder(folder_path)
    #if (file_content.upper() == "AFFIRMATIVE"):
    #    bill_text = aff_text
    #else:
    #    bill_text = neg_text

    bill_text = aff_text if user_side == "AFFIRMATIVE" else neg_text

    gpt_side = "NEGATIVE" if user_side == "AFFIRMATIVE" else "AFFIRMATIVE"
    #print(aff_text)

    bill_path = os.path.abspath(os.path.join(base_dir, "../uploads/pdf-uploads/"))

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system_prompt = (
        f"You are a skilled TFA Congressional debater assigned to argue the {gpt_side} side. "
        "Structure your response with Contention, Warrant, and Impact. "
        "Use formal tone and parliamentary style. If you are speaking second, you may rebut the user's previous points. "
        "Affirmative always speaks first, Negation second."
    )

    user_prompt = f"""
You are delivering a 3-minute congressional rebuttal speech on the {gpt_side} side.

Here is the full bill text (for context):
------------------
{bill_text.strip()}
------------------

Here is the full transcript of the opponent's speech:
------------------
{transcript_buffer.strip()}
------------------

Your task:
- DIRECTLY REBUT the opponent's speech by referencing their key arguments.
- Mention or paraphrase specific claims the opponent made.
- Break your speech into clear sections using **Contention**, **Warrant**, and **Impact**.
- Argue from the {gpt_side} side ONLY.
- Sound persuasive, formal, and parliamentary.

Please begin your full 3-minute rebuttal speech now.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.6,
        max_tokens=2048
    )

    reply = response.choices[0].message.content
    print(reply);

    # Print the output
