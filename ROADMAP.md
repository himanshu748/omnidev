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

## Shipped

- [x] Provider-agnostic AI layer: local Ollama (`gemma4:12b`, or `gemma4:e2b` on smaller Macs) or optional Gemini
- [x] Streaming chat and agent runs (NDJSON), with conversation memory across turns
- [x] Agent mode: workspaces, per-action approvals, backups before every write, no delete tool
- [x] OS-level sandbox for agent commands (macOS Seatbelt / Linux bubblewrap), network off by default
- [x] Knowledge: on-device OCR, hybrid search with citations, sensitive-file exclusions
- [x] Git landing for generated projects (`POST /api/git/land`)
- [x] MCP server (`make mcp`) and a curated MCP marketplace
- [x] Local model manager: status, recommendations, streaming pull, delete
- [x] Native macOS app with onboarding, menu-bar extra, Settings, and update checks
- [x] Release workflow on `v*` tags (app zip, DMG, checksums)
- [x] Safety: SSRF guard, DevOps plan preview and approval, loopback-only API with DNS-rebinding protection, isolated Code Gen preview

## Now (0.8)

- [ ] Stream Code Gen output ([#15](https://github.com/himanshu748/omnidev/issues/15))
- [ ] Run third-party MCP servers inside the sandbox ([#25](https://github.com/himanshu748/omnidev/issues/25))
- [ ] Model details and local GGUF import ([#20](https://github.com/himanshu748/omnidev/issues/20))
- [ ] Migrate the MCP server to MCP SDK v2 ([#14](https://github.com/himanshu748/omnidev/issues/14))

## Next

- [ ] macOS app tests in CI ([#8](https://github.com/himanshu748/omnidev/issues/8)) and VoiceOver labels everywhere ([#9](https://github.com/himanshu748/omnidev/issues/9))
- [ ] Vision OCR indexing exercised on a macOS runner ([#12](https://github.com/himanshu748/omnidev/issues/12))
- [ ] Static type checking, starting with the safety-critical services ([#7](https://github.com/himanshu748/omnidev/issues/7))
- [ ] Repository-wide Ruff formatting ([#6](https://github.com/himanshu748/omnidev/issues/6))

## Later

- [ ] Signed and notarized DMG, plus a Homebrew cask ([#16](https://github.com/himanshu748/omnidev/issues/16))

Have an idea? Open a [feature request](https://github.com/himanshu748/omnidev/issues/new?template=feature_request.yml), or see [CONTRIBUTING.md](CONTRIBUTING.md) to pick up an open issue.
