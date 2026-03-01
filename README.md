# GAMER-CAT

![Gamer-Cat Avatar](docs/assets/face_torso_anime_girl.png)

> Your local anime gaming companion that sees your screen, talks back, and hypes you up in real time.

## Why This Is Different
Gamer-Cat is built for people who want the fun of an AI teammate without cloud lag, creepy telemetry, or internet dependency.

You play. She watches the match. She reacts instantly.

## Core Vibe
- Real-time gaming buddy energy
- Anime personality with voice interaction
- Offline-first and privacy-first
- Designed to run beside your game, not replace it

## What Gamer-Cat Can Do
- Watch your screen and describe what is happening
- Talk to you with a live conversational loop
- Keep context from recent screen events
- Give playful, contextual commentary while you play

## Quick Start
1. Install Ollama and pull models:
```bash
ollama pull moondream
ollama pull llama3
```
2. Sync project dependencies:
```bash
uv sync
```
3. Start Ollama:
```bash
ollama serve
```
4. Run Gamer-Cat:
```bash
uv run python src/gamer_cat.py
```

## Voice Preset (Anime Style)
Use this in PowerShell before launching:

```powershell
$env:GAMERCAT_TTS_BACKEND="edge"
$env:GAMERCAT_TTS_VOICE="ja-JP-NanamiNeural"
$env:GAMERCAT_TTS_RATE="+20%"
$env:GAMERCAT_TTS_PITCH="+8Hz"
uv run python src/gamer_cat.py
```

## Screens + Website
- Live project page: https://adityachauhan0.github.io/gamer-cat/
- Website assets and styling live under `docs/`

## Technical Docs
All engineering details moved here:

- [DOCUMENTATION.md](DOCUMENTATION.md)

## Source
- GitHub: https://github.com/adityachauhan0/gamer-cat

---

Built for solo queue grinders, chill farmers, and anime-core gamers.
