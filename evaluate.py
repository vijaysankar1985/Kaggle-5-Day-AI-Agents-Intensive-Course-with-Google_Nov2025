import asyncio
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
import tools
# Import your agent logic (we need to slightly refactor agent.py to be importable, 
# but for now, we'll just re-instantiate the chat session here for simplicity)
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings

# 1. Setup
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Re-setup Memory (Copying for simplicity in this script)
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=input
        )
        return [e.values for e in response.embeddings]

try:
    chroma_client = chromadb.PersistentClient(path="./rag_storage")
    db = chroma_client.get_collection(name="docuops_knowledge", embedding_function=GeminiEmbeddingFunction())
except:
    db = None

def query_memory(query_text):
    if not db: return ""
    results = db.query(query_texts=[query_text], n_results=2)
    return "\n\n".join(results['documents'][0]) if results['documents'] else ""

# 2. The Golden Dataset
# Format: {Question, Expected Behavior/Answer}
test_cases = [
    {
        "question": "What files are in the current directory?",
        "expected": "It should use the list_code_files tool and list the files found."
    },
    {
        "question": "How do I implement a user exit?",
        "expected": "It should retrieve information from the RAG documentation about user exits and explain the implementation steps."
    }
]

# 3. The Judge Logic
async def run_judge(question, agent_response, expected_behavior):
    judge_prompt = f"""
    You are an impartial judge evaluating an AI Agent's performance.
    
    User Question: {question}
    Expected Behavior: {expected_behavior}
    Agent Actual Response: {agent_response}
    
    Please rate the Agent's response on a scale of 1 to 5:
    1: Completely wrong or hallucinated.
    3: Partially correct but missed key context.
    5: Perfect execution, retrieved correct data/tools, and answered accurately.
    
    Output ONLY the number (e.g., 5).
    """
    
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash-lite", # Or 1.5-flash
        contents=judge_prompt
    )
    return response.text.strip()

async def main():
    print("⚖️ Starting Evaluation...\n")
    
    # Initialize Agent Chat
    my_tools = [tools.list_code_files]
    chat = client.aio.chats.create(
        model="gemini-2.5-flash-lite", # Or 1.5-flash
        config=types.GenerateContentConfig(
            system_instruction="You are DocuOps. Use RAG and Tools to help.",
            tools=my_tools,
            automatic_function_calling=dict(disable=False)
        )
    )

    for test in test_cases:
        print(f"🔹 Testing: '{test['question']}'")
        
        # 1. Run Agent
        # (Simplified RAG injection for the test)
        context_data = query_memory(test['question'])
        full_prompt = f"Context: {context_data}\n\nQuestion: {test['question']}"
        
        agent_res = await chat.send_message(full_prompt)
        print(f"   Agent said: {agent_res.text[:100]}...") # Print first 100 chars
        
        # 2. Run Judge
        score = await run_judge(test['question'], agent_res.text, test['expected'])
        print(f"   🏆 Judge Score: {score}/5\n")

        # 3. ADD THIS PAUSE
        print("   😴 Resting for 30 seconds to respect API quotas...")
        time.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())