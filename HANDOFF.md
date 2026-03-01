# HANDOFF

## Snapshot
- Date: 2026-03-01
- Branch: `main`
- Latest pushed commit: `03b7f6b` (before current re-org pass)
- Remote: `origin/main` up to date

## What Was Completed
- Fixed TTS pipeline and fallback behavior in `src/voice_engine.py`.
- Installed and validated `edge-tts` for the active `python3` runtime.
- Added/standardized `uv` project setup:
  - `pyproject.toml`
  - `.python-version`
  - `uv.lock`
- Improved vision prompting and screen context handling for richer detail.
- Updated GitHub Pages site in `docs/` with:
  - new anime assets
  - JS visual effects (`docs/app.js`)
  - redesigned `docs/index.html` + `docs/style.css`
- Set GitHub Pages source to `main:/docs`.
- Switched default branch to `main` and removed remote `master`.
- Reworked README to gamer/anime style.
- Added `DOCUMENTATION.md` for technical details.
- Switched README hero image to `assets/banners/readme_banner.png`.
- Reorganized repo layout:
  - Moved planning/session markdown files into `notes/`
  - Moved loose root images into `assets/source-images/`
  - Moved README banner into `assets/banners/`
  - Added `.venv/` to `.gitignore`

## Important Config Notes
- Preferred runtime command:
  - `uv run python src/gamer_cat.py`
- Anime voice env (PowerShell):
  - `GAMERCAT_TTS_BACKEND=edge`
  - `GAMERCAT_TTS_VOICE=ja-JP-NanamiNeural`
  - `GAMERCAT_TTS_RATE=+20%`
  - `GAMERCAT_TTS_PITCH=+8Hz`

## Recent Commit Trail
- `03b7f6b` Use readme_banner.png as README hero banner
- `6db1b82` Redesign README with anime-first visual layout
- `a23a6a0` Resize README hero image for cleaner rendering
- `feb6525` Rewrite README for gamer/anime audience and split technical docs
- `66e804e` Fix edge-tts fallback handling and reduce warning spam
- `54a84d4` Use provided anime assets and add JS-driven landing page effects

## Outstanding Local (Not Committed)
- None expected after committing this re-org pass.

## Suggested Next Session Start
1. Refine `DOCUMENTATION.md` structure/content.
2. Optional cleanup: remove or commit root duplicate image files.
3. Validate final README and site visuals after GitHub Pages propagation.
