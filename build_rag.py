import os
import glob
import chromadb
from dotenv import load_dotenv
from google import genai
from chromadb import Documents, EmbeddingFunction, Embeddings

# 1. Setup
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. Define a Custom Embedding Function for Chroma
# This tells ChromaDB to use Google's 'text-embedding-004' model
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=input
        )
        # Extract the embedding vectors from the response
        return [e.values for e in response.embeddings]

# 3. Initialize ChromaDB (Local Storage)
chroma_client = chromadb.PersistentClient(path="./rag_storage")
db = chroma_client.get_or_create_collection(
    name="docuops_knowledge",
    embedding_function=GeminiEmbeddingFunction()
)

def main():
    print("📂 Scanning 'docs/' folder...")
    doc_files = glob.glob("docs/*.md") + glob.glob("docs/*.txt")
    
    if not doc_files:
        print("❌ No files found! Please add .md or .txt files to the 'docs' folder.")
        return

    documents = []
    ids = []

    # 4. Read and Chunk files
    for file_path in doc_files:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            # Simple chunking: Treat the whole file as one chunk for this POC.
            # In a real app, you'd split this by paragraphs.
            documents.append(text)
            ids.append(os.path.basename(file_path))
            print(f"   found: {file_path}")

    # 5. Add to Vector Store (This triggers the API to generate embeddings)
    print("🧠 Generating embeddings and storing...")
    db.upsert(documents=documents, ids=ids)
    print(f"✅ Successfully stored {len(documents)} documents in the Knowledge Base!")

if __name__ == "__main__":
    main()