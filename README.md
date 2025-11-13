# Tech Test Generator

AI-powered web application for generating comprehensive technical assessments using CrewAI and NVIDIA minimax-m2.

## 🚀 Features

- **Multi-Agent System**: 7 specialized AI agents working together
  - Product Manager (PM) - Team coordination
  - Research Analyst - Industry research
  - Assignment Designer - Question creation
  - QA Reviewer - Quality assurance
  - Data Provider - Dataset generation
  - Web Builder - Portal creation
  - Web Designer - Styling & design

- **Comprehensive Output**:
  - Technical assignments with detailed requirements
  - Realistic datasets for testing
  - Starter code templates
  - Beautiful web portal with all materials
  - Research reports

- **Multi-language Support**: Korean, English, Japanese, Chinese

## 📁 Project Structure

```
tech_test2/
├── app.py                      # Flask web application
├── crewai_working.py          # CrewAI orchestrator
├── llm_client.py              # LLM client (NVIDIA minimax-m2)
├── agent_*.py                 # Individual agent implementations
├── templates/
│   └── index.html             # Main web interface
├── output/                    # Generated assignments (gitignored content)
│   └── .gitkeep
├── .env                       # API keys and configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   cd /path/to/project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   - Copy `.env` file and add your API keys:
     - `NVIDIA_API_KEY` - NVIDIA API key
     - `GOOGLE_API_KEY` - Google Custom Search API key
     - `GOOGLE_CSE_ID` - Google Custom Search Engine ID

## 🚀 Running the Application

Start the Flask development server:

```bash
python3 app.py
```

The application will be available at:
- **http://localhost:8080**

## 📝 Usage

1. Open http://localhost:8080 in your browser
2. Select a job role (e.g., iOS Developer, Backend Developer)
3. Choose the job level (Junior, Mid-level, Senior, etc.)
4. Select the language for the assignment
5. Click "Generate Tech Test"
6. Wait 4-6 minutes for the AI agents to complete the generation
7. Click "View Generated Tech Test" to see the results

## 🎯 Generated Output

Each generation creates a folder in `output/` with:
- `index.html` - Interactive web portal
- `assignments.json` - Structured assignment data
- `assignments.md` - Markdown version
- `research_report.txt` - Industry research findings
- `datasets/` - Realistic test datasets
- `starter_code/` - Code templates (if applicable)
- `styles.css` - Custom styling
- `design_notes.md` - Design documentation

## 🔧 API Endpoints

- `GET /` - Main web interface
- `POST /api/generate` - Start generation job
- `GET /api/status/<job_id>` - Check job status
- `GET /api/logs/<job_id>` - Get generation logs
- `GET /api/agents` - List all agents
- `GET /api/jobs` - List all jobs
- `GET /output/<path>` - Serve generated files

## 🤖 Technology Stack

- **Backend**: Flask (Python 3.11+)
- **AI Framework**: CrewAI 0.203.1
- **LLM**: NVIDIA minimax-m2 (via NVIDIA API)
- **Research**: Google Custom Search API
- **Data Generation**: Faker library

## ⚙️ Configuration

Key environment variables in `.env`:

```bash
# Primary LLM (NVIDIA)
NVIDIA_API_KEY=your_key_here
DEFAULT_MODEL=minimaxai/minimax-m2
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# Google Search (for research)
GOOGLE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_cse_id_here

# LLM Parameters
OPENAI_TEMPERATURE=0.7
AGENT_MAX_ITERATIONS=8
```

## 📄 License

Copyright © 2025 Myrealtrip. All Rights Reserved.

## 🙏 Acknowledgments

- Powered by NVIDIA minimax-m2
- Built with CrewAI framework
- Uses Google Custom Search for research
