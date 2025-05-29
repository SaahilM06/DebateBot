import re
from nltk.tokenize import sent_tokenize
from nltk import download
from difflib import SequenceMatcher
from collections import Counter

download("punkt")

def is_similar(a: str, b: str, threshold=0.9) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold

def detect_repetitive_prefixes(sentences, min_occurrences=4, prefix_length=6):
    """
    Detect prefixes that appear too often (e.g., first 6 words occurring 4+ times)
    """
    prefixes = [ ' '.join(s.split()[:prefix_length]).lower() for s in sentences if len(s.split()) >= prefix_length ]
    common = [p for p, count in Counter(prefixes).items() if count >= min_occurrences]
    return common

def clean_junky_text(text: str, similarity_threshold=0.9) -> str:
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Split into sentences
    sentences = sent_tokenize(text)

    # Detect and remove common noise prefixes
    noisy_prefixes = detect_repetitive_prefixes(sentences)

    filtered_sentences = []
    seen = []

    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue

        # Remove if starts with noisy prefix
        lowered = s_clean.lower()
        if any(lowered.startswith(p) for p in noisy_prefixes):
            continue

        # Fuzzy deduplication
        if not any(is_similar(s_clean, existing, similarity_threshold) for existing in seen):
            seen.append(s_clean)
            filtered_sentences.append(s_clean)

    return ' '.join(filtered_sentences)

if __name__ == "__main__":
    input_path = "output_transcribe.txt"
    output_path = "cleaned_summary.txt"

    with open(input_path, "r") as f:
        raw = f.read()

    cleaned_summary = clean_junky_text(raw)

    with open(output_path, "w") as f:
        f.write(cleaned_summary)

    print(f"✅ Cleaned text saved to '{output_path}'")
