# OmniDev Roadmap

OmniDev is the offline-first AI dev cockpit you open instead of a cloud IDE tab:
describe what you want in plain language, watch it happen against a local model,
and keep every byte on your machine.

**Guiding principle: deepen, don't broaden.** The roadmap tracks what has shipped,
the one remaining item in the current workflow, and the open work that follows.

## Shipped

- [x] Provider-agnostic AI layer with local Ollama and optional Gemini; the default local model is `gemma4:12b`.
- [x] Local model manager for status, recommendations, streaming pulls, and model deletion.
- [x] DevOps safety: boto3 plan preview, explicit approval for destructive actions, read-only mode, and audit log.
- [x] SSRF guard on the scraper and Code Gen preview.
- [x] NDJSON streaming for chat and the agent.
- [x] Conversation memory and sessions.
- [x] Git integration to land generated projects and inspect repository status.
- [x] MCP server and curated server marketplace.
- [x] 10 MB vision upload limit.
- [x] Native macOS first-run onboarding.
- [x] Release automation for `v*` tags.

## Now

- [ ] Stream Code Gen output, keeping final-file validation and the existing non-streaming endpoints intact ([#15](https://github.com/himanshu748/omnidev/issues/15)).

## Next

- [ ] Bound replayed chat history when the newest message exceeds the character budget ([#22](https://github.com/himanshu748/omnidev/issues/22)).
- [ ] Validate loopback API `Host` headers to prevent DNS rebinding ([#24](https://github.com/himanshu748/omnidev/issues/24)).
- [ ] Run third-party MCP stdio servers inside the agent sandbox ([#25](https://github.com/himanshu748/omnidev/issues/25)).
- [ ] Add model details and import for local GGUF files ([#20](https://github.com/himanshu748/omnidev/issues/20)).
- [ ] Add VoiceOver labels to icon-only macOS controls ([#9](https://github.com/himanshu748/omnidev/issues/9)).
- [ ] Exercise macOS-only Vision OCR indexing in CI ([#12](https://github.com/himanshu748/omnidev/issues/12)).
- [ ] Enforce endpoint test coverage and report backend line coverage ([#13](https://github.com/himanshu748/omnidev/issues/13)).
- [ ] Add Ruff linting and formatting for the backend ([#6](https://github.com/himanshu748/omnidev/issues/6)).
- [ ] Add incremental static type checking for safety-critical services ([#7](https://github.com/himanshu748/omnidev/issues/7)).
- [ ] Add an XCTest target for the macOS app ([#8](https://github.com/himanshu748/omnidev/issues/8)).
- [ ] Add automated dependency updates for GitHub Actions and Python ([#10](https://github.com/himanshu748/omnidev/issues/10)).
- [ ] Migrate the MCP server to Python SDK v2 ([#14](https://github.com/himanshu748/omnidev/issues/14)).
- [ ] Add a devcontainer for backend development ([#17](https://github.com/himanshu748/omnidev/issues/17)).
- [ ] Consolidate the script directories and move the dated security review ([#18](https://github.com/himanshu748/omnidev/issues/18)).
- [ ] Add EditorConfig and optional pre-commit checks ([#19](https://github.com/himanshu748/omnidev/issues/19)).
- [ ] Unify the backend, app, changelog, and security-policy versions ([#4](https://github.com/himanshu748/omnidev/issues/4)).

## Later

- [ ] Sign and notarize release builds, and publish a Homebrew cask ([#16](https://github.com/himanshu748/omnidev/issues/16)).

Have an idea? Open a [feature request](https://github.com/himanshu748/omnidev/issues/new?template=feature_request.yml), or see [CONTRIBUTING.md](CONTRIBUTING.md) to pick up an open issue.
