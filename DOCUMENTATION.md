# DOCUMENTATION

## Project Goal
Gamer-Cat is a local-first AI companion that combines screen understanding, conversational AI, speech recognition, and speech synthesis for real-time gameplay interaction.

## Architecture Overview
- `src/screen_capture.py`: Captures screen frames and prepares image payloads
- `src/vision_engine.py`: Sends images to Ollama vision model (`moondream`)
- `src/mcp_server.py`: Maintains shared screen context and exposes MCP tool(s)
- `src/gamer_cat.py`: Main orchestrator loop (listen -> think -> speak)
- `src/voice_engine.py`: STT + TTS engine with backend fallback logic

## Runtime Stack
- Vision: `moondream` via Ollama
- LLM: `llama3` via Ollama
- STT: `faster-whisper`
- TTS Backends:
  - `edge-tts` (preferred for quality)
  - Windows `System.Speech` fallback
  - `pyttsx3` fallback
  - Optional `piper` backend support

## Environment and Tooling
- Python: pinned with `uv` (`.python-version`)
- Dependency management: `pyproject.toml` + `uv.lock`
- Local env: `.venv`

## Setup
1. Install Ollama and required models:
```bash
ollama pull moondream
ollama pull llama3
```
2. Install dependencies:
```bash
uv sync
```
3. Start Ollama:
```bash
ollama serve
```
4. Run app:
```bash
uv run python src/gamer_cat.py
```

## TTS Environment Variables
- `GAMERCAT_TTS_BACKEND`
- `GAMERCAT_TTS_VOICE`
- `GAMERCAT_TTS_RATE`
- `GAMERCAT_TTS_PITCH`
- `GAMERCAT_TTS_PIPER_EXE`
- `GAMERCAT_TTS_PIPER_MODEL`
- `GAMERCAT_TTS_PIPER_CONFIG`
- `GAMERCAT_TTS_PIPER_LENGTH_SCALE`

## Notes
- The app currently targets Windows as primary runtime.
- `mcp_server.py` uses a lock to guard shared context state.
- Vision prompting is tuned for concrete on-screen details with chess awareness.

