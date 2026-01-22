# Backend Deployment Guide

## Required Environment Variables

The following environment variables **must** be set in your Render deployment for authentication to work:

### 1. SUPABASE_JWT_SECRET (Required)

**Purpose:** Used to verify JWT tokens from Supabase authentication.

**How to get it:**
1. Go to your Supabase Dashboard: https://supabase.com/dashboard
2. Select your project
3. Navigate to **Settings** > **API**
4. Find the **JWT Secret** field
5. Copy the secret value

**Set in Render:**
- Go to your Render dashboard
- Select the `omnidev-api` service
- Go to **Environment** tab
- Add: `SUPABASE_JWT_SECRET` = `[your-jwt-secret]`

### 2. API_KEY_SALT (Required)

**Purpose:** Used to generate and verify API keys for authenticated users.

**How to generate:**
```bash
# Generate a secure random salt
openssl rand -hex 32
```

**Set in Render:**
- Go to your Render dashboard
- Select the `omnidev-api` service
- Go to **Environment** tab
- Add: `API_KEY_SALT` = `[generated-salt]`

**Important:** Use the same salt value across all environments, or users will need to regenerate their API keys.

## Verification

After setting these variables, restart your Render service and verify:

```bash
curl https://omnidev-qbiv.onrender.com/health
```

The service should return `{"status": "healthy"}`.

## Testing Authentication

Without these variables set, you'll see:
- `503 Service Unavailable` errors when trying to authenticate
- Error message: "Supabase JWT secret not configured"

With them set correctly, authentication should work normally.
