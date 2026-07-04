import streamlit as st
import sqlite3
import pandas as pd
import json
import base64
from datetime import datetime
from io import BytesIO
import wikipedia
import plotly.express as px

# Third-party integrations
from groq import Groq
from PyPDF2 import PdfReader
from docx import Document
from duckduckgo_search import DDGS
from gtts import gTTS
from audio_recorder_streamlit import audio_recorder

# --------------------------------------------------
# Supported Languages Mapping (Expanded)
# --------------------------------------------------
SUPPORTED_LANGUAGES = {
    "English": "en", "Spanish": "es", "French": "fr", "German": "de",
    "Hindi": "hi", "Bengali": "bn", "Japanese": "ja", "Arabic": "ar",
    "Mandarin": "zh-cn", "Russian": "ru", "Portuguese": "pt", "Italian": "it"
}

# --------------------------------------------------
# Page & Database Setup
# --------------------------------------------------
st.set_page_config(page_title="Sudipto's ChatBot", page_icon="⚡", layout="wide")

# Custom CSS Styling (Upgraded for Glassmorphism & Background Image)
def inject_css():
    st.markdown(
        """
        <style>
            :root {
                color-scheme: dark;
                font-family: 'Inter', sans-serif;
            }
            
            /* Background Image for the whole app */
            .stApp {
                background-image: url("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop") !important;
                background-size: cover !important;
                background-position: center !important;
                background-attachment: fixed !important;
            }
            
            /* Make header transparent */
            [data-testid="stHeader"] {
                background: transparent !important;
            }

            /* Glassmorphism for the main container */
            .block-container {
                background: rgba(15, 23, 42, 0.65) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px !important;
                padding: 2rem !important;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                margin-top: 3rem !important;
                margin-bottom: 3rem !important;
                max-width: 95% !important;
            }
            
            /* Glassmorphism for the Sidebar */
            [data-testid="stSidebar"] {
                background: rgba(10, 15, 30, 0.5) !important;
                backdrop-filter: blur(20px) !important;
                -webkit-backdrop-filter: blur(20px) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }

            h1, h2, h3, h4, h5, h6 {
                color: #ffffff !important;
                text-shadow: 0 2px 4px rgba(0,0,0,0.5);
            }
            
            /* Gradient Text for Main Title */
            h1 {
                background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: none;
            }

            /* Stylish Buttons */
            .stButton>button,
            .stDownloadButton>button,
            button[kind="primary"] {
                background: linear-gradient(135deg, #0284c7, #3b82f6) !important;
                color: #ffffff !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 12px !important;
                padding: 0.6rem 1.2rem !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4) !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton>button:hover,
            .stDownloadButton>button:hover,
            button[kind="primary"]:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(2, 132, 199, 0.6) !important;
            }

            /* Metrics Cards */
            .stMetric {
                background: rgba(30, 41, 59, 0.5) !important;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 16px !important;
                padding: 1rem !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            /* Inputs and Selectboxes */
            .stTextInput > div > input,
            .stTextInput > div > textarea,
            .stSelectbox > div > div > div,
            .stToggle > div > div,
            .stChatInputContainer {
                background: rgba(15, 23, 42, 0.7) !important;
                backdrop-filter: blur(10px);
                color: #f8fafc !important;
                border-radius: 12px !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
            }
            
            /* Chat Messages styling */
            .stChatMessage {
                background: rgba(30, 41, 59, 0.4) !important;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 1rem;
                margin-bottom: 1rem;
                backdrop-filter: blur(5px);
            }
            
            /* Fix Microphone button wrapper alignment */
            .audio-recorder {
                display: flex;
                justify-content: center;
                align-items: center;
                background: rgba(30, 41, 59, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 50%;
                padding: 10px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .audio-recorder:hover {
                background: rgba(56, 189, 248, 0.2);
                border-color: #38bdf8;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# Initialize SQLite for persistent chat history
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS messages 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, timestamp DATETIME, tokens_used INTEGER DEFAULT 0)''')
try:
    c.execute("ALTER TABLE messages ADD COLUMN tokens_used INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass
conn.commit()

# --------------------------------------------------
# Utility Functions
# --------------------------------------------------
def save_message(role, content, tokens=0):
    c.execute("INSERT INTO messages (role, content, timestamp, tokens_used) VALUES (?, ?, ?, ?)", 
              (role, content, datetime.now(), tokens))
    conn.commit()

def load_history():
    return pd.read_sql_query("SELECT role, content FROM messages ORDER BY id ASC", conn).to_dict('records')

def extract_text_from_file(uploaded_files):
    text = ""
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith(".txt"):
            text += uploaded_file.getvalue().decode("utf-8") + "\n"
        elif uploaded_file.name.endswith(".pdf"):
            pdf = PdfReader(uploaded_file)
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        elif uploaded_file.name.endswith(".docx"):
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    return text

def web_search(query):
    try:
        with DDGS() as ddgs:
            # Enforce list to correctly execute the search call
            results = list(ddgs.text(query, max_results=3))
            
        if not results:
            return "No web results found."
            
        return "\n".join([f"Source: {res.get('href', 'Unknown')}\nInfo: {res.get('body', 'No snippet')}" for res in results])
    except Exception as e:
        return f"Web search failed: {e}"

def wiki_search(query):
    try:
        # Search for the best Wikipedia page title first rather than strictly matching the full sentence prompt
        search_results = wikipedia.search(query)
        if not search_results:
            return "No relevant Wikipedia articles found."
            
        # Get summary of the closest result
        return wikipedia.summary(search_results[0], sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        # If the term is ambiguous, pick the first option
        return wikipedia.summary(e.options[0], sentences=3)
    except Exception as e:
        return f"Wikipedia search failed: {e}"

def text_to_speech(text, lang_code='en'):
    try:
        tts = gTTS(text=text, lang=lang_code)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        return None

def export_chat_to_markdown(messages):
    md_content = "# Chat History\n\n"
    for msg in messages:
        role = "🤖 AI" if msg["role"] == "assistant" else "👤 You"
        md_content += f"### {role}\n{msg['content']}\n\n---\n\n"
    return md_content

# --- Callback for Suggestions ---
def set_starter_prompt(text):
    st.session_state.starter_prompt = text

# --------------------------------------------------
# Sidebar Settings & Tools
# --------------------------------------------------
with st.sidebar:
    st.title("⚙️ AI Command Center")
    
    # NEW CHAT BUTTON
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        c.execute("DELETE FROM messages")
        conn.commit()
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    api_key = st.text_input("🔑 Groq API Key", type="password")
    
    st.subheader("🧠 Model Selection")
    selected_model = st.selectbox("Primary Model", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "qwen-2.5-32b",
        "meta-llama/llama-4-scout-17b-16e-instruct"
    ])
    
    st.subheader("🌐 Capabilities")
    selected_lang_name = st.selectbox("Output Language", list(SUPPORTED_LANGUAGES.keys()))
    selected_lang_code = SUPPORTED_LANGUAGES[selected_lang_name]

    enable_search = st.toggle("🌐 Enable Web Search (DuckDuckGo)")
    enable_wiki = st.toggle("📚 Enable Wikipedia")
    enable_tts = st.toggle("🔊 Enable Audio Responses (TTS)")
    
    st.markdown("---")
    st.subheader("📁 File Management")
    uploaded_docs = st.file_uploader("📄 Upload Docs (RAG)", type=["txt", "pdf", "docx"], accept_multiple_files=True)
    uploaded_image = st.file_uploader("📷 Upload Image (Vision)", type=["jpg", "png", "jpeg"])
    uploaded_audio = st.file_uploader("🎤 Upload Audio (STT)", type=["wav", "mp3", "m4a"])
    
    st.markdown("---")
    if st.session_state.get('messages'):
        md_data = export_chat_to_markdown(st.session_state.messages)
        st.download_button("💾 Download Chat (Markdown)", md_data, file_name="chat_history.md", mime="text/markdown")

# Load session state from DB if empty
if "messages" not in st.session_state or not st.session_state.messages:
    st.session_state.messages = load_history()

# --------------------------------------------------
# Main UI Layout
# --------------------------------------------------
tab_chat, tab_dashboard = st.tabs(["💬 Chat Interface", "📊 Analytics Dashboard"])

with tab_chat:
    st.title("⚡ Sudipto's ChatBot")
    
    # SUGGESTION PROMPTS (Only visible if chat history is empty AND no prompt was just clicked)
    if not st.session_state.messages and "starter_prompt" not in st.session_state:
        st.markdown("<h3 style='text-align: center; color: #cbd5e1;'>How can I help you today?</h3>", unsafe_allow_html=True)
        st.write("")
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.button("🚀 Explain Quantum Computing", use_container_width=True, on_click=set_starter_prompt, args=("Explain quantum computing in simple terms.",))
        with col_s2:
            st.button("🐍 Write a Python Timer", use_container_width=True, on_click=set_starter_prompt, args=("Write a simple countdown timer script in Python.",))
        with col_s3:
            st.button("✈️ 3-Day Paris Itinerary", use_container_width=True, on_click=set_starter_prompt, args=("Plan a comprehensive 3-day travel itinerary for Paris.",))
                
        st.markdown("<br>", unsafe_allow_html=True)

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Input Area (Text + Voice Mic) - FIXED ALIGNMENT
    col1, col2 = st.columns([10, 1], vertical_alignment="bottom")
    with col1:
        prompt = st.chat_input("Message the AI...")
    with col2:
        audio_bytes = audio_recorder(text="", icon_size="2x")
        
    # Check if a starter suggestion was clicked
    if "starter_prompt" in st.session_state:
        prompt = st.session_state.starter_prompt
        # Only delete it if we have an API key ready so it's not lost when clicking without a key
        if api_key:
            del st.session_state.starter_prompt

    # Audio Processing (Mic or Upload)
    audio_source = audio_bytes if audio_bytes else (uploaded_audio.getvalue() if uploaded_audio else None)

    if audio_source and not prompt:
        if not api_key:
            st.error("🔑 Please enter your Groq API Key in the sidebar to process audio.")
        else:
            client = Groq(api_key=api_key)
            audio_file = BytesIO(audio_source)
            audio_file.name = "audio.wav" if audio_bytes else uploaded_audio.name
            with st.spinner("Transcribing..."):
                transcription = client.audio.transcriptions.create(
                    file=(audio_file.name, audio_file.read()),
                    model="whisper-large-v3-turbo",
                    language=selected_lang_code
                )
                prompt = transcription.text

    # Process Input
    if prompt:
        if not api_key:
            # Prevent the app from quietly failing if the API key is missing
            st.warning("⚠️ Please enter your Groq API Key in the sidebar to start chatting.")
        else:
            client = Groq(api_key=api_key)
            
            # Display User Message
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            save_message("user", prompt)

            # Context Building (RAG, Web, Wiki)
            context = ""
            if uploaded_docs:
                doc_text = extract_text_from_file(uploaded_docs)
                context += f"\n\n[Document Context]: {doc_text[:5000]}"
                
            if enable_search:
                with st.spinner("Searching DuckDuckGo..."):
                    context += f"\n\n[Web Search Results]: {web_search(prompt)}"
                    
            if enable_wiki:
                with st.spinner("Querying Wikipedia..."):
                    context += f"\n\n[Wikipedia Info]: {wiki_search(prompt)}"

            # Final Prompt Construction
            final_prompt = prompt
            if context:
                final_prompt = f"User Question: {prompt}\n\nUse the following context to answer:\n{context}"
            
            lang_instruction = f"IMPORTANT: Please provide your entire response in {selected_lang_name}."
            final_prompt = f"{lang_instruction}\n\n{final_prompt}"

            # Vision Setup
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
            
            if uploaded_image and selected_model == "meta-llama/llama-4-scout-17b-16e-instruct":
                base64_image = base64.b64encode(uploaded_image.getvalue()).decode('utf-8')
                api_messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": final_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                })
            else:
                api_messages.append({"role": "user", "content": final_prompt})

            # Fetch AI Response
            with st.chat_message("assistant"):
                try:
                    stream = client.chat.completions.create(
                        model=selected_model,
                        messages=api_messages,
                        stream=True
                    )
                    
                    response_text = ""
                    placeholder = st.empty()
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            response_text += chunk.choices[0].delta.content
                            placeholder.markdown(response_text + "▌")
                    placeholder.markdown(response_text)
                    
                    # Estimate tokens
                    estimated_tokens = int(len(response_text.split()) * 1.3)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    save_message("assistant", response_text, tokens=estimated_tokens)
                    
                    if enable_tts:
                        with st.spinner("Generating Audio..."):
                            audio_data = text_to_speech(response_text, lang_code=selected_lang_code)
                            if audio_data:
                                # Added autoplay=True so it speaks out loud immediately
                                st.audio(audio_data, format="audio/mp3", autoplay=True)
                            else:
                                st.error("Failed to generate Text-to-Speech audio.")
                            
                except Exception as e:
                    st.error(f"Error: {e}")

# --------------------------------------------------
# Enhanced Analytics Dashboard
# --------------------------------------------------
with tab_dashboard:
    st.title("📊 Advanced Analytics Dashboard")
    df = pd.read_sql_query("SELECT * FROM messages", conn)
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['word_count'] = df['content'].apply(lambda x: len(str(x).split()))
        
        # Top Level Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Messages", len(df))
        col2.metric("User Queries", len(df[df['role'] == 'user']))
        col3.metric("Est. Tokens Used", df['tokens_used'].sum())
        col4.metric("Total Words", df['word_count'].sum())
        
        # Interactive Plotly Charts
        st.subheader("📈 Activity Over Time")
        activity_data = df.groupby([df['timestamp'].dt.date, 'role']).size().reset_index(name='count')
        
        # Transparent background for Plotly to match theme
        fig = px.line(activity_data, x='timestamp', y='count', color='role', markers=True, title="Messages per Day")
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f8fafc'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Export Data
        st.subheader("💾 Export Raw Data")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Analytics as CSV",
            data=csv,
            file_name='ai_analytics.csv',
            mime='text/csv',
        )
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Start chatting to generate interactive analytics!")