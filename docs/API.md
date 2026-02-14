# 📡 OmniDev — API Reference

> Complete REST API documentation for the OmniDev backend.

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)  
**OpenAPI Spec:** `http://localhost:8000/openapi.json`

---

## Table of Contents

1. [System](#system)
2. [DevOps Agent](#devops-agent)
3. [Web Scraper](#web-scraper)
4. [Vision Lab](#vision-lab)
5. [Cloud Storage](#cloud-storage)
6. [Location Services](#location-services)
7. [Error Handling](#error-handling)

---

## System

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

## DevOps Agent

### Execute Command

```http
POST /api/devops/command
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | `string` | ✅ | Natural language AWS command |
| `confirm` | `boolean` | ❌ | Required `true` for destructive actions |

**Example Request:**
```json
{
  "command": "List my EC2 instances",
  "confirm": false
}
```

**Example Response:**
```json
{
  "action": "list_ec2",
  "parameters": { "region": "us-east-1" },
  "summary": "Found 3 running EC2 instances in us-east-1.",
  "raw_output": { ... },
  "requires_confirmation": false
}
```

**Supported Commands:**

| Intent | Action | Confirmation |
|--------|--------|:------------:|
| List EC2 instances | `list_ec2` | ❌ |
| Launch instance | `launch_ec2` | ✅ |
| Stop instance | `stop_ec2` | ✅ |
| Terminate instance | `terminate_ec2` | ✅ |
| List S3 buckets | `list_s3` | ❌ |
| Show security groups | `list_security_groups` | ❌ |

---

## Web Scraper

### Scrape URL

```http
POST /api/scraper/scrape
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | `string` | ✅ | — | Target URL to scrape |
| `extract` | `string` | ❌ | `"text"` | `"text"`, `"html"`, or `"screenshot"` |
| `stealth` | `boolean` | ❌ | `true` | Enable anti-detection patches |
| `wait_for` | `string` | ❌ | `null` | CSS selector to wait for |
| `wait_after_load` | `integer` | ❌ | `0` | Seconds to wait after page load |
| `custom_js` | `string` | ❌ | `null` | JavaScript to execute on page |

**Example Request:**
```json
{
  "url": "https://example.com",
  "extract": "text",
  "stealth": true,
  "wait_after_load": 2
}
```

**Example Response (text/html):**
```json
{
  "success": true,
  "url": "https://example.com",
  "status_code": 200,
  "title": "Example Domain",
  "content": "This domain is for use in illustrative examples...",
  "timestamp": "2026-02-14T12:00:00Z",
  "load_time_ms": 842,
  "content_length": 1256
}
```

**Example Response (screenshot):**
```json
{
  "success": true,
  "url": "https://example.com",
  "status_code": 200,
  "title": "Example Domain",
  "screenshot_url": "https://s3.amazonaws.com/...",
  "timestamp": "2026-02-14T12:00:00Z",
  "load_time_ms": 1203
}
```

---

## Vision Lab

### Analyze Image

```http
POST /api/vision/analyze
Content-Type: multipart/form-data
```

**Form Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | `file` | ✅ | — | Image file (PNG, JPG, WEBP) |
| `mode` | `string` | ❌ | `"analyze"` | `"analyze"`, `"ocr"`, or `"custom"` |
| `prompt` | `string` | ❌ | `null` | Custom prompt (required if mode=`"custom"`) |

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/vision/analyze \
  -F "file=@photo.jpg" \
  -F "mode=analyze"
```

**Example Response:**
```json
{
  "mode": "analyze",
  "model": "gpt-4.1-mini",
  "tokens_used": 512,
  "result": "The image shows a modern office workspace with dual monitors displaying code editors..."
}
```

---

## Cloud Storage

### List Buckets

```http
GET /api/storage/buckets
```

**Response:**
```json
{
  "buckets": [
    { "name": "my-app-assets", "created": "2025-06-15T10:00:00Z" },
    { "name": "ml-datasets", "created": "2025-09-01T14:30:00Z" }
  ]
}
```

### List Files

```http
GET /api/storage/files/{bucket}?prefix={prefix}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bucket` | `string` (path) | ✅ | S3 bucket name |
| `prefix` | `string` (query) | ❌ | Filter by key prefix |

**Response:**
```json
{
  "bucket": "my-app-assets",
  "prefix": "images/",
  "files": [
    {
      "key": "images/logo.png",
      "size": 24576,
      "last_modified": "2026-01-10T08:00:00Z"
    }
  ]
}
```

### Upload File

```http
POST /api/storage/upload
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `file` | ✅ | File to upload |
| `bucket` | `string` | ✅ | Target S3 bucket |
| `key` | `string` | ❌ | Custom S3 key (default: filename) |

### Download File (Presigned URL)

```http
GET /api/storage/download/{bucket}/{key}
```

**Response:**
```json
{
  "download_url": "https://my-app-assets.s3.amazonaws.com/...",
  "expires_in": 3600
}
```

### Delete File

```http
DELETE /api/storage/files/{bucket}/{key}
```

**Response:**
```json
{
  "deleted": true,
  "bucket": "my-app-assets",
  "key": "images/old-logo.png"
}
```

---

## Location Services

### Detect My Location

```http
GET /api/location/me
```

> Uses client's IP from `X-Forwarded-For` header for accurate geolocation.

**Response:**
```json
{
  "ip": "203.0.113.42",
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

**Example:** `GET /api/location/ip/8.8.8.8`

**Response:**
```json
{
  "ip": "8.8.8.8",
  "city": "Mountain View",
  "region": "California",
  "country": "US",
  "loc": "37.4056,-122.0775",
  "org": "AS15169 Google LLC",
  "timezone": "America/Los_Angeles"
}
```

### Reverse Geocode

```http
GET /api/location/reverse?lat={lat}&lon={lon}
```

**Example:** `GET /api/location/reverse?lat=40.7128&lon=-74.0060`

**Response:**
```json
{
  "address": "New York City Hall, 260 Broadway, New York, NY 10007, USA",
  "lat": "40.7128",
  "lon": "-74.0060",
  "type": "administrative"
}
```

### Forward Geocode (Address Search)

```http
GET /api/location/geocode?q={query}
```

**Example:** `GET /api/location/geocode?q=Eiffel Tower`

**Response:**
```json
{
  "results": [
    {
      "display_name": "Eiffel Tower, 5 Avenue Anatole France, 75007 Paris, France",
      "lat": "48.8584",
      "lon": "2.2945",
      "type": "tourism"
    }
  ]
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request / validation error |
| `404` | Resource not found |
| `422` | Unprocessable entity (Pydantic validation) |
| `500` | Internal server error |

### Common Errors

| Scenario | Status | Message |
|----------|--------|---------|
| Missing API key | `500` | `"OpenAI API key not configured"` |
| Invalid URL | `400` | `"Invalid URL format"` |
| AWS credentials missing | `500` | `"AWS credentials not configured"` |
| Destructive action without confirm | `400` | `"Destructive action requires confirmation"` |
| Scraping timeout | `500` | `"Page load timed out after 30s"` |

---

<p align="center">
  <em>For architecture overview, see <a href="ARCHITECTURE.md">ARCHITECTURE.md</a>. For deployment, see <a href="DEPLOYMENT.md">DEPLOYMENT.md</a>.</em>
</p>
