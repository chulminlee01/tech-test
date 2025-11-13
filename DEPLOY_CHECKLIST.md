# 🚀 Deployment Checklist

Use this checklist to ensure smooth deployment to Railway or Vercel.

## ✅ Pre-Deployment Checklist

### 1. Code Preparation
- [ ] All code is committed to Git
- [ ] `.gitignore` is configured (don't commit `.env`)
- [ ] `requirements.txt` includes all dependencies
- [ ] Test the app locally (`python3 app.py`)

### 2. Environment Variables Ready
- [ ] `NVIDIA_API_KEY` - Get from https://build.nvidia.com
- [ ] `GOOGLE_API_KEY` - Get from Google Cloud Console
- [ ] `GOOGLE_CSE_ID` - Get from Google Programmable Search Engine
- [ ] Copy values from your `.env` file

### 3. Repository Setup
- [ ] Code pushed to GitHub
- [ ] Repository is public or you have connected it to Railway/Vercel
- [ ] All necessary files are included:
  - `app.py`
  - `requirements.txt`
  - `Procfile` (Railway)
  - `railway.json` (Railway)
  - `vercel.json` (Vercel)
  - `runtime.txt`

---

## 🚂 Railway Deployment Steps

### Quick Deploy (Easiest)
1. [ ] Go to https://railway.app
2. [ ] Click "New Project"
3. [ ] Select "Deploy from GitHub repo"
4. [ ] Choose your repository
5. [ ] Wait for auto-detection (should detect Python)
6. [ ] Go to "Variables" tab
7. [ ] Add environment variables:
   ```
   NVIDIA_API_KEY=your_key
   GOOGLE_API_KEY=your_key
   GOOGLE_CSE_ID=your_id
   ```
8. [ ] Railway will auto-deploy
9. [ ] Click "Generate Domain" for public URL
10. [ ] Test your deployment!

### CLI Deploy (Advanced)
1. [ ] Install Railway CLI: `npm i -g @railway/cli`
2. [ ] Login: `railway login`
3. [ ] Run: `./deploy_railway.sh`
4. [ ] Add environment variables in dashboard
5. [ ] Done!

---

## ⚡ Vercel Deployment Steps

### Quick Deploy
1. [ ] Go to https://vercel.com
2. [ ] Click "Import Project"
3. [ ] Select your GitHub repository
4. [ ] Configure:
   - Framework: `Other`
   - Build Command: (leave empty)
   - Install Command: `pip install -r requirements.txt`
5. [ ] Add environment variables in "Environment Variables" section
6. [ ] Click "Deploy"
7. [ ] Test your deployment!

### CLI Deploy (Advanced)
1. [ ] Install Vercel CLI: `npm i -g vercel`
2. [ ] Login: `vercel login`
3. [ ] Run: `vercel --prod`
4. [ ] Add environment variables when prompted
5. [ ] Done!

---

## 🧪 Post-Deployment Testing

### 1. Basic Health Check
- [ ] Visit your deployment URL
- [ ] Main page loads correctly
- [ ] No console errors in browser (F12)

### 2. Functionality Test
- [ ] Can select job role and level
- [ ] Can click "Generate Tech Test" button
- [ ] Generation starts (check status updates)
- [ ] Wait 5-6 minutes for completion
- [ ] "View Generated Tech Test" link appears
- [ ] Click link opens index.html correctly
- [ ] Generated content displays properly

### 3. API Endpoints Test
```bash
# Replace YOUR_DOMAIN with your deployment URL
curl https://YOUR_DOMAIN.railway.app/api/agents
curl https://YOUR_DOMAIN.railway.app/api/jobs
```

---

## 🔧 Troubleshooting

### Railway Issues

**"Application failed to start"**
- Check environment variables are set
- Check Railway logs for errors
- Verify `gunicorn` is in `requirements.txt`

**"502 Bad Gateway"**
- App might be starting (wait 30 seconds)
- Check if PORT variable is used correctly
- Check deployment logs

**"Build failed"**
- Check `requirements.txt` syntax
- Verify Python version in `runtime.txt`
- Check Railway build logs

### Vercel Issues

**"Function timeout"**
- Vercel has 300s limit
- Generation might be too long
- Consider using Railway instead

**"Generated files not found"**
- Vercel has ephemeral storage
- Files are deleted after function execution
- Use Railway for file persistence

---

## 📊 Deployment Status

### Railway
- [ ] Deployed successfully
- [ ] Environment variables configured
- [ ] Custom domain set up (optional)
- [ ] SSL certificate active (automatic)
- [ ] Tested and working

### Vercel  
- [ ] Deployed successfully
- [ ] Environment variables configured
- [ ] Custom domain set up (optional)
- [ ] SSL certificate active (automatic)
- [ ] Tested and working

---

## 🎯 Recommended: Railway

**Why Railway?**
- ✅ Better for Flask apps
- ✅ Persistent file storage
- ✅ No function timeout limits
- ✅ Easier configuration
- ✅ Full background job support

**When to use Vercel?**
- Only for demos or testing
- If you add external storage (S3)
- For read-only operations

---

## 📚 Resources

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Full Guide**: See `DEPLOYMENT.md`
- **Support**: Check platform status pages

---

## ✅ Final Checklist

Before going live:
- [ ] App works locally
- [ ] All environment variables set
- [ ] Test generation completes successfully
- [ ] Files serve correctly
- [ ] No errors in logs
- [ ] Share URL with team!

**Your deployment URL**: ___________________________

