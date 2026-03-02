from collections import deque
import os
import re
import shutil
import subprocess
import time

import requests

from mcp_server import context_lock, current_context
from screen_capture import capture_screen
from vision_engine import describe_image
from voice_engine import VoiceEngine

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
DEFAULT_LLM_MODEL = "llama3.2:3b"
DEFAULT_VISION_MODEL = "moondream"
SCREEN_CONTEXT_UNAVAILABLE = "Screen context unavailable."

# Memory for screen descriptions (last 3)
screen_history = deque(maxlen=3)


def _is_valid_screen_context(desc):
    if not desc:
        return False
    cleaned = desc.strip()
    if not cleaned:
        return False
    lowered = cleaned.lower()
    if lowered == "nothing yet...":
        return False
    if lowered.startswith("screen context unavailable"):
        return False
    if lowered.startswith("error connecting to ollama"):
        return False
    return True


def _looks_like_screen_query(user_text):
    lowered = user_text.lower()
    keywords = [
        "screen",
        "see",
        "what do you see",
        "what is on",
        "what's on",
        "look at",
        "visible",
    ]
    return any(keyword in lowered for keyword in keywords)


def _normalize_context_key(desc):
    lowered = desc.strip().lower()
    lowered = lowered.replace('"', "").replace("'", "")
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return " ".join(lowered.split())


def _set_default_env():
    defaults = {
        "GAMERCAT_LLM_MODEL": DEFAULT_LLM_MODEL,
        "GAMERCAT_VISION_MODEL": DEFAULT_VISION_MODEL,
        "GAMERCAT_TTS_BACKEND": "edge",
        "GAMERCAT_TTS_VOICE": "en-US-AnaNeural",
        "GAMERCAT_TTS_RATE": "+10%",
        "GAMERCAT_TTS_PITCH": "+12Hz",
        "GAMERCAT_STT_MODEL": "tiny.en",
        "GAMERCAT_STT_LANGUAGE": "en",
        "GAMERCAT_STT_ENFORCE_LANGUAGE": "1",
        "GAMERCAT_LISTEN_DURATION": "15",
        "GAMERCAT_LISTEN_RESUME_DELAY": "15",
        "GAMERCAT_PROACTIVE_ENABLED": "0",
        "GAMERCAT_LOCAL_ONLY": "0",
        "GAMERCAT_CAPTURE_BACKEND": "auto",
    }
    for key, value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = value
            print(f"[Startup] Using default {key}={value}")


def _wait_for_ollama(max_wait=20):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            response = requests.get(OLLAMA_TAGS_URL, timeout=2)
            response.raise_for_status()
            return True
        except Exception:
            time.sleep(1)
    return False


