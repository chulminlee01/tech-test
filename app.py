"""
Flask Web Application for Tech Test Generator
Provides a web interface to generate tech assignments using CrewAI orchestrator.
"""

import os
import sys
import io
import json
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, Response

from crewai_working import generate_with_crewai
from agent_starter_code import run_starter_code_generator
from agent_web_designer import run_web_designer

app = Flask(__name__)

# Ensure output directory exists
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Store generation status
generation_status = {}

# Agent definitions for UI (7 agents: 4 CrewAI + 3 post-processing)
AGENTS = [
    {"id": "pm", "name": "Product Manager", "icon": "👔", "role": "Team Leader & Coordinator"},
    {"id": "researcher", "name": "Research Analyst", "icon": "🔍", "role": "Industry Research"},
    {"id": "designer", "name": "Assignment Designer", "icon": "✏️", "role": "Question Creation"},
    {"id": "reviewer", "name": "QA Reviewer", "icon": "🔎", "role": "Quality Assurance"},
    {"id": "data", "name": "Data Provider", "icon": "📊", "role": "Dataset Generation"},
    {"id": "builder", "name": "Web Builder", "icon": "🌐", "role": "Portal Creation"},
    {"id": "styler", "name": "Web Designer", "icon": "🎨", "role": "Styling & Design"},
]


class LogCapture(io.StringIO):
    """Capture stdout/stderr and store in generation status."""
    
    def __init__(self, job_id):
        super().__init__()
        self.job_id = job_id
        self.buffer = []
        
    def write(self, text):
        if text and text.strip():
            # Clean the text before storing
            cleaned_text = self._clean_ansi(text)
            if cleaned_text.strip():
                self.buffer.append(cleaned_text)
                # Update generation status with cleaned log line
                if self.job_id in generation_status:
                    if 'logs' not in generation_status[self.job_id]:
                        generation_status[self.job_id]['logs'] = []
                    generation_status[self.job_id]['logs'].append(cleaned_text)
        return len(text)
    
    def flush(self):
        pass
    
    @staticmethod
    def _clean_ansi(text):
        """Remove ANSI color codes and box-drawing characters, keep only content."""
        import re
        
        # Remove ANSI escape sequences (color codes)
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        text = re.sub(r'\[[\d;]+m', '', text)
        
        # Remove box-drawing characters
        box_chars = ['╭', '╮', '╯', '╰', '─', '│', '├', '┤', '┬', '┴', '┼', '═', '╠', '╣', '╦', '╩', '╬']
        for char in box_chars:
            text = text.replace(char, '')
        
        # Split into lines and filter
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Skip pure decoration lines
            if all(c in '─═│╭╮╯╰├┤┬┴┼ \t-_' for c in stripped):
                continue
            
            # Skip CrewAI box headers/footers
            if any(marker in stripped for marker in [
                'Crew Execution Started',
                'Crew Execution Completed',
                'Crew Failure',
                'Task Completion',
                'Task Failure',
                'Memory Retrieval',
                'Tool Args:',
                'ID:', 
                'Name:',
            ]) and len(stripped) < 50:
                continue
            
            # Extract actual content (remove leading/trailing decoration)
            content = stripped.strip('│├┤╭╮╰╯─═ \t')
            
            if content:
                cleaned_lines.append(content)
        
        result = '\n'.join(cleaned_lines)
        
        # Remove excessive blank lines
        result = re.sub(r'\n\n\n+', '\n\n', result)
        
        return result


