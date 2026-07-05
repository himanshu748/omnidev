# Deployment

OmniDev is **local-first by design**: the app, the FastAPI engine, and the models run on your machine. There is no hosted OmniDev service, and deploying the backend to a public host is out of scope — the DevOps agent holds AWS credentials and the scraper would become an open proxy. (See the non-goals in [PRD.md](PRD.md).)

Two things do get "deployed":

## 1. The marketing site (Vercel)

Only the Next.js site at `/` is hosted; it is a static product page — the cockpit and modules require the local backend.

The GitHub→Vercel integration is stale (the repo was recreated), so deploy via the CLI from a staged directory with `frontend/` inside it:

```bash
# One-time: npm i -g vercel && vercel login
STAGE=$(mktemp -d)
git archive HEAD | tar -x -C "$STAGE"
cd "$STAGE" && vercel --prod   # project: omnidev, rootDirectory: frontend
```

Live: https://omnidev-himanshus-projects-acd54afd.vercel.app

## 2. The macOS app (GitHub Releases)

`scripts/macos/build-app.sh` produces `dist/mac/OmniDev.app`; packaged builds attach to GitHub Releases. Signing, notarization, and a Homebrew cask are tracked in [ROADMAP.md](../ROADMAP.md).

## Running the stack on another machine you own

The dev stack runs anywhere (see the README Quick Start). If you serve the cockpit to other devices on your LAN, set `CORS_ORIGINS` in `backend/.env` to the origins you will use, and keep the backend bound to an interface you trust — it has no authentication layer by design, because it is meant to stay on loopback.
