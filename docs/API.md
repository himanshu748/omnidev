# 📡 API Reference

> OmniDev Backend — FastAPI REST API  
> Base URL: `http://localhost:8000`  
> Interactive Docs: [Swagger UI](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)

<br />

## 🏥 System

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "omnidev"
}
```

---

## 🤖 DevOps Agent

### Run Command

```http
POST /api/devops/command
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "List my EC2 instances",
  "confirm_destructive": false
}
```

**Response:**
```json
{
  "action": "list_ec2",
  "params": {},
  "raw_result": { "...": "..." },
  "summary": "You have 3 running EC2 instances...",
  "needs_confirmation": false
}
```

**Notes:**
- Set `confirm_destructive: true` for actions like `stop`, `terminate`
- The AI agent parses natural language into specific boto3 operations

---

## 🕷️ Web Scraper

### Scrape URL

```http
POST /api/scraper/scrape
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "extract": "text",
  "stealth": true,
  "wait_for": null,
  "javascript": null,
  "wait_seconds": 0
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `string` | *required* | Target URL to scrape |
| `extract` | `string` | `"text"` | `"text"`, `"html"`, `"screenshot"`, `"links"`, `"metadata"`, or `"pdf"` |
| `stealth` | `bool` | `true` | Enable compatibility fingerprint adjustments for authorized pages; not a bot-protection bypass guarantee |
| `wait_for` | `string?` | `null` | CSS selector to wait for before extraction |
| `javascript` | `string?` | `null` | JavaScript to execute on the page |
| `wait_seconds` | `number` | `0` | Seconds to wait after page load (0–30) |
| `proxy` | `string?` | `null` | Optional proxy URL |
| `block_resources` | `string[]?` | `null` | Resource types to block, such as `image`, `font`, or `stylesheet` |

**Response (text/html mode):**
```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "status_code": 200,
  "content": "...",
  "screenshot_b64": null,
  "pdf_b64": null,
  "links": null,
  "metadata": null,
  "word_count": 42,
  "elapsed_ms": 1200
}
```

**Response (screenshot mode):**
```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "status_code": 200,
  "content": "",
  "screenshot_b64": "iVBORw0KGgo...",
  "elapsed_ms": 1200
}
```

---

## 🖼️ Vision Lab

### Analyze Image

```http
POST /api/vision/analyze
Content-Type: multipart/form-data
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | `file` | Image file (PNG, JPG, GIF, WebP) |
| `mode` | `string` | `"analyze"`, `"ocr"`, or `"custom"` |
| `prompt` | `string?` | Custom prompt (when mode = `"custom"`) |

**Response:**
```json
{
  "mode": "analyze",
  "model": "gemini-2.0-flash",
  "tokens_used": 512,
  "result": "This image shows a modern office workspace with..."
}
```

---

## 📦 Cloud Storage

### List Buckets

```http
GET /api/storage/buckets
```

**Response:**
```json
{
  "buckets": [
    {
      "name": "my-assets",
      "creation_date": "2026-01-10T12:00:00Z"
    }
  ]
}
```

### List Files

```http
GET /api/storage/files?bucket={bucket}&prefix=folder/
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `bucket` | `string` | S3 bucket name (path) |
| `prefix` | `string?` | Filter by key prefix (query) |

**Response:**
```json
{
  "bucket": "my-assets",
  "files": [
    {
      "key": "images/logo.png",
      "size": 24576,
      "last_modified": "2026-01-10T12:00:00Z"
    }
  ]
}
```

### Upload File

```http
POST /api/storage/upload
Content-Type: multipart/form-data
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `file` | `file` | File to upload |
| `bucket` | `string` | Target bucket name |
| `key` | `string?` | Custom S3 key (defaults to filename) |

### Download File

```http
GET /api/storage/download?bucket={bucket}&key={key}
```

Returns a **presigned URL** for direct download.

### Delete File

```http
DELETE /api/storage/files?bucket={bucket}&key={key}
```

---

## 📚 Knowledge (local RAG)

### Register a Source

```http
POST /api/knowledge/sources
Content-Type: application/json

{ "path": "/Users/you/notes", "kind": "docs" }
```

`kind` is `docs`, `code` or `chat` (chat ignores `path` and indexes the built-in chat history). Returns `201` with the source and starts background indexing. `GET /api/knowledge/sources` lists sources, `DELETE /api/knowledge/sources/{id}` removes one, `POST /api/knowledge/sources/{id}/reindex?full=true` re-embeds everything and `GET /api/knowledge/status` reports indexing progress.

### Search

```http
POST /api/knowledge/search
Content-Type: application/json

{ "query": "how does the login flow work?", "top_k": 8 }
```

Returns matching chunks with `file_path`, `snippet` and cosine `score`. Chat grounding: pass `"use_knowledge": true` to `POST /api/chat/stream` and the stream emits a `{"knowledge": {"cited_files": [...]}}` event before the answer deltas.

## 🤖 Agent Mode

### Run a Task

```http
POST /api/agent/stream
Content-Type: application/json

{ "task": "fix the failing test in ~/code/app", "use_mcp": true, "max_steps": 15 }
```

Streams newline-delimited JSON. Event kinds, in the order they typically appear:

| Event | Meaning |
|-------|---------|
| `{"agent": {...}}` | Run started: provider, model, workspaces, tool names, step cap |
| `{"step": {"n": 1, "thought": "..."}}` | The model's reasoning before a round of tool calls |
| `{"checkpoint": {"repo", "head", "dirty"}}` | git state recorded before the first mutation |
| `{"tool_call": {"tool", "arguments"}}` | A tool is about to run |
| `{"approval_required": {"id", "tool", "summary", "detail", "timeout_seconds"}}` | The run is paused, waiting for you |
| `{"approval_resolved": {"id", "decision"}}` | How it was answered |
| `{"tool_result": {"tool", "result", "ok"}}` | Tool output, `ok: false` when it failed |
| `{"delta": "..."}` | The final summary |
| `{"done": true}` | End of run |

Disconnecting stops the run.

### Answer an Approval

```http
POST /api/agent/approvals/{id}
Content-Type: application/json

{ "decision": "allow_once" }
```

`decision` is `allow_once`, `allow_always` (remembers that kind of action for the rest of this run) or `deny`. Approvals that go unanswered for `timeout_seconds` are denied, so a closed window can never authorise anything. `GET /api/agent/approvals` lists anything still waiting.

### Workspaces

```http
POST /api/agent/workspaces
Content-Type: application/json

{ "path": "/Users/you/code/app" }
```

Inside a workspace the agent edits without asking; everywhere else each action needs approval, and shell commands always do. Workspaces must be inside your home folder and cannot be `$HOME`, `~/Library` or OmniDev's data directory. `GET /api/agent/workspaces` lists them (the landing root appears as `implicit`) and `DELETE /api/agent/workspaces?path=...` removes one.

## 🔐 Authentication

OmniDev keeps external service keys in backend environment variables. Gemini, AWS, and Context7 credentials are configured server-side and are never exposed to clients. In Ollama mode no AI credential is needed at all — requests go to the local Ollama server.

## ⚠️ Error Handling

All endpoints return errors in a consistent format:

```json
{
  "detail": "Description of what went wrong"
}
```

HTTP status codes follow REST conventions:
- `200` — Success
- `400` — Bad request / invalid input
- `422` — Validation error (Pydantic)
- `500` — Internal server error
