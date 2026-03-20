"""
Relevance Scorer — uses Gemini to score each unscored job against the user profile.
Run: python run.py discover  (scoring is called automatically after discovery)
     python run.py score     (re-score all unscored jobs)
"""

import json
import time
import warnings
warnings.filterwarnings("ignore")
from google import genai

from scripts.database import get_connection, update_job_status
from config import (
    GEMINI_API_KEY, GEMINI_MODEL, USER_PROFILE,
    SCORE_SHOW_THRESHOLD
)

try:
    from config import GEMINI_FALLBACK_MODEL
except ImportError:
    GEMINI_FALLBACK_MODEL = "gemini-1.5-flash-latest"

_client = genai.Client(api_key=GEMINI_API_KEY)

SCORING_PROMPT = """
You are a job fit analyst. Score this job posting for the candidate below based on a holistic 0-100 scale.

## Candidate Profile
{profile}

## Job Posting
Title: {title}
Company: {company}
Board: {board}
Salary info: {salary_info}

Description:
{description}

## Scoring Rubric (Holistic Score 0-100)
Evaluate the job against the candidate's dealbreakers and strongest suits.

**Dealbreakers (Score 0-20 if any apply):**
- Not 100% remote (hybrid or on-site).
- Stated salary is clearly under $2,500 USD/month or under $30 USD/hour.
- Requires a specific US medical license, US citizenship, or US work permit/visa.
- Deep software engineering role (heavy coding/programming) with NO healthcare or clinical AI aspect.
- Sales, business development, or account management role (AE, SDR, BDR, Account Manager) with no clinical or AI leadership component.
- Patient-facing clinical role requiring active medical practice (seeing patients, clinical shifts, prescribing).

**High Match (Score 80-100):**
- Leadership, management, or senior IC role at the intersection of healthcare and AI.
- Titles like: Clinical AI Lead, Medical Director of AI, Head of Clinical AI, Director of Clinical Informatics, VP of Clinical Strategy, Clinical Product Manager, AI Program Manager (Healthcare), Clinical Transformation Lead, Senior Clinical AI Specialist, Principal Clinical Advisor, Clinical AI Architect.
- Leverages the candidate's physician background as a domain expert — NOT as a practicing clinician.
- Involves leading/managing teams or clinical AI workflows, prompt engineering, or AI product strategy.
- Fully remote with no location restriction. Salary >= $2,500/mo or >= $30/hr.

**Moderate Match (Score 50-79):**
- No dealbreakers, but not a perfect leadership/AI fit.
- Could be a general health tech, AI operations, or product role that is viable but lacks clear clinical AI leadership signals.
- Still 100% remote with no hard location restriction.

Return ONLY a JSON object like this (no markdown, no extra text):
{{
  "score": <number 0-100>,
  "reasoning": "<2-3 sentences explaining the score and any dealbreakers or strong matches>",
  "breakdown": {{
    "dealbreakers_hit": true/false,
    "remote_confirmed": true/false,
    "salary_adequate": true/false/null,
    "healthcare_ai_focus": true/false,
    "heavy_coding_penalty": true/false,
    "sales_role_penalty": true/false,
    "patient_facing_penalty": true/false
  }},
  "top_keywords": ["<keyword1>", "<keyword2>", "<keyword3>"]
}}
"""


def score_job(job: dict) -> dict:
    """Score a single job dict using Gemini. Returns updated job dict with score fields."""
    salary_info = (
        job.get("salary_raw") or
        ("Salary listed but unstructured" if job.get("salary_listed") else "No salary information provided")
    )

    prompt = SCORING_PROMPT.format(
        profile=USER_PROFILE,
        title=job.get("title", ""),
        company=job.get("company", ""),
        board=job.get("board", ""),
        salary_info=salary_info,
        description=(job.get("description") or "No description available")[:6000],
    )

    models_to_try = [GEMINI_MODEL, GEMINI_FALLBACK_MODEL]
    for attempt, model_name in enumerate(models_to_try):
        try:
            response = _client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw)
            return {
                "score": float(result.get("score", 0)),
                "score_breakdown": json.dumps(result.get("breakdown", {})),
                "reasoning": result.get("reasoning", ""),
                "top_keywords": result.get("top_keywords", []),
            }
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "503" in err_str) and attempt == 0:
                print(f"  [Scorer] 429/503 Error hit. Retrying with fallback model in 5s...")
                time.sleep(5)
                continue
            print(f"  [Scorer] Error scoring job '{job.get('title')}': {e}")
            return {"score": 0, "score_breakdown": "{}", "reasoning": f"Scoring failed: {err_str[:50]}", "top_keywords": []}


def run_scoring(limit: int = 50) -> dict:
    """Score all unscored jobs in the database."""
    from scripts.database import save_keywords

    conn = get_connection()
    jobs = conn.execute(
        "SELECT * FROM jobs WHERE score IS NULL LIMIT ?", (limit,)
    ).fetchall()
    conn.close()

    if not jobs:
        print("[Scorer] No unscored jobs found.")
        return {"scored": 0, "archived": 0}

    scored, archived = 0, 0
    for job in jobs:
        job_dict = dict(job)
        print(f"  Scoring: {job_dict['title']} @ {job_dict['company']} ...")
        result = score_job(job_dict)

        conn = get_connection()
        conn.execute(
            "UPDATE jobs SET score = ?, score_breakdown = ? WHERE id = ?",
            (result["score"], result["score_breakdown"], job_dict["id"])
        )
        conn.commit()
        conn.close()

        # Set status based on score
        if result["score"] < SCORE_SHOW_THRESHOLD:
            update_job_status(job_dict["id"], "archived")
            archived += 1
        else:
            update_job_status(job_dict["id"], "new")
            scored += 1

        # Save extracted keywords
        if result.get("top_keywords"):
            kws = [{"keyword": k, "category": "signal"} for k in result["top_keywords"]]
            save_keywords(job_dict["id"], kws)

    print(f"\n[Scorer] Done — {scored} jobs shortlisted, {archived} auto-archived.")
    return {"scored": scored, "archived": archived}


if __name__ == "__main__":
    run_scoring()
