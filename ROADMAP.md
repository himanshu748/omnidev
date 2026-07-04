# OmniDev Roadmap

OmniDev is the offline-first AI dev cockpit you open instead of a cloud IDE tab:
describe what you want in plain language, watch it happen against a local model,
and keep every byte on your machine.

**Guiding principle: deepen, don't broaden.** OmniDev already spans capable
modules with strong safety hardening. The differentiator isn't a 9th tool — it's
making the core loop feel alive: streaming output, conversation memory, and
landing real artifacts on disk.

## The killer workflow

> prompt → streaming code → iterate with memory ("now add auth", "refactor to
> TypeScript") → land in a real Git repo on disk — with zero data leaving the laptop.

## Now (0.3.x → 0.4)

- [x] Provider-agnostic AI layer (local Ollama `gemma4:e4b` or Gemini)
- [x] Local model manager — status, recommendations, streaming `ollama pull`
- [x] DevOps agent safety: boto3 plan preview, human approval, read-only mode, audit log
- [x] SSRF guard on the scraper + preview
- [x] One honest license, honest version, CI on every PR
- [ ] **Streaming** AI text + Code Gen output (SSE)
- [ ] **Conversation memory / sessions** so you can iterate
- [ ] **Git integration** — land a generated project in a real repo

## Next

- [ ] Resource-abuse guards: vision upload cap, scraper JS/selector guards, DevOps rate limits
- [ ] Extended model management: delete / show info / import GGUF
- [ ] Native macOS: model-manager surface, richer menu bar, first-run onboarding
- [ ] Docker Compose / devcontainer for reproducible dev

## Later

- [ ] Signed + notarized DMG, release automation on `v*` tags, Homebrew cask
- [ ] Optional sandboxed code execution (Docker/nsjail, network-off, resource-limited)
- [ ] MCP server surface so other agents can drive OmniDev

Have an idea? Open a [feature request](.github/ISSUE_TEMPLATE/feature_request.md).
