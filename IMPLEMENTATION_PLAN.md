# GamerCat Implementation Plan 🐱🎮

## Overview
GamerCat is a local, real-time AI companion that uses vision and voice-to-voice models to provide context-aware interaction during gaming or other activities.

## Phase 1: Foundation & Screen Perception
- [x] **Project Scaffolding:** Create directory structure (`src/`, `tests/`) and `requirements.txt`.
- [x] **Screen Capture:** Implement `src/screen_capture.py` using Pillow to capture high-quality screenshots.
- [ ] **Vision Engine:** Integrate `moondream` via Ollama in `src/vision_engine.py` to generate 30-word screen descriptions.
- [ ] **Validation:** Verify image-to-text latency and description accuracy.

## Phase 2: Voice-to-Voice Loop
- [ ] **Speech-to-Text (STT):** Implement `src/voice_engine.py` using `faster-whisper` for low-latency transcription.
- [ ] **Text-to-Speech (TTS):** Integrate `pyttsx3` (native) as a baseline, with a path to `Piper` or `Coqui` for higher quality.
- [ ] **Conversation Logic:** Implement `src/gamer_cat.py` as the main orchestrator to handle the "Listen -> Think -> Speak" loop.

## Phase 3: MCP Server Integration
- [ ] **Server Setup:** Build an MCP server in `src/mcp_server.py` using `FastMCP`.
- [ ] **Context Tool:** Expose `get_screen_context` as a tool for any MCP-compatible client.
- [ ] **Background Processing:** Ensure screen capture runs in a non-blocking background thread.

## Phase 4: Brain & Personality Tuning
- [ ] **Prompt Engineering:** Refine the system prompt for Llama 3 to ensure GamerCat is supportive, witty, and stays under 2 sentences.
- [ ] **Context Awareness:** Implement logic to feed the 3 latest screen descriptions into the prompt for temporal awareness.

## Phase 5: Robustness & Testing
- [ ] **Error Handling:** Robust handling for Ollama connection drops or microphone issues.
- [ ] **Performance Profiling:** Monitor CPU/GPU usage to ensure it doesn't impact game performance significantly.
- [ ] **User Feedback Loop:** Final testing of the end-to-end voice-to-voice experience.

---
*Targeting a fully offline, high-aesthetic prototype.*
