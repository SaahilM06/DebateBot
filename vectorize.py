import chromadb
import pdfplumber
import os
import sys
from chromadb.errors import UniqueConstraintError

chroma_client = chromadb.PersistentClient()

chroma_client.delete_collection(name="collection2") 

# print("Working directory:", os.getcwd())
# print("Dir listing here:", os.listdir(os.getcwd()))


try:
    collection = chroma_client.create_collection(name="collection2")
except UniqueConstraintError:
    collection = chroma_client.get_collection(name="collection2")


collection.upsert(
    documents = [
        "This is speech 1",
        "This is speech 2",
        "This is speech 3",
        "This is speech 4",
        "This is speech 5",
        "This is speech 6",
        "This is speech 7",

    ],
    ids = ["id1", "id2", "id3","id4","id5", "id6", "id7"]
)


root_dir = "data /pdfs"
counter_var = 0


for dirpath, dirnames, filenames in os.walk(root_dir):
    # print(" In", dirpath, "found files:", filenames)

    for fname in filenames:
        lower = fname.lower()
        # print("  -- checking", fname, "->", end=" ")

        if fname.endswith(".pdf"):
            counter_var = counter_var + 1
            full_path = os.path.join(dirpath,fname)
            with pdfplumber.open(full_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    with open('output.txt', 'a', encoding='utf8') as f:
                        original = sys.stdout
                        sys.stdout = f
                        for i in range(counter_var):
                            print(text)
                        print()
                        print()
                        print()
                        print()
                        print()
                        sys.stdout = original





