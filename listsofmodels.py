import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

print("🔍 Listing all available models...")

try:
    # We will just print every model found.
    for model in client.models.list():
        print(f"👉 {model.name}")
        
except Exception as e:
    print(f"❌ Error: {e}")