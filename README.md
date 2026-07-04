# ⚡ Sudipto's AI Command Center

![UI Theme](https://img.shields.io/badge/UI-Glassmorphism-blue?style=flat-square)
![Framework](https://img.shields.io/badge/Framework-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![LLM Provider](https://img.shields.io/badge/Powered_by-Groq-black?style=flat-square)

A highly interactive, aesthetically pleasing AI Chatbot application built using **Streamlit** and powered by the **Groq API**. This chatbot is designed to be an all-in-one AI command center, featuring document reading (RAG), web searching, image vision, voice input/output, and a comprehensive analytics dashboard.

## ✨ Key Features

*   **🧠 Advanced LLMs**: Access state-of-the-art models like LLaMA 3.3, LLaMA 3.1, Qwen 2.5, and LLaMA 4 Scout via Groq's lightning-fast inference.
*   **🌍 Multilingual Support**: Converse and generate responses in 12+ different languages including English, Spanish, French, Hindi, Bengali, Japanese, and Mandarin.
*   **📁 RAG (Retrieval-Augmented Generation)**: Upload `.txt`, `.pdf`, or `.docx` files to chat directly with your documents.
*   **👁️ Vision Capabilities**: Upload images (JPG/PNG) to analyze and discuss visual content (supported by LLaMA 4 Scout).
*   **🎤 Voice Input (STT)**: Speak to the AI using your microphone or upload audio files (WAV, MP3) for transcription via Whisper-large-v3-turbo.
*   **🔊 Voice Output (TTS)**: Hear the AI's responses aloud using integrated Google Text-to-Speech (gTTS).
*   **🌐 Real-Time Context**: Toggle on **Web Search** (DuckDuckGo) and **Wikipedia** integration to give the AI up-to-date factual context.
*   **💾 Persistent Memory & Export**: Chats are saved automatically using a local SQLite database. Export your chat histories to Markdown.
*   **📊 Analytics Dashboard**: Track your usage over time with interactive Plotly graphs, view token usage, and download raw analytics as a CSV.
*   **🎨 Glassmorphism UI**: A beautiful, modern, transparent user interface layered over custom background visuals.

## 🛠️ Tech Stack

*   **Frontend/App Framework:** [Streamlit](https://streamlit.io/)
*   **AI API:** [Groq](https://groq.com/)
*   **Database:** SQLite
*   **Data Analysis & Vis:** Pandas, Plotly Express
*   **Document Parsing:** PyPDF2, python-docx
*   **Search Integrations:** duckduckgo_search, wikipedia
*   **Audio Processing:** gTTS, audio_recorder_streamlit

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone [https://github.com/yourusername/sudiptos-chatbot.git](https://github.com/yourusername/sudiptos-chatbot.git)
cd sudiptos-chatbot
