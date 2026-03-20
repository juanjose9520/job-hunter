"""
Script to fetch remote jobs from free JSON APIs and format them for our database.
Supported APIs: Remotive, Himalayas, Jobicy, Arbeitnow
"""
import requests
import json
import sys
import pathlib

# Ensure we can import config & database from the root dir
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import scripts.database as database

# Keywords used to pre-filter jobs from APIs that don't support category filtering.
# A job passes if its title OR description contains at least one of these terms.
HEALTH_AI_KEYWORDS = [
    "health", "healthcare", "medical", "clinical", "physician", "hospital",
    "patient", "care", "biotech", "pharma", "life science", "genomic",
    "radiology", "pathology", "ehr", "epic", "fhir", "telehealth",
    "ai", "artificial intelligence", "machine learning", "llm", "nlp",
    "prompt", "generative", "informatics",
]

def _is_health_ai_relevant(title: str, description: str) -> bool:
    """Return True if the job title or description contains a health/AI keyword."""
    text = (title + " " + description).lower()
    return any(kw in text for kw in HEALTH_AI_KEYWORDS)

def fetch_remotive():
    """Fetch jobs from Remotive API — health and product/AI categories."""
    categories = ["health", "product"]
    total_retrieved = 0
    added = 0
    for category in categories:
        url = f"https://remotive.com/api/remote-jobs?category={category}&limit=50"
        print(f"[API: Remotive] Fetching from {url}...")
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            jobs = data.get('jobs', [])
            total_retrieved += len(jobs)
            for j in jobs:
                salary = str(j.get('salary', ''))
                job_dict = {
                    "title": j.get('title', 'Unknown Title'),
                    "company": j.get('company_name', 'Unknown Company'),
                    "url": j.get('url', ''),
                    "board": "remotive",
                    "description": j.get('description', ''),
                    "salary_raw": salary if salary else None,
                    "salary_monthly": None,
                    "salary_listed": 1 if salary else 0,
                    "remote": 1
                }
                if job_dict["url"]:
                    if database.upsert_job(job_dict):
                        added += 1
        except Exception as e:
            print(f"[API: Remotive] Error fetching category '{category}': {e}")
    print(f"[API: Remotive] Added {added} new unique jobs out of {total_retrieved} retrieved")

def fetch_himalayas():
    """Fetch jobs from Himalayas API, filtered to health/AI relevant roles."""
    url = "https://himalayas.app/jobs/api?limit=100"
    print(f"[API: Himalayas] Fetching from {url}...")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        jobs = data.get('jobs', [])
        added = 0
        skipped = 0
        for j in jobs:
            title = j.get('title', '')
            description = j.get('description', '')
            if not _is_health_ai_relevant(title, description):
                skipped += 1
                continue

            salary = ""
            if j.get('minSalary') and j.get('maxSalary'):
                salary = f"${j.get('minSalary')} - ${j.get('maxSalary')}"

            job_dict = {
                "title": title,
                "company": j.get('companyName', 'Unknown Company'),
                "url": j.get('applicationLink', ''),
                "board": "himalayas",
                "description": description,
                "salary_raw": salary if salary else None,
                "salary_monthly": None,
                "salary_listed": 1 if salary else 0,
                "remote": 1
            }
            if job_dict["url"]:
                if database.upsert_job(job_dict):
                    added += 1
        print(f"[API: Himalayas] Added {added} new unique jobs out of {len(jobs)} retrieved ({skipped} filtered out as non-health/AI)")
    except Exception as e:
         print(f"[API: Himalayas] Error: {e}")

def fetch_jobicy():
    """Fetch jobs from Jobicy API — healthcare and IT industries."""
    industries = ["healthcare", "it"]
    total_retrieved = 0
    added = 0
    for industry in industries:
        url = f"https://jobicy.com/api/v2/remote-jobs?count=50&industry={industry}"
        print(f"[API: Jobicy] Fetching from {url}...")
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            jobs = data.get('jobs', [])
            total_retrieved += len(jobs)
            for j in jobs:
                salary = str(j.get('annualSalaryMin', '')) + " - " + str(j.get('annualSalaryMax', ''))
                if salary == ' - ' or salary == 'None - None':
                    salary = ""

                job_dict = {
                    "title": j.get('jobTitle', 'Unknown Title'),
                    "company": j.get('companyName', 'Unknown Company'),
                    "url": j.get('url', ''),
                    "board": "jobicy",
                    "description": j.get('jobDescription', ''),
                    "salary_raw": salary if salary else None,
                    "salary_monthly": None,
                    "salary_listed": 1 if salary else 0,
                    "remote": 1
                }
                if job_dict["url"]:
                    if database.upsert_job(job_dict):
                        added += 1
        except Exception as e:
            print(f"[API: Jobicy] Error fetching industry '{industry}': {e}")
    print(f"[API: Jobicy] Added {added} new unique jobs out of {total_retrieved} retrieved")

def fetch_arbeitnow():
    """Fetch jobs from Arbeitnow, filtered to health/AI relevant remote roles."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    print(f"[API: Arbeitnow] Fetching from {url}...")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        jobs = data.get('data', [])
        added = 0
        skipped = 0
        for j in jobs:
            if not j.get('remote', False):
                continue

            title = j.get('title', '')
            description = j.get('description', '')
            if not _is_health_ai_relevant(title, description):
                skipped += 1
                continue

            job_dict = {
                "title": title,
                "company": j.get('company_name', 'Unknown Company'),
                "url": j.get('url', ''),
                "board": "arbeitnow",
                "description": description,
                "salary_raw": None,
                "salary_monthly": None,
                "salary_listed": 0,
                "remote": 1
            }
            if job_dict["url"]:
                if database.upsert_job(job_dict):
                    added += 1
        print(f"[API: Arbeitnow] Added {added} new unique remote jobs out of {len(jobs)} retrieved ({skipped} filtered out as non-health/AI)")
    except Exception as e:
         print(f"[API: Arbeitnow] Error: {e}")

def fetch_adzuna():
    print("[API: Adzuna] Adzuna requires APP_ID and APP_KEY. Skipping for now until configured by user.")
    pass

def run_all_apis():
    print("[Job APIs] Starting fetches from free endpoints...")
    fetch_remotive()
    fetch_himalayas()
    fetch_jobicy()
    fetch_arbeitnow()
    fetch_adzuna()
    print("\n[Job APIs] Completed fetching from all endpoints.")

if __name__ == "__main__":
    run_all_apis()
