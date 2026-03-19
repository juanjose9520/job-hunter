"""
Resume Tailoring Engine — generates a customized resume + cover letter seed for a job.
Run: python run.py tailor --job <job_id>
"""

import subprocess
import pathlib
import datetime
import re
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import warnings
warnings.filterwarnings("ignore")
from google import genai as genai_sdk
from scripts.database import get_connection, save_application  # type: ignore
from config import GEMINI_API_KEY, GEMINI_MODEL, USER_PROFILE, BASE_RESUME, OUTPUT_DIR, PERSONAL_INFO  # type: ignore

_client = genai_sdk.Client(api_key=GEMINI_API_KEY)

TAILOR_PROMPT = """
You are an elite executive resume writer specializing in AI, Healthcare, and Operations roles.
Your task is to comprehensively tailor the provided base resume to perfectly align with the target job description.

## Candidate Profile Context
{profile}

## Base Resume (Markdown)
{base_resume}

## Target Job
Title: {title}
Company: {company}
Job Description:
{description}

## Resume Writing Protocol & Strict Instructions:
1. **Professional Summary (3-4 sentences):** Rewrite completely to serve as a high-impact hook. It must directly mirror the job's core language, top priorities, and critical keywords. Make it unmistakably tailored for this specific role and company.
2. **Experience Bullet Points:** Rewrite and re-order bullets to front-load the most relevant achievements that directly address the job requirements. Emphasize quantifiable results and action verbs. **CRITICAL:** Do NOT invent, hallucinate, or exaggerate facts. Maintain absolute truthfulness while optimizing the framing.
3. **Core Competencies:** Strategically reorder the skills list to place the most relevant competencies for the target job at the very top.
4. **Relevance Notes (Experience & Projects):** For sections containing `[LLM: Insert 1-sentence relevance note here]`, replace that placeholder with a sharp, insightful 1-sentence explanation of why that specific experience or project makes the candidate a perfect fit for THIS exact employer and role.
5. **Section Integrity:** Keep all existing sections. Do not delete any section or remove unrelated but important context.
6. **Formatting:** Preserve the exact Markdown structure, headings, spacing, and formatting of the base resume.
7. **Tone:** Confident, highly professional, evidence-based, specific, and fully ATS-optimized without keyword stuffing.

Return ONLY the complete tailored resume in standard Markdown format. Do not include any conversational preamble, commentary, or markdown code block backticks surrounding the output.
"""

COVER_PROMPT = """
You are an expert career strategist and executive coach writing a highly compelling, custom "Why This Role" cover letter opening paragraph for a top-tier candidate.
This will serve as a seed for the candidate's final cover letter.

## Candidate Profile Context
{profile}

## Target Job
Title: {title}
Company: {company}
Job Description (Summary):
{description}

## Cover Letter Protocol & Instructions:
Write an exceptionally authentic, compelling, and punchy 3-sentence opening paragraph that accomplishes the following:
1. **The Hook:** Opens with a highly specific, well-researched hook about the company's mission, recent challenges, or the specific role (avoiding any generic platitudes like "I was excited to see...").
2. **The Bridge:** Seamlessly connects the candidate's unique intersection of skills (Medical Doctor + AI Systems Design + Remote Clinical Operations) directly to the core needs of the role.
3. **The Value Proposition:** Confidently expresses genuine interest while clearly stating the immediate value the candidate will bring, without being overly formal or sycophantic.

Return ONLY the 3-sentence paragraph text. Do NOT include a subject line, greeting (e.g., "Dear Hiring Manager"), sign-off, or any commentary.
"""


def get_job(job_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def tailor_resume(job_id: int) -> pathlib.Path | None:
    job = get_job(job_id)
    if not job:
        print(f"[Tailor] Job ID {job_id} not found.")
        return None

    base_resume = BASE_RESUME.read_text(encoding="utf-8")
    raw_desc = job.get("description") or ""
    desc_str = str(raw_desc)
    desc = desc_str[:6000] # type: ignore
    company_name = str(job.get("company") or "unknown")
    company_slug_full = str(re.sub(r"[^a-zA-Z0-9]", "_", company_name))
    company_slug = company_slug_full[:30] # type: ignore
    date_slug = datetime.date.today().strftime("%Y%m%d")
    out_dir = OUTPUT_DIR / f"{company_slug}_{date_slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Tailor] Generating resume for: {job['title']} @ {job.get('company', '?')}")

    # ── Generate tailored resume ──────────────────────────────────────────────
    resume_prompt = TAILOR_PROMPT.format(
        profile=USER_PROFILE,
        base_resume=base_resume,
        title=job.get("title", ""),
        company=job.get("company", ""),
        description=desc,
    )
    try:
        response = _client.models.generate_content(model=GEMINI_MODEL, contents=resume_prompt)
        resume_md = response.text.strip()
        if PERSONAL_INFO.exists():
            personal_info_text = PERSONAL_INFO.read_text(encoding="utf-8").strip()
            resume_md = f"{personal_info_text}\n\n---\n\n{resume_md}"
    except Exception as e:
        print(f"[Tailor] Resume generation failed: {e}")
        return None

    resume_md_path = out_dir / "resume.md"
    resume_md_path.write_text(resume_md, encoding="utf-8")
    print(f"  ✓ Tailored resume (MD) → {resume_md_path}")

    # ── Generate cover letter seed ────────────────────────────────────────────
    cover_prompt = COVER_PROMPT.format(
        profile=USER_PROFILE,
        title=job.get("title", ""),
        company=job.get("company", ""),
        description=desc_str[:2000], # type: ignore
    )
    try:
        cover_seed = _client.models.generate_content(model=GEMINI_MODEL, contents=cover_prompt).text.strip()
    except Exception as e:
        cover_seed = "[Cover letter seed generation failed]"
        print(f"[Tailor] Cover seed generation failed: {e}")

    cover_path = out_dir / "cover_seed.md"
    cover_path.write_text(
        f"# Cover Letter Seed — {job.get('title')} @ {job.get('company')}\n\n{cover_seed}\n",
        encoding="utf-8"
    )
    print(f"  ✓ Cover letter seed → {cover_path}")

    # ── Convert to PDF ────────────────────────────────────────────────────────
    pdf_path = out_dir / "resume.pdf"
    try:
        result = subprocess.run(
            ["npx", "markdown-pdf", str(resume_md_path), "-o", str(pdf_path)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  ✓ PDF → {pdf_path}")
        else:
            err_msg = str(result.stderr) if result.stderr else ""
            print(f"  ✗ PDF conversion failed: {err_msg[:200]}") # type: ignore
    except FileNotFoundError:
        print("  ✗ markdown-pdf not found. Run: npm install -g markdown-pdf")
    except Exception as e:
        print(f"  ✗ PDF error: {e}")

    # ── Save to DB ────────────────────────────────────────────────────────────
    save_application(job_id, str(pdf_path), cover_seed)
    print(f"\n[Tailor] Complete → {out_dir}")
    return out_dir


if __name__ == "__main__":
    import sys
    job_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    tailor_resume(job_id)
