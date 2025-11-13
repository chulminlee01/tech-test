# 🚀 Tech Test Generator - Quick Start Guide

Welcome! This guide will help you get started with the Tech Test Generator.

---

## 📋 What is This?

An AI-powered web application that generates comprehensive technical assessments using:
- **7 AI Agents** working together (CrewAI framework)
- **NVIDIA minimax-m2** for intelligent content generation
- **Google Custom Search** for industry research
- **Beautiful web portal** for candidates

---

## ⚡ Quick Start (Local Development)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Make sure your `.env` file has these keys:
```bash
NVIDIA_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_cse_id_here
```

### 3. Run the Application
```bash
python3 app.py
```

### 4. Open in Browser
Visit: **http://localhost:8080**

---

## 🌐 Deploy to Production

### Option 1: Railway (Recommended) 🚂

**Easiest way:**
1. Push code to GitHub
2. Go to https://railway.app
3. Click "New Project" → "Deploy from GitHub"
4. Add environment variables
5. Done! ✅

**Or use CLI:**
```bash
./deploy_railway.sh
```

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed instructions.

### Option 2: Vercel ⚡

1. Push code to GitHub
2. Go to https://vercel.com
3. Import project
4. Add environment variables
5. Deploy

**Note**: Railway is better for this app (supports file storage & long jobs).

---

## 📚 Documentation

- **[README.md](README.md)** - Full project documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed deployment guide
- **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Step-by-step checklist

---

## 🎯 How to Use

1. **Select Job Details**
   - Choose role (iOS Developer, Backend, etc.)
   - Select level (Junior, Senior, etc.)
   - Pick language (Korean, English, etc.)

2. **Generate**
   - Click "Generate Tech Test"
   - Wait 4-6 minutes
   - Watch AI agents collaborate

3. **View Results**
   - Click "View Generated Tech Test"
   - Share the portal URL with candidates
   - All materials included (assignments, datasets, starter code)

---

## 🤖 What Gets Generated?

- ✅ Technical assignments (3-5 tasks)
- ✅ Realistic datasets for testing
- ✅ Starter code templates
- ✅ Beautiful web portal
- ✅ Research report
- ✅ Design documentation

---

## 🔑 Required API Keys

### 1. NVIDIA API Key
- Sign up: https://build.nvidia.com
- Create API key
- Free tier available

### 2. Google Custom Search
- Go to: https://console.cloud.google.com
- Enable Custom Search API
- Create API key
- Set up Custom Search Engine: https://programmablesearchengine.google.com

---

## ⚙️ Project Structure

```
tech_test2/
├── app.py                  # Flask web application
├── crewai_working.py      # CrewAI orchestrator
├── agent_*.py             # Individual agents
├── templates/
│   └── index.html         # Main web interface
├── output/                # Generated assignments
├── requirements.txt       # Dependencies
└── .env                   # API keys (don't commit!)
```

---

## 🆘 Troubleshooting

**"ModuleNotFoundError: No module named 'faker'"**
```bash
pip install Faker
```

**"Port 8080 already in use"**
```bash
lsof -ti:8080 | xargs kill -9
```

**"API key invalid"**
- Check `.env` file has correct keys
- Verify keys are active and have quota
- No extra spaces in key values

**"Generation times out"**
- Normal for complex roles (takes 4-6 minutes)
- Check API keys are valid
- Check network connection

---

## 🎨 Tech Stack

- **Backend**: Flask (Python)
- **AI Framework**: CrewAI
- **LLM**: NVIDIA minimax-m2
- **Search**: Google Custom Search
- **Frontend**: Vanilla JS + CSS
- **Deployment**: Railway / Vercel

---

## 🚀 Ready to Deploy?

1. ✅ Test locally first: `python3 app.py`
2. ✅ Read: **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)**
3. ✅ Follow: **[DEPLOYMENT.md](DEPLOYMENT.md)**
4. ✅ Use script: `./deploy_railway.sh`

---

## 📞 Need Help?

- Check **[DEPLOYMENT.md](DEPLOYMENT.md)** for deployment issues
- Review **[README.md](README.md)** for usage questions
- Check Railway/Vercel docs for platform-specific issues

---

## ✨ Quick Commands Reference

```bash
# Start local server
python3 app.py

# Install dependencies
pip install -r requirements.txt

# Deploy to Railway (with CLI)
./deploy_railway.sh

# Check if port is in use
lsof -ti:8080

# Stop server on port 8080
lsof -ti:8080 | xargs kill -9
```

---

**🎉 You're all set! Start generating amazing tech tests!**
