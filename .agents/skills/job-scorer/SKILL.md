---
name: Job Scorer
description: Rubric and instructions for scoring job relevance using Gemini
---

# Job Scorer Skill

This skill defines how job postings are evaluated against the user's specific profile (MD + AI + Remote Ops).

## The Rubric (Out of 10)

When reviewing a job manually or troubleshooting the Scorer script, apply these exact weights:

- **+3 points**: Remote work confirmed in the posting
- **+2 points**: Clear AI/ML/LLM component in the role responsibilities
- **+2 points**: Healthcare, medical, or clinical domain relevance
- **+1 point**: No deep coding or software engineering required (no LeetCode, no "must have 5 yrs C++")
- **+1 point**: Salary is listed AND is ≥ $5,000/month (or equivalent hourly/annual)
- **-1 point**: Salary information is completely absent
- **-1 point**: Role requires an active medical license in a specific country (e.g., US Board Certified required)
- **-2 points**: On-site, hybrid, or heavy travel required

## Thresholds
- **Score ≥ 6**: Highly relevant. Belongs in the dashboard pipeline.
- **Score < 6**: Not a fit. Auto-archive.

## Running the Scorer
The scorer runs automatically during discovery. To force a re-score of all unscored jobs in the database:
```bash
python run.py score
```
