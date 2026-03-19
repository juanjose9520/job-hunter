"""
Wrapper for python-jobspy to scrape job boards and integrate with our local database.
"""

from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import sys
import pathlib

# Ensure we can import config & database from the root dir
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from config import SEARCH_QUERIES, JOB_BOARDS
import scripts.database as database

def map_jobspy_to_db(job: pd.Series) -> dict:
    """Map a pandas Series row from JobSpy into our database dict format."""
    
    # Safe extraction for salary
    salary_raw = None
    if pd.notna(job.get('min_amount')) and pd.notna(job.get('max_amount')):
        salary_raw = f"${job['min_amount']} - ${job['max_amount']}"
    
    # Extract monthly salary if yearly is provided
    salary_monthly = None
    if pd.notna(job.get('min_amount')) and pd.notna(job.get('max_amount')):
        try:
            # Assuming the amount is yearly if it's > 10000, rough check
            avg_yearly = (float(job['min_amount']) + float(job['max_amount'])) / 2
            if job.get('interval') == 'yearly' or avg_yearly > 15000:
                salary_monthly = avg_yearly / 12
            elif job.get('interval') == 'monthly':
                salary_monthly = avg_yearly
            elif job.get('interval') == 'hourly': # Assume 160 hrs/month
                salary_monthly = avg_yearly * 160
        except:
            pass
            
    # Location logic - prioritize remote
    is_remote = 1 if (pd.notna(job.get('is_remote')) and job['is_remote']) else 0

    return {
        "title": str(job.get("title", "Unknown Title")),
        "company": str(job.get("company", "Unknown Company")),
        "url": str(job.get("job_url", "")),
        "board": str(job.get("site", "jobspy")),
        "description": str(job.get("description", "")),
        "salary_raw": salary_raw,
        "salary_monthly": salary_monthly,
        "salary_listed": 1 if salary_raw else 0,
        "remote": is_remote
    }

def run_jobspy_scraper(queries: list[str], results_wanted: int = 20):
    """
    Run JobSpy for the given queries and save to the database.
    """
    total_added = 0
    print(f"[JobSpy] Starting search across LinkedIn, Indeed, Glassdoor, ZipRecruiter...")
    
    for query in queries:
        print(f"[JobSpy] Searching for: '{query}'")
        try:
            jobs_df = scrape_jobs(
                site_name=["indeed", "linkedin", "zip_recruiter"],
                search_term=query,
                results_wanted=results_wanted,
                is_remote=True,
                location="United States"
            )
            
            if jobs_df.empty:
                print(f"[JobSpy] No results found for '{query}'")
                continue
                
            print(f"[JobSpy] Found {len(jobs_df)} jobs for '{query}'")
            
            # Process and insert into DB
            added_for_query = 0
            for _, row in jobs_df.iterrows():
                job_dict = map_jobspy_to_db(row)
                if job_dict["url"]: # URL is required and UNIQUE
                    new_id = database.upsert_job(job_dict)
                    if new_id:
                        added_for_query += 1
            
            print(f"[JobSpy] Added {added_for_query} new unique jobs to database.")
            total_added += added_for_query
            
        except Exception as e:
            print(f"[JobSpy] Error scraping query '{query}': {e}")
            
    print(f"\n[JobSpy] Completed. Total new unique jobs added: {total_added}")

if __name__ == "__main__":
    import sys
    # Allow testing with a simple query
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running JobSpy test block...")
        test_queries = ['"AI" "clinical documentation" remote']
        run_jobspy_scraper(test_queries, results_wanted=5)
    else:
        # Use config queries if no arguments are passed
        run_jobspy_scraper(SEARCH_QUERIES, results_wanted=15)
