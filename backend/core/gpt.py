import os
from openai import OpenAI
from dotenv import load_dotenv
import pdfplumber

load_dotenv()
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

            

base_dir = os.path.dirname(__file__)
file_path = os.path.abspath(os.path.join(base_dir, "../uploads/submission_uploads/submission.txt"))
file_content = read_file_to_variable(file_path)

folder_path = "../uploads/pdf-uploads"
aff_text, neg_text = iterate_folder(folder_path)
if (file_content.upper() == "AFFIRMATIVE"):
    text = aff_text
else:
    text = neg_text

print(aff_text)

bill_path = os.path.abspath(os.path.join(base_dir, "../uploads/pdf-uploads/"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
system_prompt = (
    f"You are a skilled TFA Congressional debater assigned to argue the {file_content} side. "
    "Structure your response with Contention, Warrant, and Impact. "
    "Use formal tone and parliamentary style. If you are speaking second, you may rebut the user's previous points. "
    "Affirmative always speaks first, Negation second."
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"The bill text is:\n\n{text.strip()}\n\nPlease present your speech."}
    ],
    temperature=0.6,
    max_tokens=2048
)

# Print the output
print(response.choices[0].message.content)
