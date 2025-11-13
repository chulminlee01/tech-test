#!/bin/bash

# Railway Deployment Script for Tech Test Generator
# This script helps you deploy to Railway in a few simple steps

echo "========================================================================"
echo "🚂 Railway Deployment Helper"
echo "========================================================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
    echo ""
fi

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "⚠️  Warning: .gitignore not found!"
    echo "Please create .gitignore to avoid committing sensitive data."
    echo ""
fi

# Check if changes need to be committed
if [[ -n $(git status -s) ]]; then
    echo "📝 Committing changes..."
    git add .
    git commit -m "Prepare for Railway deployment"
    echo "✅ Changes committed"
    echo ""
else
    echo "✅ No changes to commit"
    echo ""
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "⚠️  Railway CLI not found!"
    echo ""
    echo "Install it with:"
    echo "  npm i -g @railway/cli"
    echo ""
    echo "Or deploy manually at: https://railway.app"
    echo ""
    exit 1
fi

echo "🚀 Railway CLI found!"
echo ""

# Login check
echo "🔐 Checking Railway login status..."
railway whoami &> /dev/null
if [ $? -ne 0 ]; then
    echo "Please login to Railway:"
    railway login
else
    echo "✅ Already logged in to Railway"
fi
echo ""

# Deploy
echo "========================================================================"
echo "🚀 Starting Deployment..."
echo "========================================================================"
echo ""
echo "Choose deployment method:"
echo "  1) Create new Railway project and deploy"
echo "  2) Deploy to existing linked project"
echo "  3) Just show instructions (manual deployment)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Creating new Railway project..."
        railway init
        echo ""
        echo "Deploying..."
        railway up
        echo ""
        echo "✅ Deployment initiated!"
        echo ""
        echo "Next steps:"
        echo "1. Go to https://railway.app/dashboard"
        echo "2. Add environment variables (NVIDIA_API_KEY, GOOGLE_API_KEY, etc.)"
        echo "3. Redeploy if needed"
        ;;
    2)
        echo ""
        echo "Deploying to linked project..."
        railway up
        echo ""
        echo "✅ Deployment initiated!"
        ;;
    3)
        echo ""
        echo "========================================================================"
        echo "📖 Manual Deployment Instructions"
        echo "========================================================================"
        echo ""
        echo "1. Push your code to GitHub:"
        echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
        echo "   git push -u origin main"
        echo ""
        echo "2. Go to https://railway.app"
        echo "3. Click 'New Project' → 'Deploy from GitHub repo'"
        echo "4. Select your repository"
        echo "5. Add environment variables:"
        echo "   - NVIDIA_API_KEY"
        echo "   - GOOGLE_API_KEY"
        echo "   - GOOGLE_CSE_ID"
        echo "6. Deploy!"
        echo ""
        echo "For detailed instructions, see DEPLOYMENT.md"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "✅ Done!"
echo "========================================================================"
echo ""
echo "📚 For more information, see DEPLOYMENT.md"
echo ""

