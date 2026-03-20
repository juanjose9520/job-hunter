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
# Targeting: physician transitioning to AI leadership/senior roles — fully remote.
# Exclusions: -sales -"account executive" -"account manager" remove patient-facing roles.
SEARCH_QUERIES = [
    # Leadership / Director roles
    '"clinical AI lead" remote',
    '"medical director" AI remote -"patient care"',
    '"head of clinical" AI remote',
    '"director of clinical" AI remote',
    '"VP clinical" AI remote',
    '"clinical transformation" AI remote',
    '"director" "healthcare AI" remote',
    '"head of medical affairs" AI remote',
    '"director of medical AI" remote',

    # Program / Product management
    '"clinical product manager" AI remote',
    '"AI program manager" healthcare remote',
    '"healthcare AI" "product manager" remote',
    '"AI" "clinical operations" manager remote',

    # Senior IC roles
    '"senior clinical AI" remote',
    '"principal clinical" AI remote',
    '"clinical AI architect" remote',
    '"senior healthcare AI" remote',
    '"senior medical affairs" AI remote',

    # Physician-specific crossover
    '"physician" AI remote "non-clinical" -sales',
    '"MD" "healthcare AI" remote -sales',
    '"medical doctor" AI remote -"patient care"',

    # General clinical AI (kept from before)
    '"clinical informatics" AI remote',
    '"health informatics" AI remote',
    '"AI" "clinical documentation" remote',
]

# ─── Scoring Thresholds ───────────────────────────────────────────────────────
SCORE_SHOW_THRESHOLD    = 50  # Jobs >= this appear in dashboard (0-100 scale)
SCORE_ARCHIVE_THRESHOLD = 49  # Jobs <= this are auto-archived (0-100 scale)

# ─── Salary Preferences ──────────────────────────────────────────────────────
MIN_SALARY_USD_MONTHLY = 2500   # Minimum acceptable salary
PENALIZE_MISSING_SALARY = False # Do not penalize postings with no salary info

# ─── Load User Overrides ──────────────────────────────────────────────────────
# Automatically import generated settings from config_user.py if it exists
try:
    from config_user import (
        SEARCH_QUERIES as USER_SEARCH_QUERIES,
        SCORE_SHOW_THRESHOLD as USER_SHOW_THRESHOLD,
        SCORE_ARCHIVE_THRESHOLD as USER_ARCHIVE_THRESHOLD,
        MIN_SALARY_USD_MONTHLY as USER_MIN_SALARY
    )
    
    # Overwrite defaults with user specs
    SEARCH_QUERIES = USER_SEARCH_QUERIES
    SCORE_SHOW_THRESHOLD = USER_SHOW_THRESHOLD
    SCORE_ARCHIVE_THRESHOLD = USER_ARCHIVE_THRESHOLD
    MIN_SALARY_USD_MONTHLY = USER_MIN_SALARY
except ImportError:
    pass  # No user configuration found, stick to defaults.


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
