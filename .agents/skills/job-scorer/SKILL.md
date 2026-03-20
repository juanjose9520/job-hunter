---
name: Job Scorer
description: Rubric and instructions for scoring job relevance using Gemini AI (0-100 scale)
---

# Job Scorer Skill

This skill defines how job postings are evaluated against the user's profile (MD + AI + Remote). Scoring is done automatically by Gemini AI during discovery using the rubric defined in `scripts/score.py`.

## Scale

All jobs are scored **0 to 100**. Scores map to these dashboard thresholds (configurable in `config_user.py`):

| Score | Outcome |
|---|---|
| ≥ 50 | Visible in dashboard |
| ≤ 49 | Auto-archived |

## Dealbreakers (Score → 0 regardless of other signals)

A job is immediately archived if **any** of the following are true:

1. **Not 100% remote** — hybrid or on-site roles are rejected.
2. **Salary clearly below floor** — stated salary under $2,500 USD/month or under $30 USD/hour.
3. **Hard location requirement** — requires a specific US medical license, US citizenship, or US work permit/visa.
4. **Deep software engineering** — heavy coding/programming role with NO healthcare or clinical AI component.
5. **Sales / BD role** — Account Executive, SDR, BDR, Account Manager with no clinical or AI leadership component.
6. **Patient-facing clinical** — role requires active medical practice (seeing patients, clinical shifts, prescribing).

## Scoring Rubric

**High Match (80–100):**
- Leadership, management, or senior IC role at the intersection of healthcare and AI.
- Titles in the sweet spot: Clinical AI Lead, Medical Director of AI, Head of Clinical AI, Director of Clinical Informatics, VP of Clinical Strategy, Clinical Product Manager, AI Program Manager (Healthcare), Clinical Transformation Lead, Senior Clinical AI Specialist, Principal Clinical Advisor, Clinical AI Architect.
- Leverages the user's physician background as a domain expert — NOT as a practicing clinician.
- Involves leading/managing teams, clinical AI workflows, prompt engineering, or AI product strategy.
- Fully remote, no location restriction. Salary ≥ $2,500/mo or ≥ $30/hr.

**Moderate Match (50–79):**
- No dealbreakers, but not a perfect leadership/AI fit.
- Could be a general health tech, AI operations, or product role — viable but lacks clear clinical AI leadership signals.
- Still 100% remote with no hard location restriction.

**Poor Match (0–49):**
- Contains a dealbreaker, OR
- Clearly misaligned with the target profile (wrong industry, wrong seniority, wrong role type).

## Score JSON Output (from Gemini)

The scorer returns a structured JSON per job:

```json
{
  "score": 85,
  "reason": "...",
  "dealbreakers": {
    "not_remote": false,
    "salary_too_low": false,
    "visa_required": false,
    "remote_confirmed": true,
    "salary_adequate": true,
    "healthcare_ai_focus": true,
    "heavy_coding_penalty": false,
    "sales_role_penalty": false,
    "patient_facing_penalty": false
  },
  "top_keywords": ["clinical AI", "remote", "healthcare"]
}
```

## Salary Settings

| Setting | Default | Override via |
|---|---|---|
| `MIN_SALARY_USD_MONTHLY` | `2500` | `config_user.py` |
| `PENALIZE_MISSING_SALARY` | `False` | `config_user.py` |

Setting `PENALIZE_MISSING_SALARY = False` means jobs with no salary listed are NOT penalized — they are scored purely on role fit.

## Running the Scorer

The scorer runs automatically during discovery. To force a re-score of all pending jobs:

```bash
python run.py score
```
