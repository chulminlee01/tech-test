# Deployment Guide

This document provides step-by-step instructions for deploying the Tech Test Generator to Railway or Vercel.

---

## 🚂 Railway Deployment (Recommended)

**Railway is the recommended platform** because:
- ✅ Supports long-running processes
- ✅ Better for traditional Flask applications
- ✅ Handles file storage naturally
- ✅ Supports background jobs
- ✅ Easy environment variable management

### Prerequisites
- GitHub account
- Railway account (sign up at https://railway.app)

### Step 1: Prepare Your Repository

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Railway

1. **Go to Railway**: https://railway.app
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your repository**
5. **Railway will auto-detect** Python and use the configurations

### Step 3: Configure Environment Variables

In Railway dashboard, add these environment variables:

```bash
# Required
NVIDIA_API_KEY=your_nvidia_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id

# Optional (has defaults)
DEFAULT_MODEL=minimaxai/minimax-m2
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_TEMPERATURE=0.7
AGENT_MAX_ITERATIONS=8
```

### Step 4: Deploy

1. Railway will automatically deploy
2. Wait for build to complete (2-3 minutes)
3. Your app will be available at: `https://your-app.up.railway.app`

### Step 5: Enable Custom Domain (Optional)

1. In Railway dashboard, go to **Settings**
2. Click **Domains**
3. Add your custom domain
4. Update DNS records as instructed

---

## ⚡ Vercel Deployment (Alternative)

**⚠️ Important Limitations:**
- File storage is ephemeral (files deleted after function execution)
- Background jobs have timeout limits (300 seconds max)
- Better suited for stateless applications

**Note**: This app works better on Railway, but Vercel can be used for demos.

### Step 1: Prepare Repository

Same as Railway - push your code to GitHub.

### Step 2: Deploy to Vercel

1. **Go to Vercel**: https://vercel.com
2. **Import your repository**
3. **Configure project**:
   - Framework Preset: `Other`
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   - Install Command: `pip install -r requirements.txt`

### Step 3: Configure Environment Variables

In Vercel dashboard, add environment variables:

```bash
NVIDIA_API_KEY=your_nvidia_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
DEFAULT_MODEL=minimaxai/minimax-m2
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_TEMPERATURE=0.7
AGENT_MAX_ITERATIONS=8
```

### Step 4: Deploy

1. Click **Deploy**
2. Wait for deployment (2-3 minutes)
3. Your app will be available at: `https://your-app.vercel.app`

### Vercel Limitations

⚠️ **File Storage**: Generated files in `/output` are temporary and will be lost
⚠️ **Function Timeout**: Max 300 seconds (5 minutes) - may timeout for complex generations
⚠️ **Background Jobs**: Not fully supported in serverless environment

**Solution**: Consider using external storage (AWS S3, Cloudinary) for production.

---

## 📋 Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `NVIDIA_API_KEY` | ✅ Yes | NVIDIA API key for LLM | - |
| `GOOGLE_API_KEY` | ✅ Yes | Google Custom Search API key | - |
| `GOOGLE_CSE_ID` | ✅ Yes | Google Custom Search Engine ID | - |
| `DEFAULT_MODEL` | No | LLM model to use | `minimaxai/minimax-m2` |
| `NVIDIA_BASE_URL` | No | NVIDIA API base URL | `https://integrate.api.nvidia.com/v1` |
| `OPENAI_TEMPERATURE` | No | LLM temperature (0.0-1.0) | `0.7` |
| `AGENT_MAX_ITERATIONS` | No | Max agent iterations | `8` |
| `PORT` | No | Server port | `8080` |

---

## 🔧 Troubleshooting

### Railway Issues

**Build Fails**
- Check that `requirements.txt` is present
- Verify Python version in `runtime.txt` is supported
- Check Railway build logs for specific errors

**App Crashes on Start**
- Verify environment variables are set correctly
- Check Railway deployment logs
- Ensure `gunicorn` is in `requirements.txt`

**Timeout Errors**
- Increase worker timeout in `Procfile` (currently 300s)
- Check if API keys are valid and have quota

### Vercel Issues

**Function Timeout**
- Vercel has a 300-second limit for Pro plan
- Consider using Railway for long-running operations

**File Not Found**
- Files in `/output` are temporary on Vercel
- Use external storage for production

**Build Errors**
- Check `vercel.json` configuration
- Verify Python version compatibility
- Check Vercel function logs

---

## 🚀 Quick Deploy Commands

### Railway CLI
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

---

## 📊 Platform Comparison

| Feature | Railway | Vercel |
|---------|---------|--------|
| **Flask Support** | ✅ Excellent | ⚠️ Limited |
| **File Storage** | ✅ Persistent | ❌ Ephemeral |
| **Background Jobs** | ✅ Full Support | ⚠️ Limited |
| **Max Duration** | ⏱️ No limit | ⏱️ 300s (Pro) |
| **Cost** | 💰 $5/month | 💰 Free tier available |
| **Setup Difficulty** | 😊 Easy | 😐 Moderate |
| **Best For** | Full web apps | Stateless APIs |

**Recommendation**: Use **Railway** for this application.

---

## 🆘 Support

For deployment issues:
- Railway: https://docs.railway.app
- Vercel: https://vercel.com/docs

For application issues:
- Check server logs in platform dashboard
- Verify API keys are correct
- Ensure all environment variables are set

