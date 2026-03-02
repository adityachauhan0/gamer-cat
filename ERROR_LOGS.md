# Gamer-Cat Error Logs and Technical Resolutions

## 1. Scope
This document captures the Linux/Arch migration incident history for Gamer-Cat, including:
- observed runtime errors
- root cause analysis
- code/config/service-level fixes
- bypasses where a full fix was not possible
- validation steps and residual risk

Date range covered: March 2, 2026 session timeline.

## 2. Environment Snapshot
- OS: EndeavourOS / Arch Linux
- Desktop: KDE Plasma on Wayland
- Python runner: `uv run python src/gamer_cat.py`
- LLM runtime: Ollama (`llama3.2:3b`, `moondream`)
- STT: `faster-whisper` (`tiny.en`)
- TTS candidates: `edge-tts`, `piper`, `pyttsx3`

## 3. Incident Index
| ID | Subsystem | Symptom (Log Signature) | Final Status |
|---|---|---|---|
| INC-001 | Capture | `compositor doesn't support the screen capture protocol` | mitigated by backend selection + portal checks |
| INC-002 | Capture | `import: missing an image filename` | mitigated with backend fallback and tool ordering |
| INC-003 | Capture | `All auto-detected screen capture backends are disabled` | expected safeguard; now explicit diagnostics + fallback |
| INC-004 | Audio | ALSA noise flood (`Unknown PCM`, `unable to open slave`) | mitigated (stderr suppression in app) |
| INC-005 | TTS | `GAMERCAT_TTS_PIPER_MODEL is not set` + pyttsx3 failures | mitigated by backend policy + startup defaults |
| INC-006 | LLM API | `404 ... /api/chat` | fixed with `/api/generate` fallback path |
| INC-007 | STT | wrong language detection (`nn`, `ja`) while speaking English | fixed with English model + language enforcement |
| INC-008 | Vision/Reasoning | Hallucinated game/screen answers | fixed via deterministic screen-answer path + prompt hardening |
| INC-009 | Orchestration | listen/capture/respond/speak race conditions | fixed by serialized turn flow and recorder lock |
| INC-010 | Startup | `sudo bash startup.sh` breaks Wayland/DBus context | fixed by user-session guard and re-exec logic |
| INC-011 | KDE portal | service name mismatch (`plasma-xdg-desktop-portal-kde.service`) | fixed in startup checks and docs |
| INC-012 | UX timing | user unsure when to speak | fixed by explicit `[Listen] Started/Stopped` logs + resume delay |

## 4. Detailed Incidents

### INC-001: Wayland Screen Capture Protocol Failure
Observed logs:
- `compositor doesn't support the screen capture protocol`
- capture loop repeatedly failing in auto mode

Root cause:
- Wayland capture requires compositor/portal-compatible tooling.
- Initial backend/tool combination was not guaranteed to work in the active session.

Fix:
- Added multi-backend capture strategy (`wayland`, `x11`, `pil`) with ordered fallback.
- Added startup diagnostics for missing Wayland capture tools.
- Added portal service hints/checks in startup bootstrap.

Bypass:
- allow explicit backend override via `GAMERCAT_CAPTURE_BACKEND`.

Validation:
- capture now updates context where compatible tools/services exist.
- unsupported backends fail cleanly and report once per unique error.

Residual risk:
- Wayland capture still depends on compositor/session policy.

### INC-002: X11 Import Command Capture Failure
Observed logs:
- `import: missing an image filename '/tmp/tmpXXXX.png' @ error/import.c/ImportImageCommand/1289.`

Root cause:
- X11 fallback tools can fail under Wayland or when no valid root-window path is available.
- tool behavior differs across distros/packaging.

Fix:
- Expanded fallback ordering and backend isolation.
- capture exceptions now surfaced with backend attribution.

Bypass:
- explicit backend pinning to known-good backend (`wayland` or `x11`) for a given host.

Validation:
- backend errors are now actionable (`wayland: ...; x11: ...; pil: ...`).

### INC-003: Auto Backend Disable After Repeated Failures
Observed logs:
- `[AutoCapture] Error: All auto-detected screen capture backends are disabled due to repeated failures.`

Root cause:
- protection logic intentionally suppresses noisy repeated failures.

Fix:
- retained behavior (correct), but improved startup hints and explicit override guidance.

