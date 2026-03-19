import sqlite3
import json
from scripts.database import get_connection

def insert_scored_job():
    conn = get_connection()
    job = {
        "title": "AI Product Manager (Clinical)",
        "company": "MedTech Innovators",
        "url": "https://example.com/job/456",
        "board": "test_board",
        "description": "Looking for an AI PM with a medical background to lead our clinical decision support tools.",
        "salary_raw": "$7k-$9k/mo",
        "salary_monthly": 8000.0,
        "salary_listed": 1,
        "remote": 1,
        "score": 9.0,
        "score_breakdown": json.dumps({"remote": 3, "ai_component": 2, "healthcare": 2, "no_coding_required": 1, "salary_ok": 1}),
        "status": "new"
    }
    
    try:
        conn.execute("""
            INSERT INTO jobs (title, company, url, board, description,
                              salary_raw, salary_monthly, salary_listed, remote,
                              score, score_breakdown, status)
            VALUES (:title, :company, :url, :board, :description,
                    :salary_raw, :salary_monthly, :salary_listed, :remote,
                    :score, :score_breakdown, :status)
        """, job)
        conn.commit()
        print("Scored test job inserted.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    insert_scored_job()
