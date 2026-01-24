# OmniDev End-to-End Testing Checklist

**Date:** 2026-01-21  
**Purpose:** Pre-demo verification for tomorrow's presentation

## 🔍 Pre-Testing Requirements

### Required Credentials/Data Needed:

1. **Supabase Configuration** (REQUIRED)
   - [ ] `NEXT_PUBLIC_SUPABASE_URL` - Set in Vercel
   - [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Set in Vercel
   - [ ] `SUPABASE_JWT_SECRET` - Set in Render backend

2. **Backend Environment Variables** (Set in Render)
   - [ ] `SUPABASE_JWT_SECRET` - From Supabase Dashboard > Settings > API > JWT Secret
   - [ ] `API_KEY_SALT` - Generated with `openssl rand -hex 32`
   - [ ] `OPENAI_API_KEY` - Optional, for AI features
   - [ ] `AWS_ACCESS_KEY_ID` - Optional, for DevOps/Storage
   - [ ] `AWS_SECRET_ACCESS_KEY` - Optional, for DevOps/Storage
   - [ ] `FRONTEND_URL` - Should be `https://omnidev-flame.vercel.app`

3. **Test User Account**
   - [ ] Create a test account in Supabase (or use existing)
   - [ ] Note: Admin role needed for `/devops` and `/storage` pages

---

## ✅ Deployment Verification

### Backend (Render)
- [x] Backend URL: `https://omnidev-qbiv.onrender.com`
- [x] Health check: `/health` returns `{"status":"healthy"}`
- [ ] Verify `SUPABASE_JWT_SECRET` is set in Render
- [ ] Verify `API_KEY_SALT` is set in Render
- [ ] Verify `FRONTEND_URL` points to Vercel URL

### Frontend (Vercel)
- [x] Frontend URL: `https://omnidev-flame.vercel.app` (Production domain)
- [ ] Verify `NEXT_PUBLIC_SUPABASE_URL` is set in Vercel
- [ ] Verify `NEXT_PUBLIC_SUPABASE_ANON_KEY` is set in Vercel
- [ ] Verify latest code is deployed (check git commit)
- [ ] Verify `vercel.json` rewrites are working

---

## 🧪 End-to-End Test Scenarios

### 1. Authentication Flow

#### Signup
- [ ] Navigate to `/auth/signup`
- [ ] Fill in email and password
- [ ] Submit form
- [ ] Verify redirect to home page
- [ ] Verify user is logged in

#### Login
- [ ] Navigate to `/auth/login`
- [ ] Enter credentials
- [ ] Submit form
- [ ] Verify redirect to home page
- [ ] Verify session persists on refresh

#### Logout
- [ ] Click logout
- [ ] Verify redirect to login page
- [ ] Verify protected routes redirect to login

#### Protected Routes
- [ ] Try accessing `/chat` without login → should redirect to login
- [ ] Try accessing `/settings` without login → should redirect to login
- [ ] After login, verify all routes are accessible

---

### 2. Landing Page (`/`)

- [ ] Page loads without errors
- [ ] Hero section displays correctly
- [ ] Tech stack marquee animates
- [ ] Features section displays all 6 features
- [ ] Platform section displays correctly
- [ ] CTA section is visible
- [ ] Footer displays correctly
- [ ] All links work
- [ ] Responsive on mobile

---

### 3. AI Chat (`/chat`)

**Prerequisites:**
- [ ] User is logged in
- [ ] API key generated (from Settings page)
- [ ] Optional: OpenAI API key set in Settings

**Tests:**
- [ ] Page loads
- [ ] Chat interface displays
- [ ] Send a message: "Hello, what can you do?"
- [ ] Verify response is received
- [ ] Verify message history persists
- [ ] Test with user's OpenAI API key (if set)
- [ ] Test without OpenAI key (should use server default if configured)

---

### 4. Vision Analysis (`/vision`)

**Prerequisites:**
- [ ] User is logged in
- [ ] API key generated
- [ ] Optional: OpenAI API key set

**Tests:**
- [ ] Page loads
- [ ] Upload an image file
- [ ] Click "Analyze Image"
- [ ] Verify analysis results display
- [ ] Verify error handling for invalid files
- [ ] Test with user's OpenAI API key (if set)

---

### 5. Web Scraper (`/scraper`)

**Prerequisites:**
- [ ] User is logged in
- [ ] API key generated

**Tests:**
- [ ] Page loads
- [ ] Enter a URL (e.g., `https://example.com`)
- [ ] Click "Start Scraping"
- [ ] Verify scraping starts
- [ ] Verify results display
- [ ] Verify error handling for invalid URLs
- [ ] Test screenshot feature (if available)

---

### 6. Location Services (`/location`)

**Prerequisites:**
- [ ] User is logged in
- [ ] API key generated
- [ ] Optional: Google Maps API key set

**Tests:**
- [ ] Page loads
- [ ] Test "Get Current Location" button
- [ ] Test reverse geocoding (enter lat/lng)
- [ ] Test location search (e.g., "Mumbai")
- [ ] Test nearby search
- [ ] Verify results display correctly
- [ ] Test with Google Maps API key (if set)

---

### 7. DevOps Agent (`/devops`) - Admin Only

**Prerequisites:**
- [ ] User is logged in with **admin** role
- [ ] API key generated
- [ ] Optional: AWS credentials set

**Tests:**
- [ ] Page loads (admin role required)
- [ ] View capabilities list
- [ ] Test a command: "List my EC2 instances"
- [ ] Verify response
- [ ] Test with AWS credentials (if set)
- [ ] Verify error handling

**Note:** If user doesn't have admin role, should redirect to login with error.

---

### 8. Cloud Storage (`/storage`) - Admin Only

**Prerequisites:**
- [ ] User is logged in with **admin** role
- [ ] API key generated
- [ ] Optional: AWS credentials set

**Tests:**
- [ ] Page loads (admin role required)
- [ ] List S3 buckets
- [ ] Select a bucket
- [ ] List objects in bucket
- [ ] Upload a file
- [ ] Download a file
- [ ] Delete a file
- [ ] Verify error handling

**Note:** If user doesn't have admin role, should redirect to login with error.

---

### 9. Settings Page (`/settings`)

**Prerequisites:**
- [ ] User is logged in

**Tests:**
- [ ] Page loads
- [ ] Generate API Key button works
- [ ] API key is generated and displayed
- [ ] API key is saved to localStorage
- [ ] Set OpenAI API key
- [ ] Set Google Maps API key
- [ ] Verify settings persist after refresh
- [ ] Verify settings are used in other pages

---

### 10. API Integration Tests

**Test Backend API Directly:**

```bash
# Health check
curl https://omnidev-qbiv.onrender.com/health

# Test with auth (replace TOKEN and API_KEY)
curl -X POST https://omnidev-qbiv.onrender.com/api/ai/chat \
  -H "Authorization: Bearer <TOKEN>" \
  -H "X-API-Key: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'
```

- [ ] Backend health check works
- [ ] API endpoints respond correctly
- [ ] Authentication works
- [ ] API key validation works
- [ ] CORS is configured correctly

---

## 🐛 Common Issues to Check

### Frontend Issues
- [ ] No console errors in browser
- [ ] No 404 errors for assets
- [ ] No CORS errors
- [ ] No authentication errors
- [ ] No API key errors
- [ ] All images load correctly
- [ ] All fonts load correctly

### Backend Issues
- [ ] No 503 errors (check SUPABASE_JWT_SECRET is set)
- [ ] No 401 errors (check authentication)
- [ ] No 403 errors (check API key)
- [ ] No 500 errors (check logs)

### Deployment Issues
- [ ] Vercel rewrites work correctly
- [ ] Backend URL is correct in `vercel.json`
- [ ] Environment variables are set in both Vercel and Render
- [ ] Latest code is deployed

---

## 📋 Quick Verification Commands

```bash
# Check backend health
curl https://omnidev-qbiv.onrender.com/health

# Check frontend is accessible
curl -I https://omnidev-flame.vercel.app
# Note: May require Vercel authentication if password protection is enabled

# Check git is synced
git status
git log --oneline -5

# Check Vercel deployment
cd frontend && vercel ls

# Check latest deployment
cd frontend && vercel inspect omnidev
```

---

## 🎯 Demo Flow (Recommended Order)

1. **Landing Page** - Show the beautiful UI
2. **Signup/Login** - Create account or login
3. **Settings** - Generate API key
4. **AI Chat** - Show AI capabilities
5. **Vision** - Upload and analyze an image
6. **Scraper** - Scrape a website
7. **Location** - Show location services
8. **DevOps** (if admin) - Show cloud automation
9. **Storage** (if admin) - Show S3 integration

---

## ⚠️ Critical Items for Tomorrow

1. **MUST HAVE:**
   - [ ] Supabase credentials configured in Vercel
   - [ ] Backend JWT secret configured in Render
   - [ ] Backend API key salt configured in Render
   - [ ] At least one test user account created
   - [ ] API key generated for test user

2. **NICE TO HAVE:**
   - [ ] OpenAI API key (for AI features demo)
   - [ ] AWS credentials (for DevOps/Storage demo)
   - [ ] Google Maps API key (for better location results)
   - [ ] Admin role user (for DevOps/Storage pages)

---

## 📝 Notes

- All user API keys are generated from Settings page
- API keys are stored in browser localStorage
- Backend validates both JWT token and API key
- Some features work without external API keys (using server defaults)
- Admin role is required for `/devops` and `/storage` pages

---

## ✅ Final Checklist Before Demo

- [ ] All critical environment variables are set
- [ ] Backend is healthy and responding
- [ ] Frontend is deployed and accessible
- [ ] Test user account exists
- [ ] API key is generated
- [ ] All major features tested
- [ ] No critical errors in console
- [ ] Demo flow is practiced
- [ ] Backup plan if something fails

---

**Last Updated:** 2026-01-21  
**Status:** Ready for testing
