"""
Working CrewAI Implementation with True Collaboration
PM initializes → Research → Team Discussion → Question Creation → Review → Finalize
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from agent_researcher import recent_google_search
from agent_data_provider import run_data_provider
from agent_web_builder import run_web_builder
from crewai.tools import BaseTool


# ============================================================================
# Global Variables for Tool Access
# ============================================================================

CURRENT_RESEARCH_PATH = None
CURRENT_ASSIGNMENTS_PATH = None


# ============================================================================
# CrewAI Tools
# ============================================================================

class GoogleCSETool(BaseTool):
    name: str = "google_cse_search"
    description: str = "Search Google Custom Search Engine for recent information. Use this to research coding assignment best practices, industry trends, and technical hiring standards. Input should be your search query as a string."
    
    def _run(self, query: str) -> str:
        """Execute Google CSE search."""
        print(f"\n🔍 [Research Analyst] Executing Google CSE search: '{query[:60]}...'\n", flush=True)
        result = recent_google_search(query)
        print(f"\n✅ [Research Analyst] Search completed - found results\n", flush=True)
        return result


# ============================================================================
# Create Agents
# ============================================================================

def create_working_agents(llm):
    """Create all agents for the team."""
    
    pm = Agent(
        role="Product Manager",
        goal="Lead the team to create high-quality tech assignments",
        backstory="""You are the PM at Myrealtrip. You coordinate the team, make decisions, 
        and ensure quality. You delegate tasks and lead discussions.""",
        verbose=True,
        allow_delegation=True,
        llm=llm
    )
    
    researcher = Agent(
        role="Research Analyst", 
        goal="Research industry best practices for tech assignments using Google Search",
        backstory="""You are a research expert who uses Google Custom Search to find recent information.
        You MUST perform actual web searches using the google_cse_search tool. You analyze 
        multiple sources and provide data-driven recommendations.""",
        verbose=True,
        llm=llm,
        tools=[GoogleCSETool()],  # Give the tool!
        function_calling_llm=llm
    )
    
    designer = Agent(
        role="Assignment Designer",
        goal="Create 5 unique coding assignments based on team discussion",
        backstory="""You design coding assignments. You participate in team discussions about 
        what skills to test, then create detailed assignment specifications in JSON format.""",
        verbose=True,
        llm=llm
    )
    
    reviewer = Agent(
        role="QA Reviewer",
        goal="Review assignments and provide feedback",
        backstory="""You review the quality of assignments. You check if they test the right 
        skills and provide constructive feedback.""",
        verbose=True,
        llm=llm
    )
    
    tech_writer = Agent(
        role="Technical Writer",
        goal="Ensure documentation quality and clarity",
        backstory="""You review documentation for clarity and completeness. You ensure 
        requirements are well-written and candidates can understand them.""",
        verbose=True,
        llm=llm
    )
    
    return pm, researcher, designer, reviewer, tech_writer


# ============================================================================
# Create Tasks with Proper Dependencies
# ============================================================================

def run_working_crewai(
    job_role: str,
    job_level: str,
    language: str,
    output_dir: Path
) -> Dict:
    """Run working CrewAI with proper collaboration."""
    
    global CURRENT_RESEARCH_PATH, CURRENT_ASSIGNMENTS_PATH
    
    load_dotenv()
    
    # Setup paths
    CURRENT_RESEARCH_PATH = str(output_dir / "research_report.txt")
    CURRENT_ASSIGNMENTS_PATH = str(output_dir / "assignments.json")
    
    # Configure LLM (use OpenRouter for CrewAI compatibility)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError("OPENROUTER_API_KEY required for CrewAI")
    
    os.environ["OPENAI_API_KEY"] = openrouter_key
    os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    
    print("=" * 70)
    print("🎯 CrewAI Team-Based Generation")
    print("=" * 70)
    print(f"✨ Using OpenRouter (CrewAI-compatible)")
    print(f"   Model: openrouter/deepseek/deepseek-chat")
    print()
    
    llm = ChatOpenAI(
        model="openrouter/deepseek/deepseek-chat",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key
    )
    
    # Create agents (Technical Writer optional - not needed for core workflow)
    pm, researcher, designer, reviewer, tech_writer = create_working_agents(llm)
    
    print("👥 Team Assembled:")
    print(f"   👔 {pm.role}")
    print(f"   🔍 {researcher.role}")
    print(f"   ✏️ {designer.role}")
    print(f"   🔎 {reviewer.role}")
    print()
    
    # Task 1: PM Initialization & Research Delegation
    task1 = Task(
        description=f"""You are the PM. Initialize the project to create tech assignments for {job_level} {job_role}.

