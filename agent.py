import os
import asyncio
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types
import tools # Import the tool file we just made

# 1. Setup Environment
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. Setup Memory (ChromaDB)
# We reuse the same embedding function logic from build_rag.py
from chromadb import Documents, EmbeddingFunction, Embeddings
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=input
        )
        return [e.values for e in response.embeddings]

try:
    chroma_client = chromadb.PersistentClient(path="./rag_storage")
    db = chroma_client.get_collection(
        name="docuops_knowledge",
        embedding_function=GeminiEmbeddingFunction()
    )
    print("🧠 Memory loaded successfully!")
except Exception as e:
    print(f"⚠️ Warning: Could not load Memory. Run build_rag.py first. Error: {e}")
    db = None

# 3. Define the Retrieval Helper
def query_memory(query_text: str, n_results=2):
    if not db:
        return "No memory available."
    results = db.query(query_texts=[query_text], n_results=n_results)
    # Flatten the list of documents
    docs = results['documents'][0] if results['documents'] else []
    return "\n\n".join(docs)

# 4. The Main Agent Loop
async def main():
    # We define the tool dictionary for the model
    # The 'function' is the actual python code, the SDK handles the rest.
    my_tools = [tools.list_code_files]

    system_instruction = """
    You are DocuOps, a Senior Software Architect.
    1. ALWAYS check the user's Context (RAG) first to understand the documentation.
    2. If the user asks about their files, USE the 'list_code_files' tool to see what exists.
    3. Be helpful, concise, and professional.
    """

    # We use a Chat Session so the agent remembers the conversation turns
    chat = client.aio.chats.create(
        model="gemini-2.5-flash-lite", # Swapped back to experimental, check your list if this fails!
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=my_tools,
            automatic_function_calling=dict(disable=False) # Enable the agent to run the code
        )
    )

    print("\n🤖 DocuOps is ready! (Type 'quit' to exit)")
    print("-" * 50)

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break

        # A. Context Engineering (RAG)
        # We fetch relevant docs BEFORE sending to the LLM
        print("   (Thinking... searching memory...)")
        relevant_docs = query_memory(user_input)
        
        # We inject the memory into the prompt invisibly to the user
        full_prompt = f"""
        User Query: {user_input}
        
        Relevant Documentation Context:
        {relevant_docs}
        """

        # B. Generate Response (with Tools enabled)
        try:
            response = await chat.send_message(full_prompt)
            print(f"🤖 DocuOps: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())