# Session Log - 2026-03-02

## Repo State
- Repository: `adityachauhan0/gamer-cat`
- Active branch: `linux`
- Remote default branch: `linux`
- Current HEAD: `4783833` (`Add technical error log and mitigation summary`)
- Working tree: clean

## What Was Done This Session

### 1. Linux/Arch Runtime Hardening
- Added startup bootstrap in app to set sane defaults for Linux runtime.
- Added Ollama startup + required model checks (`llama3.2:3b`, `moondream`).
- Added local runtime hints for missing portal/capture/audio prerequisites.

### 2. Model and Language Configuration
- Switched default LLM model to `llama3.2:3b`.
- Set English-only STT defaults:
  - `GAMERCAT_STT_MODEL=tiny.en`
  - `GAMERCAT_STT_LANGUAGE=en`
  - `GAMERCAT_STT_ENFORCE_LANGUAGE=1`
- Set anime-style English TTS defaults:
  - `GAMERCAT_TTS_BACKEND=edge`
  - `GAMERCAT_TTS_VOICE=en-US-AnaNeural`
  - `GAMERCAT_TTS_RATE=+10%`
  - `GAMERCAT_TTS_PITCH=+12Hz`

### 3. Capture + Vision Reliability
- Improved capture backend fallback strategy and diagnostics.
- Added Wayland/KDE portal handling guidance and checks.
- Improved vision prompt behavior and empty-response handling.
- Added deterministic answer path for direct screen questions (uses latest valid context, avoids hallucination).

### 4. TTS/STT Flow and Concurrency Fixes
- Added explicit listen logs:
  - `[Listen] Started recording user input (...)`
  - `[Listen] Stopped recording user input.`
- Added configurable post-speech resume delay:
  - `GAMERCAT_LISTEN_RESUME_DELAY` (set to `15` by default).
- Reworked main orchestration to serialized turn flow:
  - `listen -> refresh screen context -> generate -> speak`
- Disabled background listener in main path to avoid overlapping record cycles.
- Added hard recorder mutex lock in `VoiceEngine` to prevent parallel recording paths.
- Added TTS busy/cooldown gating before each listen cycle.

### 5. Startup Script for Fresh Reboot
- Added `startup.sh` with:
  - user-session safety (avoid broken `sudo` DBus/Wayland context)
  - portal user-service checks/restarts
  - dependency sync (`uv sync`)
  - Ollama/model bootstrap
  - launch command
- Confirmed expected invocation: run as normal user (`./startup.sh`), not `sudo`.

### 6. Documentation and Postmortem
- Updated `README.md` and `DOCUMENTATION.md` to match Linux runtime and defaults.
- Added detailed incident postmortem:
  - `ERROR_LOGS.md` (root causes, fixes, bypasses, validation, residual risks).

## Important Commits (linux branch)
- `5614b9b` Improve Linux runtime flow, startup, and capture/TTS stability
- `4783833` Add technical error log and mitigation summary

## Branch and Remote Actions Completed
- Created/pushed branch: `linux`
- Set GitHub default branch to: `linux`
- Updated local remote HEAD:
  - `origin/HEAD -> origin/linux`

## Current Runtime Behavior (Expected)
1. App starts and speaks greeting.
2. Waits for TTS idle + resume delay.
3. Logs waiting and starts recording.
4. Stops recording and transcribes.
5. Captures fresh screen context.
6. Generates response.
7. Speaks response.
8. Repeats.

## Open Notes / Residual Risks
- STT still incurs natural inference latency on CPU; this is expected.
- If fully local/offline TTS is required, configure Piper model and set `GAMERCAT_LOCAL_ONLY=1`.
- Wayland capture remains dependent on active compositor/portal permissions and installed tools.

## Fast Resume Checklist for Next Agent
1. Verify branch and cleanliness:
   - `git branch --show-current`
   - `git status --short --branch`
2. Start runtime:
   - `./startup.sh`
3. If diagnosing turn order, watch for these log markers:
   - `[Flow] Waiting for user input...`
   - `[Listen] Started...`
   - `[Listen] Stopped...`
   - `[Flow] Refreshing screen context before response...`
   - `[Flow] Generating response...`
   - `[Flow] Speaking response...`
4. For historical context, read:
   - `ERROR_LOGS.md`
   - `DOCUMENTATION.md`

