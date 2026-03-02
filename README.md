# GAMER-CAT

<p align="center">
  <img src="assets/banners/readme_banner.png" alt="Gamer-Cat Banner" width="100%" />
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

## Quick Start (Arch Linux)
1. Install system packages:
```bash
sudo pacman -S --needed ollama ffmpeg portaudio pipewire wireplumber grim slurp espeak-ng xdg-desktop-portal xdg-desktop-portal-kde
```
If you use KDE/Plasma, ensure portal services are running:
```bash
systemctl --user enable --now xdg-desktop-portal.service plasma-xdg-desktop-portal-kde.service
```
2. Pull models with Ollama (optional; startup will auto-pull missing models):
```bash
ollama pull moondream
ollama pull llama3.2:3b
```
3. Install/sync dependencies:
```bash
uv sync
```
4. Start Ollama (optional; startup will try to launch `ollama serve` automatically):
```bash
ollama serve
```
5. Optional: prefer fully local/offline TTS with Piper:
```bash
export GAMERCAT_TTS_BACKEND="piper"
export GAMERCAT_TTS_PIPER_MODEL="/absolute/path/to/model.onnx"
export GAMERCAT_LLM_MODEL="llama3.2:3b"
export GAMERCAT_VISION_MODEL="moondream"
```
6. Launch Gamer-Cat:
```bash
uv run python src/gamer_cat.py
```

---

## English Voice Preset (Local First)
Use this before launch:

```bash
export GAMERCAT_LOCAL_ONLY="1"
export GAMERCAT_TTS_BACKEND="auto"
export GAMERCAT_STT_MODEL="tiny.en"
export GAMERCAT_STT_LANGUAGE="en"
export GAMERCAT_LISTEN_DURATION="15"
export GAMERCAT_LISTEN_RESUME_DELAY="15"
uv run python src/gamer_cat.py
```

Optional cloud TTS mode (not local-only): set `GAMERCAT_LOCAL_ONLY=0` and `GAMERCAT_TTS_BACKEND=edge`.

Anime girl voice preset (recommended):

```bash
export GAMERCAT_LOCAL_ONLY="0"
export GAMERCAT_TTS_BACKEND="edge"
export GAMERCAT_TTS_VOICE="en-US-AnaNeural"
export GAMERCAT_TTS_RATE="+10%"
export GAMERCAT_TTS_PITCH="+12Hz"
export GAMERCAT_LISTEN_DURATION="15"
export GAMERCAT_LISTEN_RESUME_DELAY="15"
export GAMERCAT_PROACTIVE_ENABLED="0"
uv run python src/gamer_cat.py
```

### Fresh Reboot Startup
Use the helper script to configure services/env/models and launch GamerCat:

```bash
./startup.sh
```

Run it as your normal desktop user (no `sudo`).

### Screen Capture Backend
If auto-detection fails on your desktop session, set:

```bash
export GAMERCAT_CAPTURE_BACKEND="wayland" # or x11 / pil
# Optional on Wayland: allow X11 fallback attempts
export GAMERCAT_ALLOW_X11_ON_WAYLAND="1"
```

---

## Links
- Live site: https://adityachauhan0.github.io/gamer-cat/
- Technical docs: [DOCUMENTATION.md](DOCUMENTATION.md)
- Project notes/archive: [`notes/`](notes)
- Source: https://github.com/adityachauhan0/gamer-cat

---

<p align="center"><b>Built for solo-queue grinders, chill farmers, and anime-core gamers.</b></p>
