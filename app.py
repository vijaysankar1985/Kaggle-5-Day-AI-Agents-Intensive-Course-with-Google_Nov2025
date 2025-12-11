import os
import asyncio
import streamlit as st
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types
from chromadb import Documents, EmbeddingFunction, Embeddings
import tools  # Ensure tools.py is in the same directory

# 1. Page Configuration
st.set_page_config(page_title="DocuOps Agent", page_icon="🤖")
st.title("🤖 DocuOps: Legacy Code Architect")

# 2. Setup (Load only once)
@st.cache_resource
def setup_resources():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ API Key not found! Please check your .env file or Docker env vars.")
        st.stop()
    
    client = genai.Client(api_key=api_key)
    
    # Define Embedding Function
    class GeminiEmbeddingFunction(EmbeddingFunction):
        def __call__(self, input: Documents) -> Embeddings:
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=input
            )
            return [e.values for e in response.embeddings]

    # Load Memory
    try:
        chroma_client = chromadb.PersistentClient(path="./rag_storage")
        db = chroma_client.get_collection(
            name="docuops_knowledge", 
            embedding_function=GeminiEmbeddingFunction()
        )
        st.sidebar.success("🧠 Memory Loaded")
    except Exception as e:
        db = None
        st.sidebar.warning(f"⚠️ Memory not found: {e}")
        
    return client, db

client, db = setup_resources()

# 3. Helper Functions
def query_memory(query_text):
    if not db: return "No memory available."
    results = db.query(query_texts=[query_text], n_results=2)
    return "\n\n".join(results['documents'][0]) if results['documents'] else "No relevant docs found."

# 4. Chat Session Management
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. The Main Interaction Loop
if prompt := st.chat_input("Ask about your documentation or code..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare Context (RAG)
    with st.status("Thinking...", expanded=False) as status:
        st.write("🔍 Searching documentation...")
        relevant_docs = query_memory(prompt)
        
        st.write("🛠️ Checking tools...")
        # (Tool logic is handled by the model, but we prepare the prompt here)
        full_prompt = f"""
        User Query: {prompt}
        
        Relevant Documentation Context:
        {relevant_docs}
        """
        status.update(label="Generating response...", state="running")

        # Generate Response
        try:
            # We use the synchronous API for Streamlit simplicity here, 
            # or wrap async in asyncio.run()
            
            # Define Tools
            my_tools = [tools.list_code_files]
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp", # Change if needed
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are DocuOps, a Senior Software Architect. Use RAG and Tools.",
                    tools=my_tools,
                    automatic_function_calling=dict(disable=False)
                )
            )
            
            response_text = response.text
            
        except Exception as e:
            response_text = f"❌ Error: {str(e)}"
            
        status.update(label="Done!", state="complete", expanded=False)

    # Display Assistant Response
    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})