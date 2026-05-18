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
  "command": "List my EC2 instances",
  "confirm_destructive": false
}
```

**Response:**
```json
{
  "action": "list_ec2",
  "parameters": {},
  "summary": "You have 3 running EC2 instances...",
  "raw": { ... }
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
  "mode": "text",
  "stealth": true,
  "wait_for": null,
  "custom_js": null,
  "wait_after_load": 0
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `string` | *required* | Target URL to scrape |
| `mode` | `string` | `"text"` | `"text"`, `"html"`, or `"screenshot"` |
| `stealth` | `bool` | `true` | Enable anti-detection fingerprinting |
| `wait_for` | `string?` | `null` | CSS selector to wait for before extraction |
| `custom_js` | `string?` | `null` | JavaScript to execute on the page |
| `wait_after_load` | `int` | `0` | Seconds to wait after page load (0–30) |

**Response (text/html mode):**
```json
{
  "status": "success",
  "status_code": 200,
  "title": "Example Domain",
  "url": "https://example.com",
  "text": "..."
}
```

**Response (screenshot mode):**
```json
{
  "status": "success",
  "screenshot_base64": "iVBORw0KGgo..."
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
| `file` | `file` | Image file (PNG, JPG, GIF, WebP) |
| `mode` | `string` | `"analyze"`, `"ocr"`, or `"custom"` |
| `prompt` | `string?` | Custom prompt (when mode = `"custom"`) |

**Response:**
```json
{
  "mode": "analyze",
  "model": "gpt-4.1-mini",
  "tokens": 512,
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
  "buckets": ["my-assets", "my-backups", "my-logs"]
}
```

### List Files

```http
GET /api/storage/files/{bucket}?prefix=folder/
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
GET /api/storage/download/{bucket}/{key}
```

Returns a **presigned URL** for direct download.

### Delete File

```http
DELETE /api/storage/delete/{bucket}/{key}
```

---

## 📍 Location Services

### Detect My Location

```http
GET /api/location/me
```

Returns location based on the request's IP address.

**Response:**
```json
{
  "ip": "49.36.148.92",
  "city": "Mumbai",
  "region": "Maharashtra",
  "country": "IN",
  "loc": "19.0760,72.8777",
  "org": "AS55836 Reliance Jio",
  "timezone": "Asia/Kolkata"
}
```

### IP Lookup

```http
GET /api/location/ip/{ip_address}
```

### Reverse Geocode

```http
GET /api/location/reverse?lat=40.7128&lon=-74.0060
```

### Forward Geocode (Address Search)

```http
GET /api/location/geocode?q=Times+Square
```

**Response:**
```json
[
  {
    "display_name": "Times Square, Manhattan, New York...",
    "lat": "40.7580",
    "lon": "-73.9855",
    "type": "tourism"
  }
]
```

---

## 🔐 Authentication

Currently, OmniDev uses **API key authentication** via environment variables. All external service keys (`OPENAI_API_KEY`, `AWS_*`) are configured server-side and never exposed to the frontend.

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