STEP 1: Project Kickoff
Say: "Team, we're creating tech assignments for {job_level} {job_role} at Myrealtrip OTA company. 
Let's start with research to understand current industry standards."

STEP 2: Delegate to Researcher
Use your team to research. The researcher should investigate:
- Industry best practices for {job_role} take-home assignments
- Expected skill sets for {job_level} level
- Evaluation criteria used by OTA companies
- Current trends in technical hiring

Provide a brief kickoff message and delegation instruction.""",
        expected_output="PM kickoff message and research delegation confirmation",
        agent=pm
    )
    
    # Task 2: Research Execution
    task2 = Task(
        description=f"""You are the Research Analyst. The PM has asked you to research best practices 
for {job_level} {job_role} take-home coding assignments in OTA companies.

YOU MUST USE THE google_cse_search TOOL to perform these searches:

REQUIRED SEARCHES (use the tool for each):
1. Use google_cse_search with query: "{job_role} take-home assignment best practices 2024"
2. Use google_cse_search with query: "{job_level} level coding interview expectations OTA"  
3. Use google_cse_search with query: "{job_role} technical skills evaluation criteria"
4. Use google_cse_search with query: "OTA travel company coding assignment examples"

After each search, say what you found.

Then write: 
"🔍 [Research Analyst] RESEARCH SUMMARY:

Based on my Google CSE searches, here are the key findings:

**Key Skills for {job_level} {job_role}:**
- [List 5-7 technical skills found in sources]

**Assignment Characteristics:**
- [Typical scope, timeline, complexity]

**Evaluation Criteria:**
- [What companies look for]

**Recommendations for Myrealtrip:**
- [3-5 specific recommendations]

Sources: [List source URLs from search results]"

This will be discussed with the team next.
""",
        expected_output=f"Research summary with findings from Google CSE searches, listing key skills, assignment characteristics, and specific recommendations",
        agent=researcher,
        context=[task1]
    )
    
    # Task 3: Team Discussion (PM leads)
    task3 = Task(
        description=f"""You are the PM leading a team discussion about the research findings.

READ the research findings carefully and lead a discussion with your team.

FORMAT YOUR OUTPUT AS A DISCUSSION (replace ALL [...] with actual content):

"👔 [PM] Based on the research, here are the key findings: [write 3 ACTUAL key points from the research report, like "SwiftUI is industry standard", "Senior level expects architecture decisions", etc.]

👔 [PM] Team, let's discuss what we should test for {job_level} {job_role}:
- What technical skills are most critical based on research?
- What OTA-specific scenarios should we include?
- What's the appropriate difficulty level for {job_level}?

✏️ [Assignment Designer] Based on the research, I recommend we test:
- [Write ACTUAL skill like "SwiftUI"] because [write ACTUAL reason like "research shows it's industry standard in 2024"]
- [Write ACTUAL skill like "Async/await networking"] because [write ACTUAL reason]  
- [Write ACTUAL skill like "Data persistence"] because [write ACTUAL reason]
For OTA scenarios, I suggest: [write 2-3 ACTUAL scenarios like "hotel search interface", "flight booking flow", "review submission"]

🔎 [QA Reviewer] For {job_level} level, we should also consider:
- [Write ACTUAL skill or concern like "Architectural pattern choices (MVVM vs VIPER)"]
- [Write ACTUAL quality aspect like "Unit testing and code coverage"]

