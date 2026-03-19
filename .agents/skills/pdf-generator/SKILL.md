---
name: PDF Generator
description: Rules for formatting Markdown to PDF using markdown-pdf
---

# PDF Generator Skill

This skill defines the generation of a clean, ATS-compliant PDF resume from the generated Markdown file.

## Requirements
The system uses the `markdown-pdf` Node package.
If it is not installed, install it globally:
```bash
npm install -g markdown-pdf
```

## PDF Formatting Rules

1. **No External CSS (Keep it Clean)**:
   - ATS systems prefer simple, single-column text. 
   - Do not inject complex CSS formatting or columns.

2. **Standard Spacing**:
   - Ensure a blank line between all major headings (e.g., `#`, `##`, `###`).
   - Use standard unordered list bullets (`- `).

3. **Links**:
   - Keep URLs brief and clickable.
   - Example: `[linkedin.com/in/username](https://linkedin.com/in/username)`

## Execution
The `tailor.py` script automatically calls this during the resume tailoring process:
```bash
npx markdown-pdf output/resumes/company_date/resume.md -o output/resumes/company_date/resume.pdf
```
