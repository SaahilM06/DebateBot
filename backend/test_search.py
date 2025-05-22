import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import pytesseract
from PIL import Image, ImageOps
import pdfplumber
from search_and_scrape import scrape_text_from_url

# Load env
load_dotenv()
serper_api_key = os.getenv("SERPER_API_KEY")

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
    results = data.get("organic", [])
    return [r["link"] for r in results]

# Extract text
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
        else:
            print("Unsupported file")
    except Exception as e:
        print("Extract error:", e)
    return ""

# Clean text
def clean_text(text: str, max_words: int = 50) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if len(line) > 5 and any(c.isalpha() for c in line):
            cleaned.append(line)
    joined = " ".join(cleaned)
    words = joined.split()
    return " ".join(words[:max_words])

# Locate bill
base_dir = os.path.dirname(__file__)
bill_folder = os.path.join(base_dir, "uploads", "bill_uploads")

if not os.path.exists(bill_folder):
    print("Missing folder:", bill_folder)
    exit(1)

bill_files = [f for f in os.listdir(bill_folder) if f.lower().endswith((".pdf", ".jpeg", ".jpg", ".png"))]
if not bill_files:
    print("No file in bill_uploads.")
    exit(1)

bill_path = os.path.join(bill_folder, bill_files[0])
print("Found bill:", bill_files[0])

# Extract + clean
raw_text = extract_text_from_file(bill_path)
if not raw_text:
    print("No text extracted.")
    exit(1)

search_input = clean_text(raw_text)
print("Cleaned query:", repr(search_input))

# Search
results = serper_search(search_input, serper_api_key)
if not results:
    print("No results from Serper.")
    exit(1)

print("Top results:", results[:2])

# Scrape
scraped = [scrape_text_from_url(url) for url in results[:2]]
for i, article in enumerate(scraped):
    print(f"\n--- Article {i+1} ---\n{article[:1000]}...\n")
