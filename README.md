# 😼 GAMER-CAT 🎮

> **Your ultimate AI gaming buddy. No lag. No cloud. All vibes.**

Gamer-Cat is a local-first, offline AI companion that actually **sees** what you're doing. Whether you're clutching a 1v5 in Valorant or peacefully farming in Stardew Valley, Gamer-Cat is there to hype you up, give (sometimes questionable) advice, and keep you company.

---

## 🚀 LEVEL UP YOUR SETUP

*   **👁️ Visual Context:** Snaps your screen every 10s. It knows when you're in the lobby or in the heat of battle.
*   **🗣️ Real-time Voice:** Natural, low-latency voice interaction. Talk to it like a real homie.
*   **🔒 100% Offline:** Runs entirely on your rig. No telemetry, no data harvesting, no lag spikes from cloud APIs.
*   **MCP Server:** Exposes screen context as a standard Model Context Protocol tool.

---

## 🛠️ TECH STACK (The "Specs")

| Component | Tech |
| :--- | :--- |
| **The Brain** | Llama-3 (Ollama) |
| **The Eyes** | Moondream (Ollama) |
| **The Ears** | Faster-Whisper |
| **The Voice** | pyttsx3 (SAPI5) |

---

## ⚙️ PREREQUISITES

1. **Ollama:** [Install Ollama](https://ollama.com/) and pull the models:
   ```bash
   ollama pull moondream
   ollama pull llama3
   ```
2. **uv + Python 3.13.5** (pinned via `.python-version`).
3. **FFmpeg:** Required for audio processing.
4. **Dependencies:**
   ```bash
   uv sync
   ```
   *Note: `uv.lock` pins all dependency versions for reproducible installs.*

---

## 👾 HOW TO RUN

1.  **Start Ollama:** `ollama serve` (if not already running).
2.  **Launch Gamer-Cat:**
    ```bash
    uv run python src/gamer_cat.py
    ```

---

## 📂 FILE STRUCTURE

- `src/screen_capture.py`: Screen capture logic (Pillow).
- `src/vision_engine.py`: Image-to-text via Ollama.
- `src/voice_engine.py`: Whisper STT & pyttsx3 TTS.
- `src/mcp_server.py`: MCP Server implementation.
- `src/gamer_cat.py`: Main orchestration loop.

---

**Built with ❤️ for gamers who play too much.**
