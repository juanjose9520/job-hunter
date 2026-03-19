"""
Job Hunt System — Central Configuration
All user preferences, search queries, and scoring parameters live here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API ─────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = "gemini-3-flash-preview"
GEMINI_FALLBACK_MODEL = "gemini-3.1-flash-lite-preview"  # Used if 429 rate limit is hit

# ─── Paths ────────────────────────────────────────────────────────────────────
import pathlib
ROOT_DIR       = pathlib.Path(__file__).parent
DATA_DIR       = ROOT_DIR / "data"
OUTPUT_DIR     = ROOT_DIR / "output" / "resumes"
LINKEDIN_OUT   = ROOT_DIR / "output" / "linkedin_rewrite.md"
DB_PATH        = DATA_DIR / "jobs.db"
BASE_RESUME    = DATA_DIR / "base_resume.md"
SKILLS_LOG     = DATA_DIR / "skills_log.json"
PERSONAL_INFO  = DATA_DIR / ".personal_info"
DASHBOARD_DIR  = ROOT_DIR / "dashboard"

# ─── User Profile Brief (injected into all AI prompts) ───────────────────────
USER_PROFILE_PATH = DATA_DIR / "user_profile.md"
if USER_PROFILE_PATH.exists():
    USER_PROFILE = USER_PROFILE_PATH.read_text(encoding="utf-8")
else:
    USER_PROFILE = """
Name: [Your Name]

Background:
- [Your experience 1]
- [Your experience 2]

AI Skills:
- [Your skills]

Career Goals:
- [Salary requirements]
- [Roles targeted]
- [Avoid]
"""

# ─── Job Search Queries ───────────────────────────────────────────────────────
SEARCH_QUERIES = [
    '"clinical AI" remote',
    '"health AI" remote',
    '"medical AI" remote -engineer -developer -software',
    '"AI healthcare" "prompt engineering" remote',
    '"clinical informatics" AI remote',
    '"clinical operations" AI remote',
    '"physician" AI remote "non-clinical"',
    '"MD" "healthcare AI" remote -clinical',
    '"medical doctor" AI remote',
    '"health informatics" AI remote',
    '"healthcare AI" "product" remote',
    '"AI" "clinical documentation" remote',
    '"healthcare operations" AI remote',
]

# ─── Scoring Thresholds ───────────────────────────────────────────────────────
SCORE_SHOW_THRESHOLD    = 50  # Jobs >= this appear in dashboard (0-100 scale)
SCORE_ARCHIVE_THRESHOLD = 49  # Jobs <= this are auto-archived (0-100 scale)

# ─── Salary Preferences ──────────────────────────────────────────────────────
MIN_SALARY_USD_MONTHLY = 2500   # Minimum acceptable salary
PENALIZE_MISSING_SALARY = False # Do not penalize postings with no salary info


# ─── Job Boards ───────────────────────────────────────────────────────────────
JOB_BOARDS = {
    "remotive": {
        "enabled": True,
        "type": "api",
        "url": "https://remotive.com/api/remote-jobs",
        "categories": ["product", "health", "business"],
    },
    "weworkremotely": {
        "enabled": True,
        "type": "rss",
        "feeds": [
            "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
            "https://weworkremotely.com/categories/remote-product-jobs.rss",
        ],
    },
    "linkedin": {
        "enabled": True,
        "type": "scrape",
        "base_url": "https://www.linkedin.com/jobs/search/",
        "params": {"f_WT": "2", "f_JT": "F"},  # remote, full-time
    },
    "himss": {
        "enabled": False,
        "type": "scrape",
        "base_url": "https://jobs.himss.org/jobs/",
        "params": {"keywords": "AI", "remote": "1"},
    },
    "healthcareitjobs": {
        "enabled": True,
        "type": "scrape",
        "base_url": "https://www.healthcareitjobs.com/jobs/",
        "params": {"q": "AI remote"},
    },
    "wellfound": {
        "enabled": True,
        "type": "scrape",
        "base_url": "https://wellfound.com/jobs/",
        "params": {"role": "Product Manager", "remote": "true"},
    },
}
