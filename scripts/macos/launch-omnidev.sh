#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
STATE_DIR="$ROOT_DIR/.omnidev-macos"
BACKEND_PORT="${OMNIDEV_BACKEND_PORT:-8000}"
FRONTEND_PORT="${OMNIDEV_FRONTEND_PORT:-3000}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"

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

node_bin() {
  local candidates=()
  if [[ -n "${OMNIDEV_NODE:-}" ]]; then
    candidates+=("$OMNIDEV_NODE")
  fi
  candidates+=(
    "$HOME/.local/bin/node"
    "/opt/homebrew/bin/node"
    "/usr/local/bin/node"
    "$(command -v node || true)"
  )

  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" && -x "$candidate" ]] || continue
    if "$candidate" -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 20 ? 0 : 1)' >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
    log "Skipping unusable Node candidate: $candidate"
  done

  log "No usable Node.js interpreter found"
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

start_backend() {
  if is_http_up "$BACKEND_URL/health"; then
    log "Backend already healthy at $BACKEND_URL"
    return 0
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

  wait_for_url "$BACKEND_URL/health" "Backend"
}

start_frontend() {
  if is_http_up "$FRONTEND_URL"; then
    log "Frontend already running at $FRONTEND_URL"
    return 0
  fi

  if port_is_listening "$FRONTEND_PORT"; then
    log "Frontend port $FRONTEND_PORT is already in use but root is not reachable"
    return 1
  fi

  log "Starting frontend on $FRONTEND_URL"
  local node
  node="$(node_bin)"
  log "Frontend Node: $node"
  (
    cd "$ROOT_DIR/frontend"
    exec env PATH="$PATH" NEXT_PUBLIC_API_URL="$BACKEND_URL" "$node" ./node_modules/next/dist/bin/next dev -H 127.0.0.1 -p "$FRONTEND_PORT"
  ) >> "$STATE_DIR/frontend.log" 2>&1 &
  echo "$!" > "$STATE_DIR/frontend.pid"

  wait_for_url "$FRONTEND_URL" "Frontend" 120
}

main() {
  log "Launching OmniDev from $ROOT_DIR"
  start_backend

  # The native app is fully SwiftUI and only needs the backend; the Next.js
  # frontend is the dev-stack web UI and the hosted marketing site.
  if [[ "${OMNIDEV_SKIP_FRONTEND:-0}" == "1" ]]; then
    log "Frontend skipped (OMNIDEV_SKIP_FRONTEND=1); native app talks to $BACKEND_URL directly"
    if [[ "${OMNIDEV_KEEP_ALIVE:-0}" == "1" ]]; then
      trap '"$ROOT_DIR/scripts/macos/stop-omnidev.sh" "$ROOT_DIR"; exit 0' INT TERM
      log "Supervisor mode enabled"
      wait "$(cat "$STATE_DIR/backend.pid")"
    fi
    return 0
  fi

  start_frontend
  if [[ "${OMNIDEV_OPEN_BROWSER:-1}" == "1" ]]; then
    open "$FRONTEND_URL/app"
    log "Opened $FRONTEND_URL/app"
  else
    log "Browser open disabled; native shell will load $FRONTEND_URL/app"
  fi

  if [[ "${OMNIDEV_KEEP_ALIVE:-0}" == "1" ]]; then
    trap '"$ROOT_DIR/scripts/macos/stop-omnidev.sh" "$ROOT_DIR"; exit 0' INT TERM
    log "Supervisor mode enabled"
    wait "$(cat "$STATE_DIR/backend.pid")" "$(cat "$STATE_DIR/frontend.pid")"
  fi
}

main "$@"
