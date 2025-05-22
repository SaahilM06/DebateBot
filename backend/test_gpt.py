import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import pytesseract
from PIL import Image, ImageOps
import pdfplumber
from bs4 import BeautifulSoup
from openai import OpenAI
from io import StringIO

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent
BILL_DIR = BASE_DIR / "uploads" / "bill_uploads"
TRANSCRIPT_PATH = BASE_DIR / "output_transcribe.txt"

# Extract text from file
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

# Clean text for search

def clean_text(text: str, max_words: int = 50) -> str:
    lines = text.splitlines()
    cleaned = [line.strip() for line in lines if len(line.strip()) > 5 and any(c.isalpha() for c in line)]
    words = " ".join(cleaned).split()
    return " ".join(words[:max_words])

# Serper Search
def serper_search(query: str, api_key: str):
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    res = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
    if res.status_code != 200:
        print("Serper error:", res.text)
        return []
    data = res.json()
    return [r["link"] for r in data.get("organic", [])]

# Scrape with fallback

def scrape_text_from_url(url: str) -> str:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        return "\n".join(p.get_text() for p in paragraphs if p.get_text().strip())
    except Exception as e:
        print(f"[ERROR] Failed to scrape {url} — {e}")
        return ""

# Final speech generation
def generate_final_speech(user_side: str):
    bill_files = list(BILL_DIR.glob("*.pdf")) + list(BILL_DIR.glob("*.png")) + list(BILL_DIR.glob("*.jpg")) + list(BILL_DIR.glob("*.jpeg"))
    if not bill_files:
        print("No bill file found.")
        return

    bill_path = bill_files[0]
    raw_text = extract_text_from_file(bill_path)
    if not raw_text:
        print("Failed to extract bill text.")
        return

    search_input = clean_text(raw_text)
    api_key = os.getenv("SERPER_API_KEY")
    urls = serper_search(search_input, api_key)
    scraped_articles = [scrape_text_from_url(url) for url in urls[:2]]
    research_context = "\n\n".join(scraped_articles)

    transcript = ""
    if TRANSCRIPT_PATH.exists():
        transcript = TRANSCRIPT_PATH.read_text().strip()

    gpt_side = "NEGATIVE" if user_side.upper() == "AFFIRMATIVE" else "AFFIRMATIVE"
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    system_prompt = (
        f"You are a skilled TFA Congressional debater assigned to argue the {gpt_side} side. "
        "Structure your response with Contention, Warrant, and Impact. "
        "Use formal tone and parliamentary style. If you are speaking second, rebut the opponent."
    )

    user_prompt = (
        f"Here is the full bill text:\n\n{raw_text.strip()}\n\n"
        f"Transcript of the opponent's speech:\n\n{transcript}\n\n"
        f"Relevant research from the web:\n\n{research_context}\n\n"
        "Directly rebut the opponent and deliver an 800-word speech."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=True
    )

    full_reply = StringIO()
    for chunk in response:
        content = chunk.choices[0].delta.content or ""
        full_reply.write(content)
        print(content, end="", flush=True)

    with open("gpt_response.txt", "w") as f:
        f.write(full_reply.getvalue())

# Run it
if __name__ == "__main__":
    generate_final_speech("Affirmative")
