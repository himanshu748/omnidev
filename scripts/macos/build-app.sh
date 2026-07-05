#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACOS_PROJECT="$ROOT_DIR/macos"
APP_DIR="$ROOT_DIR/dist/mac"
APP_NAME="OmniDev"
APP_PATH="$APP_DIR/${APP_NAME}.app"
APP_CONTENTS="$APP_PATH/Contents"
MACOS_DIR="$APP_PATH/Contents/MacOS"
RESOURCES_DIR="$APP_PATH/Contents/Resources"
BUNDLE_ID="dev.omnidev.app"
MIN_SYSTEM_VERSION="13.0"

chmod +x "$ROOT_DIR/scripts/macos/launch-omnidev.sh" "$ROOT_DIR/scripts/macos/stop-omnidev.sh"
swift build --package-path "$MACOS_PROJECT" -c release >/dev/null
BUILD_BIN="$(swift build --package-path "$MACOS_PROJECT" -c release --show-bin-path)/$APP_NAME"

mkdir -p "$APP_DIR"
rm -rf "$APP_PATH"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"
cp "$BUILD_BIN" "$MACOS_DIR/$APP_NAME"
chmod +x "$MACOS_DIR/$APP_NAME"

ICON_PNG="$ROOT_DIR/frontend/public/brand/omnidev-logo.png"
ICON_FILE=""
if [[ -f "$ICON_PNG" ]] && command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  ICONSET="$RESOURCES_DIR/OmniDev.iconset"
  rm -rf "$ICONSET"
  mkdir -p "$ICONSET"
  sips -z 16 16 "$ICON_PNG" --out "$ICONSET/icon_16x16.png" >/dev/null
  sips -z 32 32 "$ICON_PNG" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$ICON_PNG" --out "$ICONSET/icon_32x32.png" >/dev/null
  sips -z 64 64 "$ICON_PNG" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$ICON_PNG" --out "$ICONSET/icon_128x128.png" >/dev/null
  sips -z 256 256 "$ICON_PNG" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$ICON_PNG" --out "$ICONSET/icon_256x256.png" >/dev/null
  sips -z 512 512 "$ICON_PNG" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$ICON_PNG" --out "$ICONSET/icon_512x512.png" >/dev/null
  cp "$ICON_PNG" "$ICONSET/icon_512x512@2x.png"
  iconutil -c icns "$ICONSET" -o "$RESOURCES_DIR/OmniDev.icns" >/dev/null
  rm -rf "$ICONSET"
  ICON_FILE="<key>CFBundleIconFile</key>
  <string>OmniDev</string>"
fi

cat > "$APP_CONTENTS/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleDisplayName</key>
  <string>$APP_NAME</string>
  <key>CFBundleExecutable</key>
  <string>$APP_NAME</string>
  $ICON_FILE
  <key>CFBundleIdentifier</key>
  <string>$BUNDLE_ID</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.3.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>$MIN_SYSTEM_VERSION</string>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
  </dict>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST

echo "$APP_PATH"
