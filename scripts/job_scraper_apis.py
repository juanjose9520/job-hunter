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

def fetch_remotive():
    """Fetch jobs from Remotive API (focuses on tech jobs)"""
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=50"
    print(f"[API: Remotive] Fetching from {url}...")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        jobs = data.get('jobs', [])
        added = 0
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
        print(f"[API: Remotive] Added {added} new unique jobs out of {len(jobs)} retrieved")
    except Exception as e:
         print(f"[API: Remotive] Error: {e}")

def fetch_himalayas():
    """Fetch jobs from Himalayas API"""
    url = "https://himalayas.app/jobs/api?limit=50"
    print(f"[API: Himalayas] Fetching from {url}...")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        jobs = data.get('jobs', [])
        added = 0
        for j in jobs:
            salary = ""
            if j.get('minSalary') and j.get('maxSalary'):
                salary = f"${j.get('minSalary')} - ${j.get('maxSalary')}"
                
            job_dict = {
                "title": j.get('title', 'Unknown Title'),
                "company": j.get('companyName', 'Unknown Company'),
                "url": j.get('applicationLink', ''),
                "board": "himalayas",
                "description": j.get('description', ''),
                "salary_raw": salary if salary else None,
                "salary_monthly": None,
                "salary_listed": 1 if salary else 0,
                "remote": 1
            }
            if job_dict["url"]:
                if database.upsert_job(job_dict):
                    added += 1
        print(f"[API: Himalayas] Added {added} new unique jobs out of {len(jobs)} retrieved")
    except Exception as e:
         print(f"[API: Himalayas] Error: {e}")

def fetch_jobicy():
    """Fetch jobs from Jobicy API"""
    url = "https://jobicy.com/api/v2/remote-jobs?count=50&industry=engineering"
    print(f"[API: Jobicy] Fetching from {url}...")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        jobs = data.get('jobs', [])
        added = 0
        for j in jobs:
            # Jobicy tends to have annualSalaryMin/annualSalaryMax
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
        print(f"[API: Jobicy] Added {added} new unique jobs out of {len(jobs)} retrieved")
    except Exception as e:
         print(f"[API: Jobicy] Error: {e}")

def fetch_arbeitnow():
    """Fetch jobs from Arbeitnow"""
    url = "https://www.arbeitnow.com/api/job-board-api"
    print(f"[API: Arbeitnow] Fetching from {url}...")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        jobs = data.get('data', [])
        added = 0
        for j in jobs:
            # Only keeping remote ones
            if not j.get('remote', False):
                continue
                
            job_dict = {
                "title": j.get('title', 'Unknown Title'),
                "company": j.get('company_name', 'Unknown Company'),
                "url": j.get('url', ''),
                "board": "arbeitnow",
                "description": j.get('description', ''),
                "salary_raw": None, # Usually not provided natively via the free endpoint
                "salary_monthly": None,
                "salary_listed": 0,
                "remote": 1
            }
            if job_dict["url"]:
                if database.upsert_job(job_dict):
                    added += 1
        print(f"[API: Arbeitnow] Added {added} new unique remote jobs out of {len(jobs)} retrieved")
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