def run_generation(job_id, job_role, job_level, language):
    """Run the orchestrator in a background thread."""
    global generation_status
    
    try:
        # Update status to running (already initialized in /api/generate)
        if job_id in generation_status:
            generation_status[job_id]["status"] = "running"
            generation_status[job_id]["progress"] = "Initializing agents..."
        
        # Capture stdout and stderr
        log_capture = LogCapture(job_id)
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        # Redirect stdout/stderr to capture logs
        sys.stdout = log_capture
        sys.stderr = log_capture
        
        # Create output directory
        output_root = Path("output")
        output_root.mkdir(exist_ok=True)
        
        # Create job-specific directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_role = job_role.lower().replace(" ", "_")
        safe_level = job_level.lower().replace(" ", "_").replace("-", "_")
        job_dir = output_root / f"{safe_role}_{safe_level}_{timestamp}"
        job_dir.mkdir(parents=True, exist_ok=True)
        
        generation_status[job_id]["progress"] = "PM initializing team..."
        generation_status[job_id]["active_agent"] = "pm"
        generation_status[job_id]["agent_status"] = {agent["id"]: "pending" for agent in AGENTS}
        generation_status[job_id]["agent_status"]["pm"] = "active"
        
        # Run CrewAI team collaboration
        generation_status[job_id]["progress"] = "CrewAI team collaborating..."
        result = generate_with_crewai(
            job_role=job_role,
            job_level=job_level,
            language=language,
            output_root=str(job_dir)
        )
        
        # Post-processing: Generate starter code and styling
        assignments_path = Path(job_dir) / "assignments.json"
        html_path = Path(job_dir) / "index.html"
        
        if assignments_path.exists():
            generation_status[job_id]["progress"] = "Generating starter code..."
            try:
                run_starter_code_generator(
                    assignments_path=str(assignments_path),
                    output_dir=str(Path(job_dir) / "starter_code")
                )
            except Exception as e:
                print(f"⚠️  Starter code error: {e}", flush=True)
        
        if html_path.exists():
            generation_status[job_id]["progress"] = "Applying custom styling..."
            try:
                run_web_designer(
                    html_path=str(html_path),
                    css_output=str(Path(job_dir) / "styles.css"),
                    notes_output=str(Path(job_dir) / "design_notes.md"),
                    language=language
                )
            except Exception as e:
                print(f"⚠️  Web designer error: {e}", flush=True)
        
        # Success
        generation_status[job_id].update({
            "status": "completed",
            "progress": "Generation complete!",
            "output_dir": str(job_dir),
            "completed_at": datetime.now().isoformat(),
            "index_url": f"/output/{job_dir.name}/index.html"
        })
        
    except Exception as e:
        generation_status[job_id].update({
            "status": "failed",
            "progress": f"Error: {str(e)}",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr


@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html", agents=AGENTS)


@app.route("/api/agents")
def get_agents():
    """Get list of agents."""
    return jsonify({
        "success": True,
        "agents": AGENTS
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    """Start tech test generation."""
    try:
        data = request.json
        
        if not data:
            print("[API] ERROR: No JSON data received", flush=True)
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        job_role = data.get("job_role")
        job_level = data.get("job_level")
        language = data.get("language", "Korean")
        
        print(f"[API] Received request: role={job_role}, level={job_level}, lang={language}", flush=True)
        
        if not job_role or not job_level:
            print("[API] ERROR: Missing required fields", flush=True)
            return jsonify({
                "success": False,
                "error": "Job role and level are required"
            }), 400
        
        # Generate unique job ID
        job_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{abs(hash(job_role + job_level)) % 10000}"
        
        print(f"[API] Starting generation for job_id={job_id}", flush=True)
        
        # Initialize status immediately (before thread starts)
        generation_status[job_id] = {
            "status": "initializing",
            "progress": "Starting background process...",
            "output_dir": None,
            "error": None,
            "logs": [],
            "started_at": datetime.now().isoformat()
        }
        
        # Start generation in background thread
        thread = threading.Thread(
            target=run_generation,
            args=(job_id, job_role, job_level, language),
            name=f"Generation-{job_id}"
        )
        thread.daemon = True
        thread.start()
        
        print(f"[API] Thread started successfully for job_id={job_id}", flush=True)
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "message": "Generation started"
        })
        
    except Exception as e:
        print(f"[API] EXCEPTION in generate endpoint: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/status/<job_id>")
def status(job_id):
    """Get generation status."""
    if job_id not in generation_status:
        print(f"[API] Status check failed - job_id not found: {job_id}", flush=True)
        print(f"[API] Available job_ids: {list(generation_status.keys())}", flush=True)
        return jsonify({
            "success": False,
            "error": "Job not found",
            "job_id": job_id,
            "available_jobs": list(generation_status.keys())
        }), 404
    
    return jsonify({
        "success": True,
        "status": generation_status[job_id]
    })


@app.route("/api/logs/<job_id>")
def get_logs(job_id):
    """Get generation logs."""
    if job_id not in generation_status:
        return jsonify({
            "success": False,
            "error": "Job not found"
        }), 404
    
    logs = generation_status[job_id].get('logs', [])
    return jsonify({
        "success": True,
        "logs": logs,
        "count": len(logs)
    })


@app.route("/output/<path:filename>")
def output_files(filename):
    """Serve generated output files with proper MIME types."""
    try:
        response = send_from_directory("output", filename)
        
        # Set proper MIME types for common files
        if filename.endswith('.html'):
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
        elif filename.endswith('.css'):
            response.headers['Content-Type'] = 'text/css; charset=utf-8'
        elif filename.endswith('.js'):
            response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        elif filename.endswith('.json'):
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
        elif filename.endswith('.md'):
            response.headers['Content-Type'] = 'text/markdown; charset=utf-8'
        elif filename.endswith('.csv'):
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        elif filename.endswith('.swift'):
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        
        # Add cache control headers
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": f"File not found: {filename}"
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error serving file: {str(e)}"
        }), 500


@app.route("/api/jobs")
def list_jobs():
    """List all generation jobs."""
    jobs = []
    for job_id, status_info in generation_status.items():
        jobs.append({
            "job_id": job_id,
            **status_info
        })
    
    # Sort by started time (newest first)
    jobs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    return jsonify({
        "success": True,
        "jobs": jobs
    })


if __name__ == "__main__":
    # Use PORT environment variable for Railway/Heroku compatibility
    port = int(os.getenv("PORT", 8080))
    
    print("=" * 70)
    print("🚀 Tech Test Generator Web App")
    print("=" * 70)
    print(f"📍 Server: http://0.0.0.0:{port}")
    print("🎨 Using Myrealtrip branding")
    print("🤖 Powered by NVIDIA minimax-m2 & CrewAI")
    print("=" * 70)
    if port == 8080:
        print("⚠️  Note: Using port 8080 (port 5000 is used by macOS AirPlay)")
        print("=" * 70)
    print()
    
    app.run(debug=False, host="0.0.0.0", port=port)

