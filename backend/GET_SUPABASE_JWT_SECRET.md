# How to Get SUPABASE_JWT_SECRET

## Quick Steps

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Sign in to your account

2. **Select Your Project**
   - Click on your OmniDev project (or create one if you haven't)

3. **Navigate to Settings**
   - Click on the **Settings** icon (gear icon) in the left sidebar
   - Click on **API** in the settings menu

4. **Find JWT Secret**
   - Scroll down to the **JWT Settings** section
   - Look for **JWT Secret** field
   - Click the **Reveal** button or **Copy** button to copy the secret
   - It will look something like: `your-super-secret-jwt-token-with-at-least-32-characters-long`

5. **Set in Render**
   - Go to Render Dashboard: https://dashboard.render.com
   - Select your `omnidev-api` service
   - Go to **Environment** tab
   - Click **Add Environment Variable**
   - Key: `SUPABASE_JWT_SECRET`
   - Value: Paste the JWT Secret you copied
   - Click **Save Changes**
   - **Restart** your service

## Note

You do **NOT** need:
- ❌ Key ID
- ❌ Discovery URL  
- ❌ Public Key (JWK format)

These are for JWKS (JSON Web Key Set) verification, which we're not using. We only need the **JWT Secret** for HS256 algorithm verification.

## Generate API_KEY_SALT

While you're at it, also generate the API_KEY_SALT:

```bash
openssl rand -hex 32
```

Then set it in Render as `API_KEY_SALT` with the generated value.
