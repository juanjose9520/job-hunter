import sqlite3
from scripts.database import get_connection

def insert_test_job():
    conn = get_connection()
    # A perfect fit job
    job = {
        "title": "Clinical AI Operations Manager",
        "company": "HealthTech AI Solutions",
        "url": "https://example.com/job/123",
        "board": "test",
        "salary_raw": "$6,000 - $8,000 / month",
        "salary_monthly": 7000.0,
        "salary_listed": 1,
        "remote": 1,
        "description": """
        About Us:
        We are building the next generation of clinical decision support tools using LLMs.
        
        The Role:
        We need a remote Clinical AI Operations Manager to bridge the gap between our engineering team and clinical reality.
        You do NOT need to write production code, but you must understand how to interact with LLMs and design workflows.
        
        Responsibilities:
        - Design and test system prompts for medical documentation automation.
        - Analyze clinical workflows and identify automation opportunities.
        - Work with engineering to define product requirements based on clinical necessity.
        
        Requirements:
        - Medical background (MD/DO or equivalent clinical experience).
        - Experience with prompt engineering or AI workflow tools (e.g., n8n, LangChain).
        - Deep understanding of healthcare operations and clinical documentation.
        - Fully remote.
        - Compensation: $6,000 - $8,000 / month based on experience.
        """
    }
    
    try:
        conn.execute("""
            INSERT INTO jobs (title, company, url, board, description,
                              salary_raw, salary_monthly, salary_listed, remote)
            VALUES (:title, :company, :url, :board, :description,
                    :salary_raw, :salary_monthly, :salary_listed, :remote)
        """, job)
        conn.commit()
        print("Test job inserted successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    insert_test_job()
