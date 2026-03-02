#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

log() {
  printf '[startup] %s\n' "$*"
}

if [[ "${EUID}" -eq 0 ]]; then
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    TARGET_USER="${SUDO_USER}"
    TARGET_UID="$(id -u "${TARGET_USER}")"
    TARGET_HOME="$(getent passwd "${TARGET_USER}" | cut -d: -f6)"
    TARGET_XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/${TARGET_UID}}"
    TARGET_DBUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=${TARGET_XDG_RUNTIME_DIR}/bus}"

    log "Detected sudo/root launch; re-running as ${TARGET_USER} for desktop session access."
    exec sudo -u "${TARGET_USER}" -H env \
      HOME="${TARGET_HOME}" \
      USER="${TARGET_USER}" \
      LOGNAME="${TARGET_USER}" \
      XDG_RUNTIME_DIR="${TARGET_XDG_RUNTIME_DIR}" \
      DBUS_SESSION_BUS_ADDRESS="${TARGET_DBUS_ADDRESS}" \
      DISPLAY="${DISPLAY:-}" \
      WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
      bash "$0" "$@"
  fi

  log "Do not run startup.sh as root. Run it as your desktop user."
  exit 1
fi

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "Missing required command: $cmd"
    exit 1
  fi
}

wait_for_ollama() {
  local retries=30
  local i
  for ((i=1; i<=retries; i++)); do
    if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

start_user_service_if_present() {
  local service="$1"
  if ! command -v systemctl >/dev/null 2>&1; then
    return 0
  fi
  if systemctl --user cat "$service" >/dev/null 2>&1; then
    systemctl --user start "$service" >/dev/null 2>&1 || true
    log "Ensured user service: $service"
  fi
}

require_cmd uv
require_cmd ollama
require_cmd curl

if [[ -z "${XDG_RUNTIME_DIR:-}" ]]; then
  log "Warning: XDG_RUNTIME_DIR is not set; user services may not be reachable."
fi

start_user_service_if_present "xdg-desktop-portal.service"
start_user_service_if_present "plasma-xdg-desktop-portal-kde.service"

export GAMERCAT_LLM_MODEL="${GAMERCAT_LLM_MODEL:-llama3.2:3b}"
export GAMERCAT_VISION_MODEL="${GAMERCAT_VISION_MODEL:-moondream}"
export GAMERCAT_TTS_BACKEND="${GAMERCAT_TTS_BACKEND:-edge}"
export GAMERCAT_TTS_VOICE="${GAMERCAT_TTS_VOICE:-en-US-AnaNeural}"
export GAMERCAT_TTS_RATE="${GAMERCAT_TTS_RATE:-+10%}"
export GAMERCAT_TTS_PITCH="${GAMERCAT_TTS_PITCH:-+12Hz}"
export GAMERCAT_STT_MODEL="${GAMERCAT_STT_MODEL:-tiny.en}"
export GAMERCAT_STT_LANGUAGE="${GAMERCAT_STT_LANGUAGE:-en}"
export GAMERCAT_STT_ENFORCE_LANGUAGE="${GAMERCAT_STT_ENFORCE_LANGUAGE:-1}"
export GAMERCAT_LISTEN_DURATION="${GAMERCAT_LISTEN_DURATION:-15}"
export GAMERCAT_LISTEN_RESUME_DELAY="${GAMERCAT_LISTEN_RESUME_DELAY:-15}"
export GAMERCAT_LOCAL_ONLY="${GAMERCAT_LOCAL_ONLY:-0}"
export GAMERCAT_CAPTURE_BACKEND="${GAMERCAT_CAPTURE_BACKEND:-auto}"

if ! wait_for_ollama; then
  log "Starting Ollama service..."
  nohup ollama serve >/tmp/gamercat-ollama.log 2>&1 &
  if ! wait_for_ollama; then
    log "Ollama did not become ready. See /tmp/gamercat-ollama.log"
    exit 1
  fi
fi

for model in "$GAMERCAT_LLM_MODEL" "$GAMERCAT_VISION_MODEL"; do
  if ! ollama show "$model" >/dev/null 2>&1; then
    log "Pulling missing model: $model"
    ollama pull "$model"
  fi
done

log "Syncing Python dependencies..."
uv sync

log "Launching GamerCat..."
exec uv run python src/gamer_cat.py