👔 [PM] CONSENSUS REACHED:
We will test these 5 key areas:
1. [Write ACTUAL area like "SwiftUI fundamentals and modern UI patterns"]
2. [Write ACTUAL area like "Networking with async/await"]
3. [Write ACTUAL area like "Data modeling and Core Data/SwiftData"]
4. [Write ACTUAL area like "OTA-specific booking and search flows"]
5. [Write ACTUAL area like "Architecture, testing, and code quality"]

Assignment Designer, please create 5 unique assignments covering these areas."

IMPORTANT: DO NOT use placeholder text like [Skill 1] or [reason]. Write the ACTUAL skills, reasons, and scenarios based on what you learned from the research report.""",
        expected_output="Formatted team discussion with ACTUAL skills, scenarios, and recommendations (no placeholders), ending with consensus on 5 specific skill areas to test",
        agent=pm,
        context=[task2]
    )
    
    # Task 4: Assignment Creation (based on discussion)
    task4 = Task(
        description=f"""You are the Assignment Designer. Based on the team discussion, create 5 unique coding assignments.

CONTEXT: The team discussed and agreed on skills to test (from previous discussion).

CREATE 5 ASSIGNMENTS for {job_level} {job_role} that test:
- Different technical skills (from discussion)
- OTA product scenarios (hotels, flights, reviews, bookings, recommendations)
- Real-world challenges

FOR EACH ASSIGNMENT:
1. Title and mission statement (in {language})
2. Technical requirements (3-5 specific requirements)
3. Dataset needed (name, format, columns, record count)
4. Evaluation criteria (4-6 points)
5. Discussion questions (3 questions)

FORMAT AS JSON:
{{
  "company": "Myrealtrip OTA Company",
  "job_role": "{job_role}",
  "job_level": "{job_level}",
  "assignments": [
    {{
      "id": "OTA-001",
      "title": "...",
      "mission": "...",
      "requirements": ["...", "...", "..."],
      "datasets": [{{"name": "...", "format": "csv", "records": 100, "columns": []}}],
      "evaluation": ["...", "..."],
      "discussion_questions": ["?", "?", "?"]
    }}
  ]
}}

Save using: "SAVE_ASSIGNMENTS: [your complete JSON]"
""",
        expected_output=f"5 complete assignments in JSON format aligned with team discussion",
        agent=designer,
        context=[task3]
    )
    
    # Task 5: Quality Review
    task5 = Task(
        description=f"""You are the QA Reviewer. Review the 5 assignments created by the designer.

CHECK:
1. Do assignments test the skills agreed in team discussion?
2. Is difficulty appropriate for {job_level} level?
3. Are requirements clear and achievable?
4. Do datasets make sense for each assignment?

PROVIDE FEEDBACK:
If excellent: "APPROVED - All 5 assignments meet quality standards. They effectively test [list key skills]."

If issues: "NEEDS REVISION - 
- Assignment #X: [specific issue]
- Assignment #Y: [specific issue]
Please update these and resubmit."

Be constructive and specific.""",
        expected_output="Quality review with APPROVED or specific revision requests",
        agent=reviewer,
        context=[task4]
    )
    
    # Task 6: PM Final Decision
    task6 = Task(
        description=f"""You are the PM. Review the QA feedback and make final decision.

IF APPROVED by QA:
- Confirm approval
- Thank the team
- Provide final sign-off

IF REVISIONS NEEDED:
- Review the feedback
- Decide if revisions are necessary
- If yes: "Team, please address these concerns: [list them]"
- If minor: "These are acceptable, let's proceed"

FINAL OUTPUT:
"DECISION: [APPROVED or NEEDS_REVISION]
SUMMARY: [What was accomplished and quality assessment]
READY FOR DELIVERY: [YES or NO]"

