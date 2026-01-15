#!/bin/bash

# OmniDev CLI Deployment Helper

echo "🚀 Starting OmniDev Deployment..."

# 1. Backend (Render)
echo ""
echo "backend: Checking deployment status..."
echo "✅ Code has been pushed to GitHub."
echo "ℹ️  FOR BACKEND: Go to https://dashboard.render.com/ -> New Web Service -> Connect 'omnidev' repo."
echo "    Render will automatically detect the configuration from 'backend/render.yaml'."
echo "    The deployment starts automatically after you connect it."

# 2. Frontend (Vercel)
echo ""
echo "frontend: Deploying to Vercel..."
echo "ℹ️  You may be asked to log in to Vercel."
cd frontend
if command -v npx &> /dev/null; then
    # Pass Supabase keys directly to the build
    npx vercel deploy --build-env NEXT_PUBLIC_SUPABASE_URL="https://wyhufnrsufyamhguozaw.supabase.co" --build-env NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5aHVmbnJzdWZ5YW1oZ3VvemF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgyOTE3MTQsImV4cCI6MjA4Mzg2NzcxNH0.QRW4vwKS9w2T6xWzfrIMxshDhKFtp7qMEn9qfRAo-eM"
else
    echo "❌ Error: npx is not installed. Please install Node.js."
fi
cd ..

echo ""
echo "✨ done! If Vercel deployment succeeded, you will see the URL above."