def _ensure_ollama_running():
    if _wait_for_ollama(max_wait=1):
        return True
    if shutil.which("ollama") is None:
        print("[Startup] 'ollama' command not found on PATH.")
        return False

    print("[Startup] Ollama not reachable, starting 'ollama serve'...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return _wait_for_ollama(max_wait=20)


def _ensure_required_models():
    llm_model = os.getenv("GAMERCAT_LLM_MODEL", DEFAULT_LLM_MODEL)
    vision_model = os.getenv("GAMERCAT_VISION_MODEL", DEFAULT_VISION_MODEL)
    required_models = [llm_model, vision_model]

    try:
        tags = requests.get(OLLAMA_TAGS_URL, timeout=5).json().get("models", [])
        installed = {item.get("name", "") for item in tags}
    except Exception as err:
        print(f"[Startup] Could not query installed Ollama models: {err}")
        return

    def is_installed(model_name):
        if model_name in installed:
            return True
        if ":" not in model_name and f"{model_name}:latest" in installed:
            return True
        if model_name.endswith(":latest") and model_name.split(":", 1)[0] in installed:
            return True
        return False

    for model in required_models:
        if is_installed(model):
            continue
        print(f"[Startup] Pulling missing model: {model}")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
        except Exception as err:
            print(f"[Startup] Failed to pull model '{model}': {err}")


def _print_local_runtime_hints():
    def user_service_active(service_name):
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", service_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    local_only = os.getenv("GAMERCAT_LOCAL_ONLY", "1").strip() != "0"
    tts_backend = os.getenv("GAMERCAT_TTS_BACKEND", "auto").strip().lower()
    piper_model = os.getenv("GAMERCAT_TTS_PIPER_MODEL", "").strip()
    piper_exe = os.getenv("GAMERCAT_TTS_PIPER_EXE", "piper").strip()
    if local_only and tts_backend in {"auto", "pyttsx3", "piper"}:
        has_espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        has_piper = bool(piper_model) and (
            shutil.which(piper_exe) or os.path.exists(piper_exe)
        )
        if not has_espeak and not has_piper:
            print(
                "[Startup] Local TTS prerequisites missing. Install `espeak-ng` "
                "or set GAMERCAT_TTS_PIPER_MODEL with a Piper voice model."
            )

    capture_backend = os.getenv("GAMERCAT_CAPTURE_BACKEND", "auto").strip().lower()
    is_wayland = os.getenv("XDG_SESSION_TYPE", "").strip().lower() == "wayland" or bool(
        os.getenv("WAYLAND_DISPLAY")
    )
    if capture_backend in {"auto", "wayland"} and is_wayland:
        if not any(shutil.which(cmd) for cmd in ("spectacle", "gnome-screenshot", "grim")):
            print("[Startup] No Wayland capture tools found. Install spectacle, gnome-screenshot, or grim.")
        portal_service_active = user_service_active("xdg-desktop-portal.service")
        kde_portal_active = user_service_active("plasma-xdg-desktop-portal-kde.service")
        if not portal_service_active and not kde_portal_active and not shutil.which("xdg-desktop-portal"):
            print(
                "[Startup] xdg-desktop-portal not found. Wayland capture permissions may fail without portal services."
            )


def bootstrap_runtime():
    _set_default_env()
    _print_local_runtime_hints()
    if not _ensure_ollama_running():
        print("[Startup] Ollama unavailable. AI responses may fail until Ollama is running.")
        return
    _ensure_required_models()


def get_ai_response(user_input, history, proactive=False):
    """Gets a chat response from Ollama considering the screen history."""
    valid_history = [desc for desc in history if _is_valid_screen_context(desc)]
    if proactive and not valid_history:
        return ""
    screen_query = bool(user_input and _looks_like_screen_query(user_input))
    if screen_query:
        if not valid_history:
            return "I cannot read your screen yet. Please fix capture, then ask me again."
        latest = valid_history[-1].strip()
        if len(latest) > 260:
            latest = latest[:257].rstrip() + "..."
        return f"I can see this on your screen: {latest}"

    context_str = (
        "\n".join([f"- {desc}" for desc in valid_history])
        if proactive
        else f"- {SCREEN_CONTEXT_UNAVAILABLE}"
    )

    system_prompt = (
        "You are 'GamerCat', a supportive, witty, and observant AI gaming buddy. "
        "You speak in short, punchy sentences. Maximum 2 sentences per response. "
        "Use the provided screen history only when relevant. "
        "If screen context is unavailable, explicitly say you cannot currently see the screen and do not invent details. "
        "If the user did not ask about the screen, do not mention or infer any visual/game details. "
        "Never invent game names, modes, or events that are not explicitly provided. "
        "Avoid stage directions and quotes around your own speech. "
        "If the context includes concrete game state (like chess piece squares, move list, clocks, inventory counts, or scores), reference those details. "
        "You are offline, local, and slightly snarky but always a good friend."
    )

    if proactive:
        prompt = f"Recent screen events:\n{context_str}\n\nComment on what you see happening right now without being asked."
    else:
        prompt = f"Recent screen events:\n{context_str}\n\nUser says: '{user_input}'"

    llm_model = os.getenv("GAMERCAT_LLM_MODEL", DEFAULT_LLM_MODEL)
    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    try:
        print(f"[AI Thinking] Requesting response for: {user_input if not proactive else 'Proactive'}")
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=20)
        if response.status_code == 404:
            fallback_payload = {
                "model": llm_model,
                "prompt": f"{system_prompt}\n\n{prompt}",
                "stream": False,
            }
            response = requests.post(OLLAMA_GENERATE_URL, json=fallback_payload, timeout=20)
            response.raise_for_status()
            content = response.json().get("response", "Meow? I lost my train of thought.")
        else:
            response.raise_for_status()
            content = response.json().get("message", {}).get("content", "Meow? I lost my train of thought.")
        print(f"[AI Responded] {content}")
        return content
    except Exception as e:
        print(f"[AI Error] {str(e)}")
        return f"Brain freeze! {str(e)}"


def refresh_screen_context():
    try:
        image_b64 = capture_screen()
        desc = (describe_image(image_b64) or "").strip() or SCREEN_CONTEXT_UNAVAILABLE
    except Exception as err:
        desc = f"{SCREEN_CONTEXT_UNAVAILABLE}: {err}"

    with context_lock:
        current_context["description"] = desc
        current_context["timestamp"] = time.time()

    print(f"[AutoCapture] Screen context updated: {desc}")
    return desc


def main():
    print("--- GamerCat: The Buddy is Online ---")
    voice = VoiceEngine(background_listen=False, listen_duration=15)
    voice.speak("Gamer Cat is in the house! What's the plan for today?")
    voice.wait_until_tts_idle()

    last_processed_desc = ""
    last_processed_desc_key = ""

    while True:
        try:
            if voice.is_listening():
                time.sleep(0.05)
                continue

            if voice.is_tts_busy():
                time.sleep(0.1)
                continue

            cooldown = voice.listen_cooldown_remaining()
            if cooldown > 0:
                time.sleep(min(0.5, cooldown))
                continue

            print("[Flow] Waiting for user input...")
            user_text = voice.listen(duration=voice.listen_duration)
            if not user_text or len(user_text.strip()) <= 1:
                time.sleep(0.1)
                continue

            print(f"User (Recognized): {user_text}")

            print("[Flow] Refreshing screen context before response...")
            current_desc = refresh_screen_context()
            current_desc_key = _normalize_context_key(current_desc) if _is_valid_screen_context(current_desc) else ""
            if (
                _is_valid_screen_context(current_desc)
                and current_desc != last_processed_desc
                and current_desc_key
                and current_desc_key != last_processed_desc_key
            ):
                screen_history.append(current_desc)
                last_processed_desc = current_desc
                last_processed_desc_key = current_desc_key
                print(f"[History Updated] {current_desc}")

            print("[Flow] Generating response...")
            response = get_ai_response(user_text, list(screen_history))
            if response:
                print("[Flow] Speaking response...")
                voice.speak(response)
                voice.wait_until_tts_idle()

        except KeyboardInterrupt:
            print("\nGamerCat is taking a nap. Catch ya later!")
            voice.close()
            break
        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    bootstrap_runtime()
    main()
