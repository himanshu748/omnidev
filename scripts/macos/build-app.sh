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
APP_VERSION="$(sed -n 's/.*static let version = "\(.*\)".*/\1/p' "$MACOS_PROJECT/Sources/OmniDevMac/Support/AppSettings.swift")"

chmod +x "$ROOT_DIR/scripts/macos/launch-omnidev.sh" "$ROOT_DIR/scripts/macos/stop-omnidev.sh"
# Universal binary so the same .app runs on Apple Silicon and Intel Macs.
# --arch needs full Xcode; two --triple builds + lipo work with bare CLT.
swift build --package-path "$MACOS_PROJECT" -c release --triple arm64-apple-macosx >/dev/null
swift build --package-path "$MACOS_PROJECT" -c release --triple x86_64-apple-macosx >/dev/null
ARM_BIN="$(swift build --package-path "$MACOS_PROJECT" -c release --triple arm64-apple-macosx --show-bin-path)/$APP_NAME"
X86_BIN="$(swift build --package-path "$MACOS_PROJECT" -c release --triple x86_64-apple-macosx --show-bin-path)/$APP_NAME"
UNIVERSAL_DIR="$MACOS_PROJECT/.build/universal"
mkdir -p "$UNIVERSAL_DIR"
lipo -create "$ARM_BIN" "$X86_BIN" -output "$UNIVERSAL_DIR/$APP_NAME"
BUILD_BIN="$UNIVERSAL_DIR/$APP_NAME"

mkdir -p "$APP_DIR"
rm -rf "$APP_PATH"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"
cp "$BUILD_BIN" "$MACOS_DIR/$APP_NAME"
chmod +x "$MACOS_DIR/$APP_NAME"

# Bundle.module resolves against Contents/Resources inside a .app; without
# the SwiftPM resource bundle the accessor fatalErrors at launch.
cp -R "$(dirname "$ARM_BIN")/OmniDevMac_OmniDevMac.bundle" "$RESOURCES_DIR/"

# Bundle the engine (backend source + launch scripts) so the packaged app
# self-installs into ~/Library/Application Support/OmniDev on first run.
ENGINE_DIR="$RESOURCES_DIR/engine"
mkdir -p "$ENGINE_DIR/scripts/macos"
rsync -a \
  --exclude '.venv' --exclude '__pycache__' --exclude '.pytest_cache' \
  --exclude 'tests' --exclude 'test-results' --exclude '.env' \
  "$ROOT_DIR/backend/" "$ENGINE_DIR/backend/"
cp "$ROOT_DIR/scripts/macos/launch-omnidev.sh" "$ROOT_DIR/scripts/macos/stop-omnidev.sh" "$ENGINE_DIR/scripts/macos/"
chmod +x "$ENGINE_DIR/scripts/macos/"*.sh

ICON_PNG="$ROOT_DIR/macos/Sources/OmniDevMac/Resources/AppIcon.png"
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
  <string>$APP_VERSION</string>
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

# Drag-to-Applications DMG alongside the raw .app (still unsigned; the
# release notes carry the right-click-to-open instructions).
DMG_STAGING="$APP_DIR/dmg-staging"
DMG_PATH="$APP_DIR/OmniDev-v$APP_VERSION.dmg"
rm -rf "$DMG_STAGING" "$DMG_PATH"
mkdir -p "$DMG_STAGING"
cp -R "$APP_PATH" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_STAGING" -ov -format UDZO "$DMG_PATH" >/dev/null
rm -rf "$DMG_STAGING"

echo "$APP_PATH"
echo "$DMG_PATH"
