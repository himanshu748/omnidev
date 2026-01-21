# 🚀 OmniDev Deployment Guide

This guide covers how to deploy the **Backend to Render** and the **Frontend to Vercel**.

## 1. Backend Deployment (Render.com)

Render is chosen because it supports the system dependencies required by Playwright better than standard serverless functions.

1. **Push to GitHub**: Ensure your code is pushed to a GitHub repository.
2. **Sign up/Login to [Render](https://dashboard.render.com/)**.
3. **New Blueprint**:
    - Click **"New +"** and select **"Blueprint"**.
    - Connect your GitHub repository.
    - Render will automatically detect `backend/render.yaml`.
4. **Configure Environment Variables**:
    - In the Render dashboard for your new service, go to **Environment**.
    - You MUST manually add these secrets (they are not synced from repo for security):
        - `OPENAI_API_KEY`: Your key starting with `sk-...`
        - `AWS_ACCESS_KEY_ID`: Your AWS Key ID (optional, for DevOps agent)
        - `AWS_SECRET_ACCESS_KEY`: Your AWS Secret (optional)
        - `GEMINI_API_KEY`: If used.
5. **Deploy**: Click **Apply** or **Deploy**.
    - Watch the build logs. It will install Python 3.12+, dependencies, and Chromium.
    - Once "Live", copy your backend URL (e.g., `https://omnidev-api.onrender.com`).

---

## 2. Frontend Deployment (Vercel)

Vercel provides the best performance for Next.js applications.

1. **Update Vercel Config**:
    - Edit `frontend/vercel.json`.
    - **Crucial**: Replace `https://omnidev-api.onrender.com` with your **ACTUAL** Render Backend URL from step 1.
    ```json
    {
      "source": "/api/:path*",
      "destination": "https://your-render-app-name.onrender.com/api/:path*"
    }
    ```
2. **Push Changes**: Commit and push the updated `vercel.json`.
3. **Sign up/Login to [Vercel](https://vercel.com/)**.
4. **Add New Project**:
    - Import your GitHub repository.
    - **Root Directory**: Select `frontend` (Edit -> select `frontend` folder).
    - **Framework Preset**: Next.js (should detect automatically).
5. **Environment Variables**:
    - Add `NEXT_PUBLIC_API_URL` = `https://your-render-app-name.onrender.com` (Your Render Backend URL).
    - Add other public vars if needed.
6. **Deploy**: Click **Deploy**.

## 3. Post-Deployment Verification

1. Open your Vercel URL.
2. Check the Status indicators in the top right. `API` should be green (● API).
3. Try the **AI Chat** to verify OpenAI connection.
4. Try **Web Scraper** to verify Playwright on Render.
