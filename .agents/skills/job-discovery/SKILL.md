---
name: Job Discovery
description: Instructions and guidelines for discovering AI+Healthcare remote jobs
---

# Job Discovery Skill

This skill defines the strategy for finding highly relevant job postings for a Medical Doctor transitioning into remote AI/Tech roles.

## Search Strategy

1. **Target Titles/Roles**: 
   - Clinical Informatics Specialist
   - AI Product Manager (Healthcare)
   - Clinical AI Operations Manager
   - Prompt Engineer (Medical/Healthcare)
   - AI Clinical Analyst

2. **Core Search Queries**:
   When using job board APIs or scraping, use these exact queries:
   - `"clinical AI" remote`
   - `"health AI" remote`
   - `"medical AI" remote -engineer -developer -software`
   - `"AI healthcare" "prompt engineering" remote`
   - `"clinical informatics" AI remote`

3. **Ineligible Roles (Filter Out)**:
   - Requires active medical license in the US/EU (user is MD in Colombia)
   - Pure Software Engineering (requires advanced Python/C++/React)
   - On-site only
   - Pay explicitly under $5,000 USD/month

## Running Discovery
If the user asks you to "find new jobs" or "run discovery", simply execute:
```bash
python run.py discover
```
This script handles the scraping, deduplication, and database insertion automatically.
