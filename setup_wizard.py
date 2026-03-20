#!/usr/bin/env python3
"""
Job Hunt — Interactive Setup Wizard
Guides new users through setting up their profile, generating search queries,
and preparing their environment to run the job scraper.
"""

import os
import sys
import json
import time
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
ENV_EXAMPLE = ROOT_DIR / ".env.example"
CONFIG_USER = ROOT_DIR / "config_user.py"
USER_PROFILE = DATA_DIR / "user_profile.md"

# ANSI Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_step(text):
    print(f"\n{Colors.OKCYAN}-> {text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}[!] {text}{Colors.ENDC}")

def ask(question, default=""):
    prompt = f"{Colors.BOLD}{question}{Colors.ENDC}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    
    answer = input(prompt).strip()
    return answer if answer else default

def ask_yes_no(question, default="y"):
    while True:
        ans = ask(f"{question} (y/n)", default).lower()
        if ans in ['y', 'yes']:
            return True
        if ans in ['n', 'no']:
            return False
        print("Please answer 'y' or 'n'.")

def get_gemini_client():
    from google import genai
    from google.genai import types
    
    # Try to get from .env first (if they already set it up)
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key and api_key != "your_gemini_api_key_here":
        try:
            client = genai.Client(api_key=api_key)
            return client
        except Exception:
            pass
            
    # If not in env, ask for it in memory
    print_warning("I need a Gemini API key to generate your personalized search queries.")
    print("This key will only be used right now in memory, it won't be saved automatically.")
    print("You can get a free API key here: https://aistudio.google.com/app/apikey")
    
    while True:
        api_key = ask("Please paste your Gemini API key")
        if not api_key:
            print("API Key is required to continue. Press Ctrl+C to exit.")
            continue
            
        try:
            client = genai.Client(api_key=api_key)
            # Test the client
            client.models.get(model='gemini-2.5-flash')
            print_success("API Key verified successfully!")
            return client
        except Exception as e:
            print_warning(f"Invalid API key: {e}. Please try again.")

