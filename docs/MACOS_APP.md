# macOS App

OmniDev can be launched on macOS through a native SwiftUI/WebKit `.app` shell. The app starts the FastAPI backend and Next.js frontend as local sidecars, waits for both to become reachable, then loads the OmniDev cockpit inside the native window.

This is a developer-friendly native shell for a local checkout, not a signed production installer.

## Prerequisites

- macOS
- Python dependencies installed in `backend/`
- Node dependencies installed in `frontend/`
- Playwright Chromium installed for the backend

Use the normal local setup first:

```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium

cd ../frontend
npm install
```

## Build the Native App

```bash
scripts/macos/build-app.sh
```

The generated app is written to:

```text
dist/mac/OmniDev.app
```

## Package a Release Zip

The landing page "Get the app" buttons point to GitHub Releases
(`https://github.com/himanshu748/omnidev/releases/latest`). Build the zip to
attach to a release with:

```bash
scripts/macos/package-download.sh
```

This writes `frontend/public/downloads/OmniDev-macOS.zip` locally (the path is
not committed). The package is a native macOS shell for this local project
checkout. It is not yet a signed, notarized, portable installer.

## Launch

Open the generated app in Finder, or run:

```bash
open dist/mac/OmniDev.app
```

The native shell uses app-owned loopback ports by default:

- Backend sidecar: `127.0.0.1:8010`
- Frontend sidecar: `127.0.0.1:3010`

This avoids common development-port collisions such as another app already using
`3000`. The native shell starts local services without opening a separate
browser. For the old browser-opening launcher flow, run:

```bash
scripts/macos/launch-omnidev.sh
```

The launcher writes logs and process IDs under:

```text
.omnidev-macos/
```

## Stop Local Services

```bash
scripts/macos/stop-omnidev.sh
```

## Ports

Defaults:

- Backend: `127.0.0.1:8000`
- Frontend: `127.0.0.1:3000`

Override them when launching from the shell:

```bash
OMNIDEV_BACKEND_PORT=8010 OMNIDEV_FRONTEND_PORT=3010 scripts/macos/launch-omnidev.sh
```
