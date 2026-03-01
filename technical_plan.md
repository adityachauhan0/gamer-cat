# Technical Plan: Gamer-Cat (Local Offline Companion)

## Objective
Create a low-latency, offline AI companion that perceives the user's screen and interacts via voice, staying within 16GB RAM.

## 1. Resource Budget (Target: <16GB RAM)
- **OS/System:** 2.0 GB
- **Vision (Moondream2):** 2.0 GB (Smallest capable VLM for screen descriptions)
- **Brain (Llama-3-8B-Q4_K_M):** 5.5 GB (The core personality)
- **STT (Faster-Whisper-Small):** 1.0 GB (Transcribes user speech)
- **TTS (Piper):** 0.5 GB (High-speed, low-resource voice synthesis)
- **Buffer/Other:** 1.0 GB
- **TOTAL:** ~12.0 GB (Safe margin of 4GB for the game/activity)

## 2. Component Breakdown

### A. Vision (The Eyes)
- **Frequency:** Every 10 seconds.
- **Tool:** `pyautogui` for screenshots + Moondream2.
- **Output:** "The player is currently in a dark forest, fighting a giant spider with a sword."

### B. Brain (The Personality)
- **System Prompt:** "You are a chill gaming buddy. You get text updates about what's on the screen. Don't be a robot; be a friend."
- **Context Management:** We will keep a sliding window of the last 5-10 screen descriptions to maintain continuity.

### C. Voice (The Ears & Mouth)
- **STT:** Faster-Whisper (runs on CPU/GPU) to detect when the user speaks.
- **TTS:** Piper. It uses raw PCM audio and is significantly faster than Coqui or others for real-time feel.

## 3. Potential Bottlenecks
- **GPU VRAM vs System RAM:** If running on a laptop with integrated graphics, the 16GB is shared. We must use 4-bit quantization (GGUF) strictly.
- **CPU Spikes:** Running VLM inference every 10s might cause frame drops in heavy games. We may need to "nice" the process priority.

## 4. Next Steps
1. Initialize a Python environment.
2. Prototype the "Screen -> Moondream -> Text" pipeline.
3. Test latency of STT + LLM + TTS chain.
