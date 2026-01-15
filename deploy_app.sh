#!/bin/bash

# OmniDev Full Deploy Script
# Commits, pushes, and deploys to both Render (backend) and Vercel (frontend)

set -e

echo "🚀 OmniDev Full Deployment"
echo "=========================="

# Step 1: Git commit and push
echo ""
echo "📦 Step 1: Committing & Pushing to GitHub..."
if [ -n "$(git status --porcelain)" ]; then
    git add .
    read -p "Enter commit message (or press Enter for default): " msg
    msg=${msg:-"Update OmniDev application"}
    git commit -m "$msg"
    git push origin main
    echo "✅ Pushed to GitHub"
else
    echo "ℹ️  No changes to commit"
fi

# Step 2: Backend (Render auto-deploys on push if configured)
echo ""
echo "🖥️  Step 2: Backend (Render)"
echo "   Render auto-deploys on push if 'Auto-Deploy' is enabled."
echo "   If not enabled, go to: https://dashboard.render.com → Your Service → Manual Deploy"

# Step 3: Frontend (Vercel)
echo ""
echo "🌐 Step 3: Deploying Frontend to Vercel..."
cd frontend
if command -v npx &> /dev/null; then
    npx vercel --prod --yes \
        --build-env NEXT_PUBLIC_SUPABASE_URL="https://wyhufnrsufyamhguozaw.supabase.co" \
        --build-env NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5aHVmbnJzdWZ5YW1oZ3VvemF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgyOTE3MTQsImV4cCI6MjA4Mzg2NzcxNH0.QRW4vwKS9w2T6xWzfrIMxshDhKFtp7qMEn9qfRAo-eM"
    echo "✅ Frontend deployed to Vercel"
else
    echo "❌ Error: npx not found. Install Node.js first."
    exit 1
fi
cd ..

echo ""
echo "✨ Deployment Complete!"
echo "   Frontend: Check Vercel output above for URL"
echo "   Backend: https://omnidev-qbiv.onrender.com"
