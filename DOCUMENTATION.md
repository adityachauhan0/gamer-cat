# Gamer-Cat Technical Documentation

## 1. System Overview
Gamer-Cat is a local-first, real-time game companion that combines:
- screen capture
- vision summarization
- speech-to-text
- local LLM response generation
- text-to-speech playback

Primary runtime target is Arch Linux (Wayland-first, X11 fallback), with Windows compatibility retained.

## 2. High-Level Architecture
```mermaid
flowchart LR
    U[User] -->|Voice input| VE[Voice Engine]
    VE -->|Transcript| GC[GamerCat Orchestrator]
    GC -->|Chat request| OLLC[Ollama Chat API /api/chat]
    OLLC -->|Assistant reply| GC
    GC -->|Speak queue| VE
    SC[Screen Capture] --> VISION[Vision Engine]
    VISION -->|Screen description| MCP[MCP Context Store]
    MCP -->|current_context| GC
    MCP -->|Tool get_screen_context| CLIENT[MCP Client]
    VE -->|Audio output| U
```

## 3. Runtime Sequence
```mermaid
sequenceDiagram
    participant User
    participant Voice as VoiceEngine
    participant Main as gamer_cat.py
    participant Capture as auto_capture_loop
    participant Vision as vision_engine.py
    participant Ollama as Ollama

    Note over Capture: Every ~10s
    Capture->>Vision: capture_screen() -> describe_image()
    Vision->>Ollama: POST /api/generate (moondream)
    Ollama-->>Vision: 45-60 word description
    Vision-->>Capture: description
    Capture->>Main: update current_context (locked)

    loop Main loop (~10Hz)
      Voice->>Main: poll_transcript()
      alt transcript exists
        Main->>Ollama: POST /api/chat (llama3.2:3b, non-stream)
        Ollama-->>Main: response text
        Main->>Voice: speak(response)
      else context changed + cooldown + random trigger
        Main->>Ollama: proactive comment prompt
        Ollama-->>Main: response text
        Main->>Voice: speak(response)
      end
    end
```

## 4. Module Responsibilities
| Module | Responsibility | Notes |
|---|---|---|
| `src/screen_capture.py` | Captures primary screen and returns base64 JPEG | JPEG quality set to `80` |
| `src/vision_engine.py` | Sends screenshot to Ollama vision endpoint | Uses `moondream`, low temperature, capped tokens |
| `src/mcp_server.py` | Maintains shared context + MCP tool exposure | `context_lock` protects shared state |
| `src/gamer_cat.py` | Main orchestration loop | Manages history, proactive logic, LLM calls |
| `src/voice_engine.py` | STT + TTS backend manager | Background listening and queued speech |

## 5. Concurrency Model
### Active Threads
- Main thread: orchestration loop in `gamer_cat.py`
- Capture thread: `auto_capture_loop()` updates screen context
- TTS thread: queue consumer in `VoiceEngine._tts_worker()`
- Listener thread (optional, enabled by default): `VoiceEngine._listen_worker()`

### Shared-State Safety
- `mcp_server.current_context` is guarded by `context_lock` for read/write consistency.
- Transcript flow uses a bounded queue (`maxsize=2`) to avoid unbounded memory growth.

## 6. Core Data Contracts
### Screen context
`mcp_server.current_context`:
```python
{
  "description": str,
  "timestamp": float
}
```

### LLM context memory
- `gamer_cat.py` keeps `screen_history = deque(maxlen=3)`.
- History is appended only when the description changes and is not placeholder text.

### STT acceptance criteria
- Transcript accepted only if:
  - text is non-empty
  - `info.language_probability > 0.4`

## 7. External Interfaces
### Ollama Chat API
- Endpoint: `http://localhost:11434/api/chat`
- Model: `llama3.2:3b` (override with `GAMERCAT_LLM_MODEL`)
- Streaming: disabled (`stream: false`)

### Ollama Vision API
- Endpoint: `http://localhost:11434/api/generate`
- Model: `moondream`
- Prompt target: concrete visual details, 45-60 words
- Options:
  - `temperature: 0.1`
  - `num_predict: 120`

### MCP Tool
- Tool name: `get_screen_context`
- Returns: age + latest context description string

## 8. Voice Pipeline and Backend Selection
### STT
- Engine: `faster-whisper` (`tiny`, CPU `int8`)
- Input: 16kHz mono PCM chunks from PyAudio

### TTS backends
Configured via `GAMERCAT_TTS_BACKEND`:
- `piper`: offline neural (requires explicit model path)
- `edge`: edge-tts neural voice
- `powershell`: Windows `System.Speech`
- `pyttsx3`: local platform TTS fallback
- `auto`: selection chain below

Auto selection order:
1. `piper` (preferred for local/offline voice; requires `GAMERCAT_TTS_PIPER_MODEL`)
2. `edge-tts` (only when `GAMERCAT_LOCAL_ONLY=0`)
3. PowerShell `System.Speech` (Windows only)
4. `pyttsx3`

### Screen capture backends
Configured via `GAMERCAT_CAPTURE_BACKEND`:
- `wayland`: uses external capture tools (`grim` or `gnome-screenshot`)
- `x11`: uses `maim`, `import`, or `scrot`
- `pil`: Pillow `ImageGrab` fallback
- `auto`: chooses by session type (`wayland -> x11 -> pil`, `x11 -> pil -> wayland`)

