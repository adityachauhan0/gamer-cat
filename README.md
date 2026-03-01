# GamerCat 🐱🎮

A real-time AI companion that sees what you're doing and talks to you.

## Features
- **Local Screen Perception:** Captures your screen every 10 seconds and describes it in 30 words.
- **Voice-to-Voice:** Speak to GamerCat, and it responds with context-aware buddy talk.
- **MCP Server:** Exposes screen context as a standard Model Context Protocol tool.
- **Fully Offline:** Uses Ollama for vision/chat and Whisper for STT.

## Prerequisites
1. **Ollama:** [Install Ollama](https://ollama.com/) and download the models:
   ```bash
   ollama pull moondream
   ollama pull llama3
   ```
2. **Python 3.10+**: Recommended.
3. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On Windows, you might need to install `PyAudio` via a wheel if `pip install pyaudio` fails.*

## How to Run
1. Start Ollama: `ollama serve` (if not already running).
2. Run GamerCat:
   ```bash
   python src/gamer_cat.py
   ```

## Files
- `src/screen_capture.py`: Screen capture logic (Pillow).
- `src/vision_engine.py`: Image-to-text via Ollama.
- `src/voice_engine.py`: Whisper STT & pyttsx3 TTS.
- `src/mcp_server.py`: MCP Server implementation.
- `src/gamer_cat.py`: Main orchestration loop.
