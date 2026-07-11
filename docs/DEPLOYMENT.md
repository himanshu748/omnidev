# Deployment

OmniDev is **local-first by design**: the app, the FastAPI engine, and the models run on your machine. There is no hosted OmniDev service, and deploying the backend to a public host is out of scope — the DevOps agent holds AWS credentials and the scraper would become an open proxy. (See the non-goals in [PRD.md](PRD.md).)

The stack is the native SwiftUI app plus the FastAPI backend sidecar it supervises (and an optional MCP server). The Next.js web frontend was removed in favor of the native app, so there is no web deployment.

One thing does get "deployed":

## The macOS app (GitHub Releases)

`scripts/macos/build-app.sh` produces `dist/mac/OmniDev.app`; packaged builds attach to GitHub Releases. Signing, notarization, and a Homebrew cask are tracked in [ROADMAP.md](../ROADMAP.md).

## Running the backend on another machine you own

The backend runs anywhere Python does (see the README Quick Start). It has no authentication layer by design, so it refuses any non-loopback client by default (HTTP 403) even if bound to `0.0.0.0`. Exposing it beyond loopback is strongly discouraged; if you understand the risk and control the network, set `ALLOW_REMOTE_CLIENTS=1` and `CORS_ORIGINS` in `backend/.env`, and keep it behind an interface and firewall you trust. Prefer an SSH tunnel over opening the port.