## 9. Configuration Reference
| Variable | Purpose | Default |
|---|---|---|
| `GAMERCAT_TTS_BACKEND` | Force TTS backend (`auto`, `edge`, `piper`, `powershell`, `pyttsx3`) | `edge` |
| `GAMERCAT_LOCAL_ONLY` | Disable cloud-backed TTS backends (`1` = local-only) | `0` |
| `GAMERCAT_TTS_VOICE` | edge-tts voice id | `en-US-AnaNeural` |
| `GAMERCAT_TTS_RATE` | edge-tts speaking rate | `+10%` |
| `GAMERCAT_TTS_PITCH` | edge-tts pitch | `+12Hz` |
| `GAMERCAT_STT_MODEL` | faster-whisper model name | `tiny.en` |
| `GAMERCAT_STT_LANGUAGE` | STT language code | `en` |
| `GAMERCAT_STT_ENFORCE_LANGUAGE` | drop transcripts not matching `GAMERCAT_STT_LANGUAGE` (`1`/`0`) | `1` |
| `GAMERCAT_STT_LANGUAGE_THRESHOLD` | minimum language confidence for transcript acceptance | `0.4` |
| `GAMERCAT_LISTEN_DURATION` | Duration of each listening window in seconds | `15` |
| `GAMERCAT_LISTEN_RESUME_DELAY` | Delay after assistant speech before recording resumes (seconds) | `15` |
| `GAMERCAT_PROACTIVE_ENABLED` | Enable unsolicited proactive comments (`1`/`0`) | `0` |
| `GAMERCAT_TTS_PIPER_EXE` | Piper executable path | `piper` |
| `GAMERCAT_TTS_PIPER_MODEL` | Piper model `.onnx` path | empty |
| `GAMERCAT_TTS_PIPER_CONFIG` | Piper `.json` config path | empty |
| `GAMERCAT_TTS_PIPER_LENGTH_SCALE` | Piper speed/length control | `0.95` |
| `GAMERCAT_LLM_MODEL` | Ollama chat model name | `llama3.2:3b` |
| `GAMERCAT_VISION_MODEL` | Ollama vision model name | `moondream` |
| `GAMERCAT_CAPTURE_BACKEND` | Capture backend (`auto`, `wayland`, `x11`, `pil`) | `auto` |
| `GAMERCAT_ALLOW_X11_ON_WAYLAND` | Try X11 fallback after Wayland failure (`1` to enable) | unset |

## 10. Build, Setup, and Run
### Prerequisites
- Arch Linux
- Ollama installed
- `ffmpeg`/`ffplay` available on PATH
- `portaudio` + running PipeWire stack (`pipewire`, `wireplumber`)
- Screen capture tooling (`grim` recommended for Wayland)
- `espeak-ng` for local `pyttsx3` fallback
- Wayland portal services (`xdg-desktop-portal` + desktop portal backend, for example `xdg-desktop-portal-kde`)
  - KDE/Plasma systemd unit: `plasma-xdg-desktop-portal-kde.service`
- `uv` installed

### Model setup
```bash
ollama pull moondream
ollama pull llama3.2:3b
```

### Python env setup
```bash
uv sync
```

### Run
```bash
ollama serve
uv run python src/gamer_cat.py
```

### Fresh reboot run
```bash
./startup.sh
```
Run it as your normal desktop user (no `sudo`).

Startup bootstrap behavior:
- sets defaults for unset `GAMERCAT_*` runtime variables
- attempts to start `ollama serve` if Ollama is not reachable
- attempts to pull missing required models (`GAMERCAT_LLM_MODEL`, `GAMERCAT_VISION_MODEL`)

### Recommended anime voice preset (shell)
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

## 11. Operational Behavior
### Main loop cadence
- Main loop sleeps `0.1s` each cycle (~10Hz scheduling).
- Background screen capture updates every `10s`.

### Proactive comment logic
- Requires context change.
- Enforces 30s cooldown since last AI response.
- Random gate (`random.random() > 0.5`).

## 12. Observability
Important log prefixes:
- `[AutoCapture]` screen updates/errors
- `[AI Thinking]`, `[AI Responded]`, `[AI Error]`
- `[TTS Warning]`, `[TTS Worker Error]`
- `[Listen Error]`
- `[History Updated]`

## 13. Failure Modes and Recovery
| Symptom | Likely Cause | Mitigation |
|---|---|---|
| No AI replies | Ollama unavailable | verify `ollama serve`, model pulls, localhost access |
| Silent speech | TTS backend failure/device routing | force backend to `piper` or `edge`; verify `ffplay`/`aplay` |
| Repeated STT mis-detection | ambient noise/language detection variance | improve mic quality, adjust capture duration, tune threshold |
| Empty screen context | capture/vision request failure | inspect `[AutoCapture]` logs, set `GAMERCAT_CAPTURE_BACKEND`, verify `grim`/`maim` |
| High CPU usage | continuous STT + model inference | increase listen interval, lower proactive frequency, use smaller models |

## 14. Security and Privacy Posture
- No required cloud API keys for core operation.
- Primary inference endpoints are local Ollama HTTP services.
- Speech and screen data remain local unless optional third-party backends are chosen.
- `edge-tts` may involve network usage depending on backend implementation; use `piper` for fully offline TTS.

## 15. Repository Layout
```text
gamer-cat/
  assets/
    banners/
    source-images/
  docs/                 # GitHub Pages site
  notes/                # planning and session notes
  src/
    gamer_cat.py
    mcp_server.py
    screen_capture.py
    vision_engine.py
    voice_engine.py
  tests/
  DOCUMENTATION.md
  README.md
  HANDOFF.md
  pyproject.toml
  uv.lock
```

## 16. Known Gaps
- Limited automated test coverage for orchestration and concurrency behavior.
- No formal config validation layer for environment variables.
- No structured metrics export (only console logs).

## 17. Suggested Next Improvements
- Add integration tests with mock Ollama endpoints.
- Add configurable YAML/TOML runtime config file.
- Add structured logging with log levels and optional JSON output.
- Add watchdog/health endpoint for long-running sessions.
