---
name: Job Discovery
description: Instructions and guidelines for discovering AI+Healthcare remote jobs
---

# Job Discovery Skill

This skill defines the strategy for finding highly relevant job postings for a Medical Doctor transitioning into remote AI/Tech leadership roles.

## User Profile

**Always read `data/user_profile.md` before modifying or interpreting search queries.** It contains the user's actual target roles, skills, salary floor, and what to avoid. The defaults in `config.py` are populated for the original author — once a user runs the Setup Wizard, their personalized queries live in `config_user.py` and override those defaults.

## Search Strategy

### Active Search Queries (defaults in `config.py` — overridden by `config_user.py` if present)

**Leadership / Director roles:**
- `"clinical AI lead" remote`
- `"medical director" AI remote -"patient care"`
- `"head of clinical" AI remote`
- `"director of clinical" AI remote`
- `"VP clinical" AI remote`
- `"clinical transformation" AI remote`
- `"director" "healthcare AI" remote`
- `"head of medical affairs" AI remote`
- `"director of medical AI" remote`

**Program / Product management:**
- `"clinical product manager" AI remote`
- `"AI program manager" healthcare remote`
- `"healthcare AI" "product manager" remote`
- `"AI" "clinical operations" manager remote`

**Senior IC roles:**
- `"senior clinical AI" remote`
- `"principal clinical" AI remote`
- `"clinical AI architect" remote`
- `"senior healthcare AI" remote`
- `"senior medical affairs" AI remote`

**Physician-specific crossover:**
- `"physician" AI remote "non-clinical" -sales`
- `"MD" "healthcare AI" remote -sales`
- `"medical doctor" AI remote -"patient care"`

**General clinical AI:**
- `"clinical informatics" AI remote`
- `"health informatics" AI remote`
- `"AI" "clinical documentation" remote`

### Ineligible Roles (Auto-filtered / Auto-archived)
- Requires active US medical license or US citizenship/visa
- Pure software engineering (heavy coding, no healthcare component)
- Sales, business development, account executive, AE, SDR, BDR
- Patient-facing clinical roles (seeing patients, clinical shifts, prescribing)
- On-site or hybrid with heavy travel

## Job Boards Used

| Board | Type | Notes |
|---|---|---|
| Remotive | API | Health + Product categories |
| Himalayas | API | Filtered to health/AI keywords |
| Jobicy | API | Healthcare + IT industries |
| Arbeitnow | API | Remote-only filter + health/AI keyword filter |
| LinkedIn | Scrape | Remote + full-time filters |
| Wellfound | Scrape | Product Manager + remote |
| HealthcareITJobs | Scrape | Direct healthcare IT board |

## Running Discovery

If the user asks you to "find new jobs" or "run discovery", execute:

```bash
python run.py discover
```

For a deeper scrape (slower, more thorough):
```bash
python run.py discover --deep
```

This handles scraping, deduplication, and database insertion automatically.
