#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
STATE_DIR="$ROOT_DIR/.omnidev-macos"
BACKEND_PORT="${OMNIDEV_BACKEND_PORT:-8000}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/opt/anaconda3/bin:/usr/bin:/bin:/usr/sbin:/sbin"

mkdir -p "$STATE_DIR"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$STATE_DIR/launcher.log"
}

is_http_up() {
  curl -fsS "$1" >/dev/null 2>&1
}

port_is_listening() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

python_bin() {
  local candidates=()
  if [[ -n "${OMNIDEV_PYTHON:-}" ]]; then
    candidates+=("$OMNIDEV_PYTHON")
  fi
  candidates+=(
    "$ROOT_DIR/backend/.venv/bin/python"
    "/opt/anaconda3/bin/python3"
    "$(command -v python3 || true)"
  )

  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" && -x "$candidate" ]] || continue
    if python_is_usable "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
    log "Skipping unusable Python candidate: $candidate"
  done

  log "No usable Python interpreter found"
  return 1
}

python_is_usable() {
  local candidate="$1"
  (
    cd "$ROOT_DIR/backend"
    "$candidate" -c 'import app.main' >/dev/null 2>&1
  ) &
  local pid="$!"

  # Cold imports (playwright, boto3, google-genai) can take >5s on first
  # launch or under load — probe for up to 15s before skipping a candidate.
  for _ in $(seq 1 60); do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      wait "$pid"
      return "$?"
    fi
    sleep 0.25
  done

  kill "$pid" >/dev/null 2>&1 || true
  wait "$pid" >/dev/null 2>&1 || true
  return 1
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local max_attempts="${3:-90}"

  for _ in $(seq 1 "$max_attempts"); do
    if is_http_up "$url"; then
      log "$label is ready at $url"
      return 0
    fi
    sleep 1
  done

  log "$label did not become ready at $url"
  return 1
}


best_system_python() {
  local candidates=()
  if [[ -n "${OMNIDEV_PYTHON:-}" ]]; then
    candidates+=("$OMNIDEV_PYTHON")
  fi
  candidates+=(
    /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3
    /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/local/bin/python3.11 /usr/local/bin/python3
    /opt/anaconda3/bin/python3
    "$(command -v python3 || true)"
  )
  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" && -x "$candidate" ]] || continue
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

ensure_venv() {
  # Some Python that can already import the app means deps are installed.
  if python_bin >/dev/null 2>&1; then
    return 0
  fi

  log "No usable engine Python — bootstrapping backend/.venv (first run can take a few minutes)"
  local sys_py
  if ! sys_py="$(best_system_python)"; then
    log "No Python 3.11+ found. Install one (brew install python) and relaunch OmniDev."
    return 1
  fi
  log "Bootstrap Python: $sys_py"
  rm -rf "$ROOT_DIR/backend/.venv"
  {
    "$sys_py" -m venv "$ROOT_DIR/backend/.venv"
    "$ROOT_DIR/backend/.venv/bin/pip" install --upgrade pip
    "$ROOT_DIR/backend/.venv/bin/pip" install -r "$ROOT_DIR/backend/requirements.txt"
  } >> "$STATE_DIR/bootstrap.log" 2>&1
  if ! "$ROOT_DIR/backend/.venv/bin/python" -m playwright install chromium >> "$STATE_DIR/bootstrap.log" 2>&1; then
    log "Playwright Chromium install failed; the scraper will return 503 until it succeeds"
  fi
  log "Engine bootstrap complete"
}

# Fingerprint the settings-derived env so a healthy backend from a previous
# launch is reused only when it was started with the same configuration.
env_fingerprint() {
  printf '%s|%s|%s|%s|%s|%s|%s' \
    "$BACKEND_PORT" "${AI_PROVIDER:-}" "${DEVOPS_READ_ONLY:-}" \
    "${OLLAMA_MODEL:-}" "${OLLAMA_VISION_MODEL:-}" \
    "${GEMINI_API_KEY:-}" "${AWS_ACCESS_KEY_ID:-}" \
    | shasum -a 256 | cut -d' ' -f1
}

start_backend() {
  if is_http_up "$BACKEND_URL/health"; then
    local fp_file="$STATE_DIR/backend.env-fingerprint"
    if [[ ! -f "$fp_file" || "$(cat "$fp_file")" == "$(env_fingerprint)" ]]; then
      log "Backend already healthy at $BACKEND_URL"
      return 0
    fi
    log "Backend healthy but launched with different settings — restarting it"
    "$ROOT_DIR/scripts/macos/stop-omnidev.sh" "$ROOT_DIR" >/dev/null 2>&1 || true
    sleep 1
  fi

  if port_is_listening "$BACKEND_PORT"; then
    log "Backend port $BACKEND_PORT is already in use but /health is not healthy"
    return 1
  fi

  log "Starting backend on $BACKEND_URL"
  local py
  py="$(python_bin)"
  log "Backend Python: $py"
  (
    cd "$ROOT_DIR/backend"
    exec env PATH="$PATH" "$py" -m uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT"
  ) >> "$STATE_DIR/backend.log" 2>&1 &
  echo "$!" > "$STATE_DIR/backend.pid"
  env_fingerprint > "$STATE_DIR/backend.env-fingerprint"

  wait_for_url "$BACKEND_URL/health" "Backend"
}

main() {
  log "Launching OmniDev from $ROOT_DIR"
  ensure_venv
  start_backend
  log "Native app talks to $BACKEND_URL directly"

  if [[ "${OMNIDEV_KEEP_ALIVE:-0}" == "1" ]]; then
    trap '"$ROOT_DIR/scripts/macos/stop-omnidev.sh" "$ROOT_DIR"; exit 0' INT TERM
    log "Supervisor mode enabled"
    wait "$(cat "$STATE_DIR/backend.pid")"
  fi
}

main "$@"
