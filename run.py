"""
Job Hunt Automation System CLI
Usage:
  python run.py discover
  python run.py score
  python run.py tailor --job <job_id>
  python run.py report
  python run.py linkedin
  python run.py dashboard
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Job Hunt Automation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # discover
    parser_discover = subparsers.add_parser("discover", help="Scrape job boards and auto-score new jobs")
    parser_discover.add_argument("--deep", action="store_true", help="Run the deep search using JobSpy and native APIs")
    
    # score
    subparsers.add_parser("score", help="Score any unscored jobs in the database")

    # tailor
    parser_tailor = subparsers.add_parser("tailor", help="Generate a tailored resume and cover letter seed")
    parser_tailor.add_argument("--job", type=int, required=True, help="Job ID from the database")

    # report
    subparsers.add_parser("report", help="Print the skills intelligence gap analysis")

    # linkedin
    subparsers.add_parser("linkedin", help="Generate a customized LinkedIn profile rewrite guide")

    # dashboard
    parser_dashboard = subparsers.add_parser("dashboard", help="Start the local job tracking dashboard")
    parser_dashboard.add_argument("--port", type=int, default=8080, help="Port to run the dashboard on (default: 8080)")

    args = parser.parse_args()

    if args.command == "discover":
        if args.deep:
            from scripts.job_scraper_apis import run_all_apis
            from scripts.job_scraper_jobspy import run_jobspy_scraper
            from config import SEARCH_QUERIES
            
            run_all_apis()
            run_jobspy_scraper(SEARCH_QUERIES, results_wanted=15)
        
        from scripts.discover import run_discovery
        from scripts.score import run_scoring
        run_discovery()
        run_scoring()

    elif args.command == "score":
        from scripts.score import run_scoring
        run_scoring()

    elif args.command == "tailor":
        from scripts.tailor import tailor_resume
        tailor_resume(args.job)

    elif args.command == "report":
        from scripts.keywords import build_skills_log, run_report
        build_skills_log()
        run_report()

    elif args.command == "linkedin":
        from scripts.linkedin import generate_linkedin_rewrite
        generate_linkedin_rewrite()

    elif args.command == "dashboard":
        from dashboard.server import run_server
        run_server(port=args.port)

if __name__ == "__main__":
    main()
