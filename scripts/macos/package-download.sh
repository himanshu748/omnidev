#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_PATH="$("$ROOT_DIR/scripts/macos/build-app.sh")"
OUT_DIR="$ROOT_DIR/frontend/public/downloads"
OUT_PATH="$OUT_DIR/OmniDev-macOS.zip"

mkdir -p "$OUT_DIR"
rm -f "$OUT_PATH"
export COPYFILE_DISABLE=1

if command -v zip >/dev/null 2>&1; then
  (cd "$(dirname "$APP_PATH")" && zip -qry "$OUT_PATH" "$(basename "$APP_PATH")")
elif command -v ditto >/dev/null 2>&1; then
  ditto -c -k --keepParent "$APP_PATH" "$OUT_PATH"
else
  echo "zip or ditto is required to package OmniDev.app" >&2
  exit 1
fi

echo "$OUT_PATH"
