"""
Keywords Intelligence — aggregates skills/keywords from all job descriptions.
Run: python run.py report
"""

import json
import re
from collections import Counter
import google.generativeai as genai
from scripts.database import get_connection
from config import GEMINI_API_KEY, GEMINI_MODEL, SKILLS_LOG, BASE_RESUME

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(GEMINI_MODEL)

EXTRACT_PROMPT = """
Analyze this job description and extract keywords/skills in three categories.

Job Description:
{description}

Return ONLY a JSON object (no markdown, no extra text):
{{
  "tools": ["<software, platform, or technical tool>", ...],
  "skills": ["<professional skill or competency>", ...],
  "signals": ["<role signal phrase or unique qualifier>", ...]
}}

Examples:
- tools: Epic, FHIR, AWS HealthLake, LangChain, Salesforce, n8n
- skills: "clinical documentation", "prompt engineering", "workflow automation", "NLP"
- signals: "physician champion", "clinical AI advocate", "non-technical clinician", "translation layer"

Extract up to 6 items per category. Be specific, not generic.
"""


def extract_keywords_from_description(description: str) -> dict:
    if not description or len(description) < 100:
        return {"tools": [], "skills": [], "signals": []}
    try:
        response = _model.generate_content(
            EXTRACT_PROMPT.format(description=description[:5000])
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        print(f"  [Keywords] Extraction error: {e}")
        return {"tools": [], "skills": [], "signals": []}


def build_skills_log() -> dict:
    """Re-aggregate all keyword data from the keywords table."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT keyword, category, COUNT(*) as freq FROM keywords GROUP BY keyword, category"
    ).fetchall()
    conn.close()

    log = {"tools": Counter(), "skills": Counter(), "signals": Counter()}
    for row in rows:
        cat = row["category"] if row["category"] in log else "skills"
        log[cat][row["keyword"]] += row["freq"]

    # Convert to sorted lists
    result = {
        cat: [{"keyword": k, "frequency": v}
              for k, v in sorted(counter.items(), key=lambda x: -x[1])]
        for cat, counter in log.items()
    }
    SKILLS_LOG.parent.mkdir(parents=True, exist_ok=True)
    SKILLS_LOG.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def get_resume_keywords() -> set[str]:
    """Extract simple keywords already present in the base resume."""
    if not BASE_RESUME.exists():
        return set()
    text = BASE_RESUME.read_text(encoding="utf-8").lower()
    # Extract words/phrases 2+ chars
    words = re.findall(r"\b[a-z][a-z\s\-]{1,30}\b", text)
    return {w.strip() for w in words if len(w.strip()) > 3}


def run_report() -> None:
    """Print a skills intelligence report to the terminal."""
    if not SKILLS_LOG.exists():
        print("[Report] No skills_log.json found. Run discover + score first.")
        return

    log = json.loads(SKILLS_LOG.read_text(encoding="utf-8"))
    resume_kws = get_resume_keywords()

    print("\n" + "=" * 60)
    print("  SKILLS INTELLIGENCE REPORT")
    print("=" * 60)

    for category, items in log.items():
        if not items:
            continue
        print(f"\n▸ {category.upper()} (top 15)")
        print(f"  {'Keyword':<35} {'Freq':>5}  {'In Resume?':>10}")
        print("  " + "-" * 55)
        for item in items[:15]:
            kw = item["keyword"]
            freq = item["frequency"]
            in_resume = "✓" if any(kw.lower() in rk for rk in resume_kws) else "✗ GAP"
            print(f"  {kw:<35} {freq:>5}  {in_resume:>10}")

    print("\n" + "=" * 60)
    print("  ✗ GAP = keyword appears in job postings but not in your base resume")
    print("  Update base_resume.md to include frequently requested skills.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    build_skills_log()
    run_report()