Bypass:
- set `GAMERCAT_CAPTURE_BACKEND` explicitly after installing/repairing capture deps.

Validation:
- once capture path fixed, context updates resumed.

### INC-004: ALSA Error Flood During TTS
Observed logs:
- `ALSA lib pcm_dmix.c:... unable to open slave`
- `Unknown PCM ...`, `Cannot open device /dev/dsp`, etc.

Root cause:
- ALSA probing noise from fallback audio stacks and backend probing paths.
- not always a hard playback failure; often noisy diagnostics from optional devices.

Fix:
- installed ALSA error handler suppression in `voice_engine.py` for Linux.
- added stronger backend fallback logic and local/offline hints.

Bypass:
- use stable playback path (`ffplay`, `pw-play`, `paplay`, or `aplay`).

Validation:
- logs substantially cleaner; actual backend failures now easier to identify.

Residual risk:
- if no real audio sink/player is available, TTS still fails (correct behavior).

### INC-005: TTS Backend Selection and Missing Local Dependencies
Observed logs:
- `[TTS Warning] GAMERCAT_TTS_PIPER_MODEL is not set.`
- pyttsx3/espeak failures (`This means you probably do not have eSpeak or eSpeak-ng installed!`)
- occasional edge playback command failures (`ffplay` exit status)

Root cause:
- local-only path was underconfigured (no Piper model, no espeak fallback).
- backend expectations not explicit at startup.

Fix:
- startup defaults now prefer `edge` for voice quality when `GAMERCAT_LOCAL_ONLY=0`.
- added local runtime hints if local-only mode lacks prerequisites.
- backend fallback chain hardened and warnings clarified.

Bypass:
- for fully local TTS: install `espeak-ng` or configure Piper model (`GAMERCAT_TTS_PIPER_MODEL`).

Validation:
- edge voice (`en-US-AnaNeural`) active in normal path.

Residual risk:
- edge TTS is not fully offline; local-only users must install/point local models.

### INC-006: Ollama Chat Endpoint 404
Observed logs:
- `[AI Error] 404 Client Error: Not Found for url: http://localhost:11434/api/chat`

Root cause:
- endpoint compatibility mismatch for some local runtime/model configurations.

Fix:
- added fallback to `/api/generate` when `/api/chat` returns 404.

Bypass:
- none required post-fix; fallback is automatic.

Validation:
- responses continue even when chat route unavailable.

### INC-007: STT Misclassification (Non-English)
Observed logs:
- `Detected language 'nn' ...`
- `Detected language 'ja' ...` despite English-only use case.

Root cause:
- multilingual small model + short/noisy windows can mis-detect language.

Fix:
- default STT model changed to `tiny.en`.
- forced `GAMERCAT_STT_LANGUAGE=en` and `GAMERCAT_STT_ENFORCE_LANGUAGE=1`.

Bypass:
- adjust `GAMERCAT_STT_LANGUAGE_THRESHOLD` if needed for noisy hardware.

Validation:
- transcript quality improved and off-language transcripts dropped.

### INC-008: Vision/LLM Hallucination About Screen Content
Observed behavior:
- assistant claimed to not see screen despite context updates.
- or invented game details unrelated to actual display.

Root cause:
- prompt and control flow allowed inference beyond reliable context.
- invalid/stale context could still influence generation.

Fix:
- screen-query detector now returns deterministic answer from latest valid context.
- invalid context filtered (`Screen context unavailable`, placeholders, errors).
- prompt hardened: no game/detail invention; no screen mention unless requested.

Bypass:
- none needed; deterministic path handles direct screen questions.

Validation:
- `Can you see my screen?` now maps to explicit current context string.

### INC-009: Race Conditions Between Recording, Capture, and Speech
Observed behavior:
- recording started unexpectedly while TTS still speaking.
- context updates and listening overlapped unpredictably.
- user flow became non-deterministic.

Root cause:
- mixed async threads and timing windows without strict turn ownership.

Fix:
- moved to serialized flow in `gamer_cat.py`: `listen -> capture -> think -> speak`.
- disabled background listening in primary path (`background_listen=False`).
- added recorder mutex (`_record_lock`) and TTS/listen gating.
- added `wait_until_tts_idle()` and resume delay support.

Bypass:
- none; this is structural, not just timing tuning.

Validation:
- runtime logs now show ordered `[Flow]` stages and listen windows.

