# How to Get Credentials for OmniDev

This guide walks you through getting each API key or credential used by the backend.

---

## API key matrix (at a glance)

| Module           | OpenAI | AWS | IPInfo | Context7 | Notes |
|-----------------|--------|-----|--------|----------|--------|
| **DevOps Agent**| ✅ Required | ✅ Required | — | — | Natural language → boto3 |
| **Code Gen**    | ✅ Required | — | — | Optional | Without Context7: no live docs. Generate-image uses DALL-E. |
| **RAG Chatbot** | ✅ Required | — | — | — | Ingest + chat |
| **Vision Lab**  | ✅ Required | — | — | — | Image analysis / OCR |
| **Web Scraper** | — | — | — | — | No keys (Playwright) |
| **Cloud Storage**| — | ✅ Required | — | — | S3 only |
| **Location**    | — | — | Optional | — | Works without token (rate limited) |

---

## 1. OpenAI API Key (required for DevOps Agent, Code Gen, RAG, Vision Lab)

You already have one. If you need another or a new one:

1. Go to **https://platform.openai.com**
2. Sign in or create an account.
3. Click your profile (top right) → **View API keys** (or go to https://platform.openai.com/api-keys).
4. Click **Create new secret key**. Name it (e.g. "OmniDev"), copy the key immediately (it starts with `sk-` and is shown only once).
5. In `backend/.env` set:
   ```bash
   OPENAI_API_KEY=sk-proj-...your-key...
   OPENAI_MODEL=gpt-4.1-mini
   ```

**Billing:** Usage is billed to your OpenAI account. Check https://platform.openai.com/usage and set limits if needed.

---

## 2. AWS Credentials (required for DevOps Agent + Cloud Storage)

These are used to call AWS (EC2, S3) from the backend. You need an **Access Key ID** and **Secret Access Key**.

### Step 1: Create an AWS account (if you don’t have one)

1. Go to **https://aws.amazon.com**
2. Click **Create an AWS Account** and complete sign-up (card may be required; free tier is available).

### Step 2: Create an IAM user and access key

1. Sign in to the **AWS Console**: https://console.aws.amazon.com
2. Open **IAM**:
   - Use the search bar at the top and type **IAM**, or
   - Go to **Services** → **Security, Identity, & Compliance** → **IAM**.
3. In the left sidebar, click **Users** → **Create user**.
4. **User name:** e.g. `omnidev-backend`. Click **Next**.
5. **Permissions:**
   - Choose **Attach policies directly**.
   - For full OmniDev use (EC2 + S3), attach:
     - `AmazonEC2FullAccess`
     - `AmazonS3FullAccess`
   - For minimal S3-only (e.g. only Cloud Storage): attach only `AmazonS3FullAccess`.
   - Click **Next** → **Next** → **Create user**.
6. Open the user you just created → **Security credentials** tab.
7. Scroll to **Access keys** → **Create access key**.
8. Use **Application running outside AWS** (or **Command Line Interface**) → **Next** → **Create access key**.
9. **Copy both values once (Secret key is shown only here):**
   - **Access key ID** (e.g. `AKIA...`) → use as `AWS_ACCESS_KEY_ID`
   - **Secret access key** → use as `AWS_SECRET_ACCESS_KEY`

### Step 3: Put them in `.env`

In `backend/.env`:

```bash
AWS_ACCESS_KEY_ID=AKIA...your-access-key-id...
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_DEFAULT_REGION=us-east-1
```

Replace `us-east-1` with your preferred region (e.g. `ap-south-1` for Mumbai) if you want.

**Security:** Never commit `.env` or share these keys. The IAM user should have only the permissions it needs (e.g. EC2 + S3 as above).

---

## 3. IPInfo Token (optional for Location Services)

Location endpoints work without a token (free tier). For higher limits and more data:

1. Go to **https://ipinfo.io**
2. Sign up → **Dashboard** → **Account** (or **Token**).
3. Copy your token and in `backend/.env` set:
   ```bash
   IPINFO_TOKEN=your-token
   ```
   Or leave it empty: `IPINFO_TOKEN=`.

---

## 4. Context7 API Key (optional for Code Gen)

Code Gen uses Context7 to inject up-to-date library docs (React, Next.js, Streamlit, etc.) into generated code. Without it, generation still works using model knowledge.

1. Go to **https://context7.com/dashboard**
2. Sign up and create an API key.
3. In `backend/.env` set:
   ```bash
   CONTEXT7_API_KEY=ctx7sk-...
   ```
   Or leave empty: `CONTEXT7_API_KEY=`.

---

## Quick reference: `.env` template

```bash
# OpenAI (required for DevOps, Code Gen, RAG, Vision)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4.1-mini

# AWS (required for DevOps + Storage)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# IPInfo (optional for Location)
IPINFO_TOKEN=

# Context7 (optional for Code Gen live docs)
CONTEXT7_API_KEY=

# CORS
CORS_ORIGINS=http://localhost:3000
```

After editing `.env`, restart the backend: `uvicorn app.main:app --reload`.

---

## Verify each API key end-to-end

Run the backend (`cd backend && uv run uvicorn app.main:app --reload`) and frontend (`cd frontend && npm run dev`), then:

| Check | How |
|-------|-----|
| **Health** | `curl http://localhost:8000/health` → `{"status":"ok"}` |
| **Scraper** (no key) | Open http://localhost:3000/scraper → paste URL → Start Scraping. Should return content. |
| **Location** (optional key) | Open http://localhost:3000/location → Detect Location. Should show IP + city. |
| **DevOps** (OpenAI + AWS) | Open http://localhost:3000/devops → e.g. "List my EC2 instances" → Run. Should return summary (or 500 if keys missing). |
| **Code Gen** (OpenAI) | Open http://localhost:3000/codegen → prompt e.g. "A hello world page", framework React → Generate. Should return files. |
| **RAG** (OpenAI) | Open http://localhost:3000/rag → Add some text → Ask a question. Should reply from docs or say add documents. |
| **Vision** (OpenAI) | Open http://localhost:3000/vision → Upload image → Analyze. Needs valid `OPENAI_API_KEY`. |
| **Storage** (AWS) | Open http://localhost:3000/storage → List buckets. Should list buckets or `[]` (500 if AWS keys missing). |

If any endpoint returns **500** with a message like "Invalid API key" or "Credentials not found", add or fix that key in `backend/.env`.