def read_resume():
    print_step("Let's grab your resume context.")
    has_resume = ask_yes_no("Do you have a resume text or markdown file ready to import?", "y")
    
    if has_resume:
        while True:
            filepath = ask("Enter the path to your resume file (e.g., data/base_resume.md)")
            path = Path(filepath.strip("'\""))
            if path.exists() and path.is_file():
                try:
                    content = path.read_text(encoding="utf-8")
                    print_success(f"Successfully loaded {len(content)} characters from your resume.")
                    return content
                except Exception as e:
                    print_warning(f"Failed to read file: {e}")
            else:
                print_warning(f"File not found: {path}. Try again or type 'skip' to enter manually.")
                if filepath.lower() == 'skip':
                    break
    
    print("\nPlease paste a brief summary of your background (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)

def generate_assets(client, is_technical, resume_text, prefs):
    print_step("Calling Gemini AI to build your profile and search queries...")
    print("This usually takes 10-20 seconds.")
    
    prompt = f"""
You are an expert technical recruiter and AI system architect setting up a job hunting system.
Based on the user's resume and preferences, generate two things:
1. A formatted markdown User Profile
2. A list of Boolean search queries to find the perfect remote jobs.

--- RESUME / BACKGROUND ---
{resume_text}

--- EXPLICIT PREFERENCES ---
Target Titles: {prefs['titles']}
Target Industry: {prefs['industry']}
Key Skills to Highlight: {prefs['skills']}
Salary Min (USD/mo): {prefs['salary']}
Work Style: {prefs['work_style']}
Avoid: {prefs['avoid']}
Seniority: {prefs['seniority']}

--- TASK 1: USER PROFILE ---
Create a crisp, highly targeted markdown profile. Use this exact format:
Name: [Infer from resume if possible, or put Your Name]
Background:
- [bullet point]
- [bullet point]
AI Skills (or Technical Skills):
- [bullet point]
- [bullet point]
Career Goals:
- Salary requirements: Minimum ${prefs['salary']} USD monthly
- Roles targeted: {prefs['titles']}
- Industry: {prefs['industry']}
- Avoid: {prefs['avoid']}

--- TASK 2: SEARCH QUERIES ---
Generate 8-12 highly specific boolean search queries for job boards.
Rules for queries:
- Must include the target roles/keywords.
- Must include 'remote' if work style contains remote.
- Must use MINUS sign (-) to exclude things in the 'Avoid' list (e.g. -sales -\"account executive\")
- Keep them varied (some broad, some niche).
- Only use standard boolean: quotes for exact match, minus for exclude. No AND/OR.
Output them as a JSON array of strings.

--- FINAL OUTPUT FORMAT ---
You MUST return ONLY a valid JSON object with exactly two keys: "profile_markdown" (string) and "search_queries" (array of strings). Do not use markdown code blocks like ```json around the response.
"""
    
    try:
        from google.genai import types
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        data = json.loads(response.text)
        print_success("AI Generation complete!")
        return data['profile_markdown'], data['search_queries']
    except Exception as e:
        print_warning(f"AI Generation failed: {e}")
        print("Falling back to empty templates.")
        return "", []

def write_files(profile_md, queries, prefs):
    DATA_DIR.mkdir(exist_ok=True)
    
    # Write Profile
    if profile_md:
        write_profile = True
        if USER_PROFILE.exists():
            write_profile = ask_yes_no(f"\n{Colors.WARNING}File {USER_PROFILE.relative_to(ROOT_DIR)} already exists. Overwrite it?{Colors.ENDC}", "n")
            
        if write_profile:
            try:
                USER_PROFILE.write_text(profile_md, encoding="utf-8")
                print_success(f"Generated user profile: {USER_PROFILE.relative_to(ROOT_DIR)}")
            except Exception as e:
                print_warning(f"Could not write user profile: {e}")
        else:
            print_warning("Skipped writing user profile. Your original file was kept.")
    
    # Write config_user.py
    if queries:
        write_config = True
        if CONFIG_USER.exists():
            write_config = ask_yes_no(f"\n{Colors.WARNING}File {CONFIG_USER.relative_to(ROOT_DIR)} already exists. Overwrite it?{Colors.ENDC}", "n")
            
        if write_config:
            config_content = f'''"""
User-specific Configuration Overrides
Generated by Setup Wizard
"""

# ─── Job Search Queries ───────────────────────────────────────────────────────
SEARCH_QUERIES = [
'''
            for q in queries:
                config_content += f'    {repr(q)},\n'
            
            config_content += f''']

# ─── Scoring & Salary Preferences ─────────────────────────────────────────────
SCORE_SHOW_THRESHOLD    = 50  # Jobs >= this appear in dashboard (0-100 scale)
SCORE_ARCHIVE_THRESHOLD = 49  # Jobs <= this are auto-archived (0-100 scale)

'''
            def_score = int(prefs['salary']) if prefs['salary'].isdigit() else 2500
            config_content += f'''MIN_SALARY_USD_MONTHLY = {def_score}
PENALIZE_MISSING_SALARY = False # Do not penalize postings with no salary info
'''
            try:
                CONFIG_USER.write_text(config_content, encoding="utf-8")
                print_success(f"Generated configuration overrides: {CONFIG_USER.relative_to(ROOT_DIR)}")
            except Exception as e:
                print_warning(f"Could not write config file: {e}")
        else:
            print_warning("Skipped writing configuration overrides. Your original config_user.py was kept.")

def run_wizard():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header("Job Hunt Dashboard - Setup Wizard")
    print("Welcome! This wizard will configure your automated job hunting system.")
    
    # Step 1: Technical Check
    is_technical = ask_yes_no("\nAre you comfortable editing Python and .env configuration files yourself?", "y")
    
    if is_technical:
        print(f"\n{Colors.OKBLUE}Running in Compact Mode for advanced users.{Colors.ENDC}")
    else:
        print(f"\n{Colors.OKBLUE}Running in Guided Mode. I'll explain everything step-by-step.{Colors.ENDC}")

    # Step 2: Resume Input
    resume_text = read_resume()
    
    # Step 3: Job Preferences Questionnaire
    print_step("Let's define what kind of jobs you actually want.")
    prefs = {}
    
    if is_technical:
        prefs['titles'] = ask("Target role titles (comma separated)")
        prefs['industry'] = ask("Target industries/sectors")
        prefs['skills'] = ask("Top 3-5 skills to highlight")
        prefs['salary'] = ask("Minimum monthly salary (USD, numbers only)", "3000")
        prefs['work_style'] = ask("Work style (remote, hybrid, onsite)", "remote")
        prefs['avoid'] = ask("Keywords/roles to avoid (e.g., sales, management)")
        prefs['seniority'] = ask("Seniority level (e.g., Senior, Lead, Mid-level)")
    else:
        print("\nWhat job titles are you aiming for? (e.g. 'Project Manager', 'Frontend Developer')")
        prefs['titles'] = ask("Titles")
        
        print("\nAre there specific industries you want to work in? (leave blank if open)")
        prefs['industry'] = ask("Industries")
        
        print("\nWhat are the absolute most important skills you want the AI to look for?")
        prefs['skills'] = ask("Skills")
        
        print("\nWhat is your minimum acceptable monthly salary in US Dollars? (just the number)")
        prefs['salary'] = ask("Min Salary USD", "3000")
        
        print("\nDo you want to work remote, hybrid, or on-site?")
        prefs['work_style'] = ask("Work style", "remote")
        
        print("\nWhat kinds of jobs do you HATE and want the AI to hide from you? (e.g. Sales, Support)")
        prefs['avoid'] = ask("Avoid")
        
        print("\nWhat is your seniority level? (e.g. Junior, Mid-Level, Senior, Director)")
        prefs['seniority'] = ask("Seniority")

    # Get Gemini Client
    client = get_gemini_client()

    # Step 4: AI Generation
    profile_md, queries = generate_assets(client, is_technical, resume_text, prefs)
    
    # Step 5: File Writes
    print_step("Writing configuration files...")
    write_files(profile_md, queries, prefs)
    
    # Step 6: Final Instructions
    print_header("Setup Complete!")
    
    if is_technical:
        print(f"""
{Colors.BOLD}Next Steps:{Colors.ENDC}
1. Copy {Colors.OKCYAN}.env.example{Colors.ENDC} to {Colors.OKCYAN}.env{Colors.ENDC} and add your GEMINI_API_KEY.
2. Put your full resume markdown into {Colors.OKCYAN}data/base_resume.md{Colors.ENDC}.
3. Run {Colors.OKGREEN}python run.py discover --deep{Colors.ENDC} to start scraping.
""")
    else:
        print(f"""
{Colors.BOLD}Almost done! You have 3 manual steps left to complete the setup:{Colors.ENDC}

{Colors.OKCYAN}Step 1: Set up your secret API Key{Colors.ENDC}
1. Look in the file explorer on the left side of VS Code.
2. Find the file named '.env.example'.
3. Right-click it, select 'Rename', and change it to exactly: .env
4. Open the new '.env' file.
5. Go to https://aistudio.google.com/app/apikey to get a free Gemini API key.
6. Replace 'your_gemini_api_key_here' in the file with your actual key and save.

{Colors.OKCYAN}Step 2: Add your full resume{Colors.ENDC}
1. In the file explorer, go into the 'data' folder.
2. Create or edit the file named 'base_resume.md'.
3. Paste your full, complete resume into this file as text. Save it.

{Colors.OKCYAN}Step 3: Start hunting!{Colors.ENDC}
1. Go to the top menu bar in VS Code: Terminal → Run Task...
2. Select '🚀 Discover & Score Jobs'.
3. The system will start searching the internet and scoring jobs for you!
""")

if __name__ == "__main__":
    try:
        run_wizard()
    except KeyboardInterrupt:
        print("\n\nSetup aborted by user. run `python setup_wizard.py` to try again.")
        sys.exit(1)
