#!/usr/bin/env bash
#
# Register OmniDev's MCP server with Claude Code, then prove it works.
#
# Registration is the easy part. The reason this script exists is that the
# hard parts are invisible: which Python can import the server, where the
# engine actually lives once the app has self-installed it, and whether the
# thing you just registered can really answer a tools/list call. All three
# are checked here so a failure is a clear message rather than a tool that
# silently never appears in Claude Code.
#
# Usage:
#   ./scripts/install-mcp.sh            register and verify
#   ./scripts/install-mcp.sh --print    print client config, register nothing
#   ./scripts/install-mcp.sh --verify   verify an existing registration only

set -uo pipefail

APP_SUPPORT_ENGINE="$HOME/Library/Application Support/OmniDev/engine"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32mok\033[0m   %s\n" "$1"; }
warn() { printf "  \033[33mwarn\033[0m %s\n" "$1"; }
die()  { printf "  \033[31mfail\033[0m %s\n" "$1" >&2; exit 1; }

# ── 1. Find the engine ──────────────────────────────────────
# The installed app copies the engine into Application Support, so prefer
# that: it survives the repo being moved or deleted. Fall back to this
# checkout for people running from source.
find_engine() {
  if [ -f "$APP_SUPPORT_ENGINE/backend/mcp_server.py" ]; then
    echo "$APP_SUPPORT_ENGINE"
  elif [ -f "$REPO_ROOT/backend/mcp_server.py" ]; then
    echo "$REPO_ROOT"
  else
    return 1
  fi
}

# ── 2. Find a Python that can actually run the server ───────
# Mirrors the launcher's resolution order. A Python that cannot import `mcp`
# is useless here even if it exists, so every candidate is tested rather
# than assumed.
find_python() {
  local engine="$1" candidate
  local candidates=(
    "$engine/backend/.venv/bin/python"
    "$REPO_ROOT/backend/.venv/bin/python"
    "$(command -v python3.13 || true)"
    "$(command -v python3.12 || true)"
    "$(command -v python3.11 || true)"
    "$(command -v python3 || true)"
  )
  for candidate in "${candidates[@]}"; do
    [ -n "$candidate" ] && [ -x "$candidate" ] || continue
    if "$candidate" -c "import mcp, httpx" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

# ── 3. Prove the server speaks MCP ──────────────────────────
# An stdio client must keep stdin open until it has read the responses;
# closing it early shuts the server down mid-call and looks like a hang.
verify_server() {
  local python="$1" server="$2"
  "$python" - "$python" "$server" <<'PY'
import json, subprocess, sys, time

python, server = sys.argv[1], sys.argv[2]
proc = subprocess.Popen(
    [python, server], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL, text=True, bufsize=1,
)


def send(payload):
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "omnidev-installer", "version": "1"}}})
send({"jsonrpc": "2.0", "method": "notifications/initialized"})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

tools, deadline = None, time.time() + 45
while time.time() < deadline:
    line = proc.stdout.readline()
    if not line:
        break
    try:
        message = json.loads(line)
    except json.JSONDecodeError:
        continue
    if message.get("id") == 2:
        tools = [t["name"] for t in message.get("result", {}).get("tools", [])]
        break

proc.stdin.close()
proc.terminate()
if not tools:
    print("NO_TOOLS")
    sys.exit(1)
print(" ".join(sorted(tools)))
PY
}

# ── Run ─────────────────────────────────────────────────────
MODE="install"
case "${1:-}" in
  --print) MODE="print" ;;
  --verify) MODE="verify" ;;
  --help|-h) sed -n '3,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac

bold "OmniDev MCP setup"

ENGINE="$(find_engine)" || die "Could not find the OmniDev engine. Install the app, or run this from a checkout."
ok "engine: ${ENGINE/#$HOME/~}"

PYTHON="$(find_python "$ENGINE")" || die "No Python could import the 'mcp' package.
       Install the app once and let it bootstrap its environment, or run:
       python3 -m pip install --require-hashes -r '$ENGINE/backend/requirements.lock'"
ok "python: ${PYTHON/#$HOME/~}"

SERVER="$ENGINE/backend/mcp_server.py"
[ -f "$SERVER" ] || die "Missing $SERVER"

