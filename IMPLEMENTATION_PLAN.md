# GamerCat Implementation Plan 🐱🎮

## Overview
GamerCat is a local, real-time AI companion that uses vision and voice-to-voice models to provide context-aware interaction during gaming or other activities.

## Phase 1: Foundation & Screen Perception
- [x] **Project Scaffolding:** Create directory structure (`src/`, `tests/`) and `requirements.txt`.
- [x] **Screen Capture:** Implement `src/screen_capture.py` using Pillow to capture high-quality screenshots.
- [x] **Vision Engine:** Integrate `moondream` via Ollama in `src/vision_engine.py` to generate 30-word screen descriptions.
- [x] **Validation:** Verify image-to-text latency and description accuracy.

## Phase 2: Voice-to-Voice Loop
- [x] **Speech-to-Text (STT):** Implement `src/voice_engine.py` using `faster-whisper` for low-latency transcription.
- [x] **Text-to-Speech (TTS):** Integrate `pyttsx3` (native) as a baseline, with a path to `Piper` or `Coqui` for higher quality.
- [x] **Conversation Logic:** Implement `src/gamer_cat.py` as the main orchestrator to handle the "Listen -> Think -> Speak" loop.

## Phase 3: MCP Server Integration
- [x] **Server Setup:** Build an MCP server in `src/mcp_server.py` using `FastMCP`.
- [x] **Context Tool:** Expose `get_screen_context` as a tool for any MCP-compatible client.
- [x] **Background Processing:** Ensure screen capture runs in a non-blocking background thread.

## Phase 4: Brain & Personality Tuning
- [x] **Prompt Engineering:** Refine the system prompt for Llama 3 to ensure GamerCat is supportive, witty, and stays under 2 sentences.
- [x] **Context Awareness:** Implement logic to feed the 3 latest screen descriptions into the prompt for temporal awareness.

## Phase 5: Robustness & Testing
- [x] **Error Handling:** Robust handling for Ollama connection drops or microphone issues.
- [x] **Performance Profiling:** Monitor CPU/GPU usage to ensure it doesn't impact game performance significantly.
- [x] **User Feedback Loop:** Final testing of the end-to-end voice-to-voice experience.

---
*Targeting a fully offline, high-aesthetic prototype.*
