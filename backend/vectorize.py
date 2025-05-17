import chromadb
import pdfplumber
import os
import sys
from chromadb.errors import UniqueConstraintError
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions
from chromadb.config import Settings 
import nltk
from nltk.tokenize import sent_tokenize
print("Current working dir:", os.getcwd())


with open("output.txt", "w") as file:
    pass  
nltk.download('punkt_tab')



chroma_client = chromadb.PersistentClient(path="database/chroma_db")

collection_name = "collection2"
try:
    chroma_client.delete_collection(name=collection_name)
except:
    pass  

collection = chroma_client.create_collection(name=collection_name)
#this should be the same as the Mini sentence transformers model thing
model = SentenceTransformer("all-MiniLM-L6-v2")



# print("Working directory:", os.getcwd())
# print("Dir listing here:", os.listdir(os.getcwd()))
root_dir = "uploads/pdf-uploads"



for dirpath, dirnames, filenames in os.walk(root_dir):
    # print(" In", dirpath, "found files:", filenames)

    for fname in filenames:
        lower = fname.lower()
        if fname.endswith(".pdf"):
            full_path = os.path.join(dirpath,fname)
            with pdfplumber.open(full_path) as pdf:
                for page in pdf.pages:
                    #extracts text then outputs to the output file 
                    text = page.extract_text()
                    with open('output.txt', 'a', encoding='utf8') as f:
                        original = sys.stdout
                        sys.stdout = f
                        print(fname)
                        print(text)
                        print()
                        print()
                        print()
                        print()
                        print()
                        sys.stdout = original



with open('output.txt', 'r', encoding = 'utf8') as f:
    text_read = f.read()

sentences = nltk.sent_tokenize(text_read)

embeddings = model.encode(sentences)


ids = [f"sent-{i}" for i in range(len(sentences))]
metadatas = [{"source": "output.txt"} for _ in range(len(sentences))]

collection.upsert(
    documents=sentences,
    embeddings=embeddings.tolist(),
    ids=ids,
    metadatas=metadatas
)

if len(sentences) != len(embeddings):
    print("fail")
else :
    print("yay")



query = "What does this say about peace"
results = collection.query(query_texts=[query], n_results=5)

print("Top 5 matches:")
for doc in results['documents'][0]:
    print(" -", doc)