Residual risk:
- STT processing latency still depends on CPU load (expected).

### INC-010: Startup Script Run as sudo Breaks Desktop Session
Observed logs:
- `[startup] Warning: XDG_RUNTIME_DIR is not set`
- GLib DBus assertions from screenshot tooling
- black/invalid captures during startup path only

Root cause:
- running GUI/session-bound app as root detaches from user DBus/Wayland runtime.

Fix:
- `startup.sh` now detects sudo/root mode and re-execs as desktop user with session vars.
- explicit warning not to run script as root without user context.

Bypass:
- run `./startup.sh` as normal user (recommended).

Validation:
- non-sudo startup path restored functional capture behavior.

### INC-011: KDE Portal Unit Name Mismatch
Observed behavior:
- confusion between alias and real systemd unit names.

Root cause:
- KDE service unit is `plasma-xdg-desktop-portal-kde.service`; alias handling is distro-specific.

Fix:
- startup checks/restarts target actual KDE unit name.
- docs updated with correct service naming guidance.

Bypass:
- manage real unit directly:
  - `systemctl --user restart plasma-xdg-desktop-portal-kde.service`

Validation:
- portal service checks now align with actual unit naming on Arch/KDE.

### INC-012: User Timing Confusion During Turn Taking
Observed behavior:
- unclear moment to speak due backend delay.

Fix:
- explicit logs added:
  - `[Listen] Started recording user input (...)`
  - `[Listen] Stopped recording user input.`
- default `GAMERCAT_LISTEN_DURATION=15` and `GAMERCAT_LISTEN_RESUME_DELAY=15`.

Validation:
- turn boundaries visible in console.

## 5. Configuration Baseline After Fixes
Recommended runtime baseline:
```bash
export GAMERCAT_LLM_MODEL="llama3.2:3b"
export GAMERCAT_VISION_MODEL="moondream"

export GAMERCAT_STT_MODEL="tiny.en"
export GAMERCAT_STT_LANGUAGE="en"
export GAMERCAT_STT_ENFORCE_LANGUAGE="1"

export GAMERCAT_TTS_BACKEND="edge"
export GAMERCAT_TTS_VOICE="en-US-AnaNeural"
export GAMERCAT_TTS_RATE="+10%"
export GAMERCAT_TTS_PITCH="+12Hz"

export GAMERCAT_LISTEN_DURATION="15"
export GAMERCAT_LISTEN_RESUME_DELAY="15"

export GAMERCAT_CAPTURE_BACKEND="auto"
```

Offline-first alternative (fully local TTS):
```bash
export GAMERCAT_LOCAL_ONLY="1"
export GAMERCAT_TTS_BACKEND="piper"
export GAMERCAT_TTS_PIPER_MODEL="/abs/path/to/en_US-lessac-medium.onnx"
```

## 6. Operational Checks (Post-Reboot)
1. Start services and app:
```bash
./startup.sh
```
2. Confirm portal units in user session:
```bash
systemctl --user is-active xdg-desktop-portal.service
systemctl --user is-active plasma-xdg-desktop-portal-kde.service
```
3. Confirm Ollama models:
```bash
ollama list
```
4. Verify turn flow in logs (expected order):
- `[Flow] Waiting for user input...`
- `[Listen] Started...`
- `[Listen] Stopped...`
- `User (Recognized): ...`
- `[Flow] Refreshing screen context before response...`
- `[Flow] Generating response...`
- `[Flow] Speaking response...`

## 7. Known Non-Fatal Warnings
- Hugging Face warning about unauthenticated requests (`HF_TOKEN`) during first STT model fetch.
  - impact: slower downloads/rate-limit risk
  - not required for core functionality once model is cached

## 8. Residual Risks and Next Hardening Items
- Add explicit end-to-end integration test for strict turn ordering under simulated latency.
- Add metric timestamps to each `[Flow]` stage to quantify latency per phase.
- Add optional push-to-talk mode for deterministic user control in noisy rooms.
- Add startup probe for audio sink readiness before first TTS.

## 9. Changelog Linkage
Primary files touched across the incident response:
- `src/gamer_cat.py`
- `src/voice_engine.py`
- `src/screen_capture.py`
- `src/vision_engine.py`
- `src/mcp_server.py`
- `startup.sh`
- `README.md`
- `DOCUMENTATION.md`

