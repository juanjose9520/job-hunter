---
name: Resume Tailor
description: Guidelines for tailoring the baseline MD+AI resume for specific roles
---

# Resume Tailor Skill

This skill outlines the philosophy and mechanics of adjusting the user's resume for a specific job posting.

## Tailoring Strategy (The "MD+AI Bridge")

The user is a Medical Doctor pivoting into tech. The #1 goal of tailoring is to **translate clinical/medical experience into tech/business value**.

1. **The Professional Summary**:
   - Must be completely rewritten for every job.
   - Must mirror the exact title of the job opening.
   - Example bridge: "Leveraging clinical expertise and prompt engineering to solve [Problem mentioned in job description]."

2. **Experience Bullets**:
   - **Do not invent facts.**
   - Do organically reorder bullets to put the most relevant achievement first.
   - For AI roles: Highlight the 5% denial rate achievement and the WhatsApp n8n chatbot.
   - For Ops roles: Highlight the Intake Operations Manager experience and remote team management.

3. **Core Competencies**:
   - Reorder the grid so the top-left skill matches the primary requirement of the JD.

## Execution
To generate a tailored resume (Markdown + PDF) + Cover Letter seed:
```bash
# Requires the DB ID of the job
python run.py tailor --job <ID>
```
The output will be saved in `output/resumes/<company_date>/`.
