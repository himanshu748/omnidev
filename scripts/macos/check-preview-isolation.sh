#!/usr/bin/env bash
# Regression check for the Code Gen preview's network isolation, against a
# real WKWebView. A hostname that resolves to loopback (as DNS rebinding
# would) must not reach a local server, while an allowlisted CDN still loads.
# The unfiltered run is a positive control proving the harness can reach it.
# Needs macOS and sudo (adds a hosts entry). Used by CI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$(mktemp -d)"
LOG="$WORK/requests.log"
HOST_NAME="preview.omnidev.test"
trap 'kill "${SERVER_PID:-}" 2>/dev/null || true; rm -rf "$WORK"' EXIT

if ! grep -q "$HOST_NAME" /etc/hosts; then
  echo "127.0.0.1 $HOST_NAME" | sudo tee -a /etc/hosts >/dev/null
  sudo dscacheutil -flushcache || true
fi

swiftc -O \
  "$ROOT/macos/Sources/OmniDevMac/Support/PreviewNetworkPolicy.swift" \
  "$ROOT/scripts/macos/preview-isolation/main.swift" \
  -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist \
  -Xlinker "$ROOT/scripts/macos/preview-isolation/Info.plist" \
  -o "$WORK/preview-isolation"

PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
python3 - "$PORT" "$LOG" <<'PY' &
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
port, log = int(sys.argv[1]), sys.argv[2]
class H(BaseHTTPRequestHandler):
    def _hit(self):
        with open(log, "a") as f:
            f.write(f"{self.command} {self.path} host={self.headers.get('Host')}\n")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"ok")
    do_GET = do_POST = _hit
    def log_message(self, *args): pass
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
PY
SERVER_PID=$!
sleep 1

echo "== positive control (no filter): the local server must be reached"
: > "$LOG"
"$WORK/preview-isolation" "$PORT" unfiltered
if ! grep -q "host=$HOST_NAME" "$LOG"; then
  echo "FAIL: control run never reached the loopback server via $HOST_NAME; the check is not meaningful"
  cat "$LOG"
  exit 1
fi
echo "control reached the server $(wc -l < "$LOG" | tr -d ' ') times"

echo "== preview policy: nothing may reach the local server"
: > "$LOG"
"$WORK/preview-isolation" "$PORT" filtered
sleep 2
if [ -s "$LOG" ]; then
  echo "FAIL: the preview reached the loopback server:"
  cat "$LOG"
  exit 1
fi
echo "OK: no request reached the loopback server, and the allowlisted CDN loaded"
