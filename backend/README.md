# OmniDev Backend

Local-first AI developer cockpit — FastAPI backend.

The AI layer is **provider-agnostic**: it runs fully offline against a local
[Ollama](https://ollama.com) model (default `gemma4:12b`) or, optionally,
against Google Gemini. `AI_PROVIDER=auto` (the default) uses Gemini when
`GEMINI_API_KEY` is set and falls back to local Ollama otherwise — so the
backend works out of the box with **no API key and no cloud**.

## Modules

| Module | Description | Backing |
|---|---|---|
| DevOps Agent | Natural-language AWS ops with a boto3 **plan preview**, human approval for destructive actions, read-only mode, and an audit log | AI provider + boto3 |
| Code Gen | Validated project generation (path/secret/npm-script safety); never executed on the backend | AI provider + optional Context7 |
| Web Scraper | Playwright extraction (text/html/screenshot/pdf/links/metadata) with an SSRF guard on target URLs | Playwright |
| Vision Lab | Image analysis & OCR | AI provider (multimodal) |
| Cloud Storage | S3 browse / upload / delete / presigned URLs | boto3 |
| Models | List installed models, recommend picks, and stream `ollama pull` progress | Ollama |

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --require-hashes -r requirements.lock
playwright install chromium

cp .env.example .env      # optional — sensible offline defaults work as-is
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for interactive API docs.

### Fully offline (no key)

```bash
# In a separate terminal:
ollama serve
ollama pull gemma4:12b    # one model covers text, structured plans, and vision
```

Then run the backend with `AI_PROVIDER=ollama` (or just leave `GEMINI_API_KEY`
unset — `auto` falls back to Ollama).

## Environment variables

See [`.env.example`](.env.example). Key ones:

- `AI_PROVIDER` — `auto` \| `gemini` \| `ollama`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL` — local model config
- `GEMINI_API_KEY`, `GEMINI_MODEL` — optional cloud provider
- `AWS_*` — optional, for DevOps Agent + Cloud Storage
- `CONTEXT7_API_KEY` — optional, for Code Gen live docs
- `DEVOPS_READ_ONLY`, `AUDIT_LOG_PATH` — DevOps safety controls
- `CORS_ORIGINS` — allowed browser origins

For provider and AWS setup steps, see the [Configuration section of the main README](../README.md#configuration).

## Tests

```bash
pytest              # from the backend/ directory
```
