# GAMER-CAT

<p align="center">
  <img src="docs/assets/face_torso_anime_girl.png" alt="Gamer-Cat Avatar" width="300" />
</p>

<p align="center">
  <b>Your local anime gaming companion that sees your screen and talks back in real time.</b>
</p>

<p align="center">
  <a href="https://adityachauhan0.github.io/gamer-cat/"><img alt="Website" src="https://img.shields.io/badge/Website-Live-22c55e?style=for-the-badge"></a>
  <a href="https://github.com/adityachauhan0/gamer-cat"><img alt="Repo" src="https://img.shields.io/badge/GitHub-gamer--cat-4a89ff?style=for-the-badge"></a>
  <img alt="Local First" src="https://img.shields.io/badge/Local--First-Offline-9333ea?style=for-the-badge">
</p>

---

## What Is Gamer-Cat?
Gamer-Cat is a local-first AI gaming buddy built for players who want:
- live reactions while playing
- zero cloud dependency for core gameplay interaction
- a fun anime companion vibe, not a sterile assistant

It watches your screen context, listens to your voice, thinks with local models, and talks back like a teammate.

---

## Why It Feels Different
- `Screen-aware`: understands what is visible on your current game/activity screen
- `Voice loop`: hear + respond flow for natural interaction
- `Anime personality`: playful companion tone tuned for gamers
- `Privacy-friendly`: runs on your machine with local model infrastructure

---

## Quick Start
1. Pull models with Ollama:
```bash
ollama pull moondream
ollama pull llama3
```
2. Install/sync dependencies:
```bash
uv sync
```
3. Start Ollama:
```bash
ollama serve
```
4. Launch Gamer-Cat:
```bash
uv run python src/gamer_cat.py
```

---

## Anime Voice Preset
Use this in PowerShell before launch:

```powershell
$env:GAMERCAT_TTS_BACKEND="edge"
$env:GAMERCAT_TTS_VOICE="ja-JP-NanamiNeural"
$env:GAMERCAT_TTS_RATE="+20%"
$env:GAMERCAT_TTS_PITCH="+8Hz"
uv run python src/gamer_cat.py
```

---

## Links
- Live site: https://adityachauhan0.github.io/gamer-cat/
- Technical docs: [DOCUMENTATION.md](DOCUMENTATION.md)
- Source: https://github.com/adityachauhan0/gamer-cat

---

<p align="center"><b>Built for solo-queue grinders, chill farmers, and anime-core gamers.</b></p>
