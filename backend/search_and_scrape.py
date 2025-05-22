import pytesseract
from PIL import Image
import pdfplumber
import requests
from newspaper import Article

def extract_text_from_file(file_path):
    if file_path.lower().endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return pdf.pages[0].extract_text().split('\n')[0].strip()
    elif file_path.lower().endswith((".jpeg", ".jpg", ".png")):
        img = Image.open(file_path)
        return pytesseract.image_to_string(img).split('\n')[0].strip()
    return ""

def brave_search(query: str, api_key: str):
    try:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        params = {"q": query}
        res = requests.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)

        print("🔁 Brave API status:", res.status_code)
        if res.status_code != 200:
            print("❌ Brave error:", res.text)
            return []

        data = res.json()
        return [r["url"] for r in data.get("results", [])]
    except Exception as e:
        print("🔥 Brave request failed:", e)
        return []

def scrape_text_from_url(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text