# ── Prefer the running engine over a private process ────────
# The engine serves the same tools at /mcp over stateless streamable HTTP.
# Pointing a client there beats spawning a stdio process per client: no
# Python to resolve, no per-client process, and several clients can share
# one engine because there is no session to own.
find_engine_url() {
  local url
  for url in "${OMNIDEV_BACKEND_URL:-}" "http://127.0.0.1:8010" "http://127.0.0.1:8000"; do
    [ -n "$url" ] || continue
    if curl -fsS --max-time 2 "$url/health" 2>/dev/null | grep -q '"service":"omnidev"'; then
      echo "$url"
      return 0
    fi
  done
  return 1
}

verify_http() {
  # Parse the reply rather than grepping for "name", which also matches the
  # property names inside each tool's JSON schema and overcounts.
  local url="$1"
  curl -fsS --max-time 20 -X POST "$url/mcp" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' 2>/dev/null \
  | "$PYTHON" -c '
import json, sys
for line in sys.stdin.read().splitlines():
    line = line.strip()
    if line.startswith("data:"):
        line = line[5:].strip()
    if line.startswith("{"):
        print(len(json.loads(line).get("result", {}).get("tools", [])))
        break
else:
    print(0)
'
}

ENGINE_URL="$(find_engine_url || true)"

if [ "$MODE" = "print" ]; then
  bold ""
  if [ -n "$ENGINE_URL" ]; then
    bold "Recommended, while the OmniDev app is running:"
    cat <<JSON
  "omnidev": {
    "type": "http",
    "url": "$ENGINE_URL/mcp"
  }
JSON
    bold ""
  fi
  bold "Standalone process (works with the app closed):"
  cat <<JSON
  "omnidev": {
    "command": "$PYTHON",
    "args": ["$SERVER"]
  }
JSON
  exit 0
fi

if [ "$MODE" = "install" ]; then
  if command -v claude >/dev/null 2>&1; then
    claude mcp remove omnidev -s user >/dev/null 2>&1
    if [ -n "$ENGINE_URL" ] &&
       claude mcp add --scope user --transport http omnidev "$ENGINE_URL/mcp" >/dev/null 2>&1; then
      ok "registered over HTTP at $ENGINE_URL/mcp (no extra process)"
      TOOL_COUNT="$(verify_http "$ENGINE_URL")"
      if [ "${TOOL_COUNT:-0}" -gt 0 ]; then
        ok "engine answered with $TOOL_COUNT tools"
        bold ""
        bold "Done. Restart Claude Code, then try:"
        printf "  \"search my notes for the deployment checklist\"   (search_knowledge)\n"
        printf "  \"what does ~/Desktop/screenshot.png say?\"        (ask_file)\n"
        printf "\nKeep the OmniDev app running. Add folders under Knowledge.\n"
        exit 0
      fi
      warn "registered, but the engine did not answer; falling back to a standalone process"
      claude mcp remove omnidev -s user >/dev/null 2>&1
    fi
    if claude mcp add --scope user omnidev -- "$PYTHON" "$SERVER" >/dev/null 2>&1; then
      ok "registered a standalone stdio server (user scope)"
    else
      warn "could not register automatically; run this to see why:"
      printf "       claude mcp add --scope user omnidev -- '%s' '%s'\n" "$PYTHON" "$SERVER"
    fi
  else
    warn "the 'claude' CLI is not on PATH, so nothing was registered"
    printf "       Run '%s --print' for a config you can paste into another client.\n" "$0"
  fi
fi

printf "  ..   verifying over real stdio, this starts the server\n"
TOOLS="$(verify_server "$PYTHON" "$SERVER")"
if [ -z "$TOOLS" ] || [ "$TOOLS" = "NO_TOOLS" ]; then
  die "The server did not answer a tools/list call. It will not work in Claude Code."
fi

COUNT="$(printf "%s" "$TOOLS" | wc -w | tr -d ' ')"
ok "server answered with $COUNT tools"
printf "       %s\n" "$TOOLS"

bold ""
bold "Done. Restart Claude Code, then try:"
printf "  \"search my notes for the deployment checklist\"   (search_knowledge)\n"
printf "  \"what does ~/Desktop/screenshot.png say?\"        (ask_file)\n"
printf "\nAdd folders to the index in the OmniDev app under Knowledge.\n"