Provide your final PM decision.""",
        expected_output="PM final decision (APPROVED/NEEDS_REVISION) with clear direction",
        agent=pm,
        context=[task5]
    )
    
    # Create crew (4 agents: PM, Researcher, Designer, Reviewer)
    print("📋 Tasks Defined:")
    print(f"   1. PM Initialization & Delegation")
    print(f"   2. Research Execution (Google CSE)")
    print(f"   3. Team Discussion (PM leads)")
    print(f"   4. Assignment Creation (Designer)")
    print(f"   5. Quality Review (QA Reviewer)")
    print(f"   6. PM Final Decision")
    print()
    print("🚀 Initializing CrewAI Team (4 core agents)...")
    print()
    
    crew = Crew(
        agents=[pm, researcher, designer, reviewer],
        tasks=[task1, task2, task3, task4, task5, task6],
        process=Process.sequential,
        verbose=True
    )
    
    print("=" * 70)
    print("🎬 Starting Team Collaboration...")
    print("=" * 70)
    print()
    
    # Execute
    result = crew.kickoff()
    
    print()
    print("=" * 70)
    print("✅ Team Collaboration Complete")
    print("=" * 70)
    print()
    
    # Save research output to file
    result_text = str(result)
    
    # Extract research content (before discussion section)
    research_lines = []
    for line in result_text.split('\n'):
        if '[PM]' in line and 'discuss' in line.lower():
            break  # Stop at discussion phase
        if line.strip():
            research_lines.append(line)
    
    if research_lines:
        research_content = '\n'.join(research_lines)
        Path(CURRENT_RESEARCH_PATH).write_text(research_content, encoding="utf-8")
        print(f"✅ Research saved to: {CURRENT_RESEARCH_PATH}")
    
    # For assignments, use the proven agent_question_generator
    print()
    print("📝 Generating structured assignments using proven generator...")
    try:
        from agent_question_generator import run_question_generator
        
        # Get job info from paths
        parts = str(output_dir).split('/')
        job_info = parts[-1] if parts else ""
        
        run_question_generator(
            job_role=job_role,
            job_level=job_level,
            company_name="Myrealtrip OTA Company",
            input_path=CURRENT_RESEARCH_PATH,
            output_path=CURRENT_ASSIGNMENTS_PATH,
            language=language
        )
        print(f"✅ Assignments generated and saved")
    except Exception as e:
        print(f"⚠️  Assignment generation error: {e}")
    
    # Post-processing: Generate datasets
    if Path(CURRENT_ASSIGNMENTS_PATH).exists():
        print()
        print("📊 Generating datasets...")
        try:
            run_data_provider(
                assignments_path=CURRENT_ASSIGNMENTS_PATH,
                output_dir=str(output_dir / "datasets"),
                language=language
            )
        except Exception as e:
            print(f"⚠️  Dataset generation error: {e}")
        
        print("🌐 Building web portal...")
        try:
            run_web_builder(
                assignments_path=CURRENT_ASSIGNMENTS_PATH,
                research_summary_path=CURRENT_RESEARCH_PATH,
                output_html=str(output_dir / "index.html"),
                language=language,
                starter_dir=str(output_dir / "starter_code")
            )
        except Exception as e:
            print(f"⚠️  Web builder error: {e}")
    
    return {
        "status": "completed",
        "result": result_text,
        "output_dir": str(output_dir)
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def generate_with_crewai(
    job_role: str,
    job_level: str = "Senior",
    language: str = "Korean",
    output_root: str = "output"
) -> Dict:
    """Generate tech test with CrewAI team collaboration."""
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_role = job_role.lower().replace(" ", "_")
    safe_level = job_level.lower().replace(" ", "_")
    
    output_dir = Path(output_root) / f"{safe_role}_{safe_level}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output: {output_dir}")
    print()
    
    return run_working_crewai(
        job_role=job_role,
        job_level=job_level,
        language=language,
        output_dir=output_dir
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-role", default="iOS Developer")
    parser.add_argument("--job-level", default="Senior")
    parser.add_argument("--language", default="Korean")
    parser.add_argument("--output-root", default="output")
    
    args = parser.parse_args()
    
    result = generate_with_crewai(
        job_role=args.job_role,
        job_level=args.job_level,
        language=args.language,
        output_root=args.output_root
    )
    
    print()
    print("✅ Complete!")
    print(f"📂 Output: {result['output_dir']}")

