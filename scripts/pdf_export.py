"""
PDF Export Module
Converts markdown documents into beautifully formatted PDFs using xhtml2pdf.
Two templates: one for resumes, one for cover letters.
"""

import re
import io
import markdown as md_lib
from xhtml2pdf import pisa
from config import PERSONAL_INFO


# ─────────────────────────────────────────────
#  Document-type detection
# ─────────────────────────────────────────────

def detect_doc_type(content: str) -> str:
    """Returns 'cover' or 'resume' based on content heuristics."""
    lower = content.lower()
    cover_signals = ["cover letter", "dear hiring", "dear ", "i am writing", "cover_seed", "sincerely", "regards,"]
    for sig in cover_signals:
        if sig in lower:
            return "cover"
    return "resume"


def get_personal_info() -> tuple[str, str]:
    """Reads name and contact info from PERSONAL_INFO file."""
    if not PERSONAL_INFO.exists():
        return "[Candidate Name]", "[Contact Information]"
    
    lines = PERSONAL_INFO.read_text(encoding="utf-8").strip().splitlines()
    name = lines[0].replace("#", "").strip() if len(lines) > 0 else "[Candidate Name]"
    # Looking for the contact info line (usually the 3rd line or the one with @)
    contact = ""
    for line in lines[1:]:
        if "@" in line or "·" in line:
            contact = line.replace("#", "").strip()
            break
    if not contact and len(lines) >= 3:
        contact = lines[2].replace("#", "").strip()
    
    return name, contact or "[Contact Information]"


# ─────────────────────────────────────────────
#  Shared CSS base
# ─────────────────────────────────────────────

SHARED_CSS = """
@page {
    size: letter;
    margin: 2.2cm 2.4cm 2.2cm 2.4cm;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 13pt;
    line-height: 1.55;
    color: #1a1a2e;
}

p {
    margin-bottom: 6pt;
}

a {
    color: #2563eb;
    text-decoration: none;
}

strong {
    font-weight: bold;
}

em {
    font-style: italic;
}

ul {
    margin: 4pt 0 6pt 14pt;
    padding: 0;
}

ul li {
    margin-bottom: 3pt;
    list-style-type: disc;
}

hr {
    border: none;
    border-top: 1pt solid #d1d5db;
    margin: 10pt 0;
}
"""


# ─────────────────────────────────────────────
#  RESUME template
# ─────────────────────────────────────────────

RESUME_CSS = SHARED_CSS + """
.doc-header {
    border-bottom: 2pt solid #1d4ed8;
    padding-bottom: 10pt;
    margin-bottom: 14pt;
}

.candidate-name {
    font-size: 26pt;
    font-weight: bold;
    color: #1e3a8a;
    letter-spacing: 0.5pt;
    margin-bottom: 2pt;
}

.candidate-title {
    font-size: 14pt;
    color: #374151;
    font-weight: normal;
    margin-bottom: 4pt;
}

.candidate-contact {
    font-size: 11pt;
    color: #6b7280;
}

.candidate-contact a {
    color: #2563eb;
}

h2 {
    font-size: 14pt;
    font-weight: bold;
    color: #1d4ed8;
    text-transform: uppercase;
    letter-spacing: 1.2pt;
    margin-top: 14pt;
    margin-bottom: 5pt;
    padding-bottom: 2pt;
    border-bottom: 1pt solid #bfdbfe;
}

h3 {
    font-size: 13pt;
    font-weight: bold;
    color: #111827;
    margin-top: 8pt;
    margin-bottom: 1pt;
}

h4, h5 {
    font-size: 12pt;
    font-weight: bold;
    color: #374151;
    margin-top: 4pt;
    margin-bottom: 2pt;
}

.role-meta {
    font-size: 11.5pt;
    color: #6b7280;
    margin-bottom: 4pt;
    font-style: italic;
}

.relevance-tag {
    font-style: italic;
    color: #9ca3af;
    font-size: 11pt;
    margin-bottom: 3pt;
}
"""

RESUME_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ─────────────────────────────────────────────
#  COVER LETTER template
# ─────────────────────────────────────────────

COVER_CSS = SHARED_CSS + """
.cover-header {
    margin-bottom: 28pt;
}

.cover-name {
    font-size: 22pt;
    font-weight: bold;
    color: #1e3a8a;
    letter-spacing: 0.3pt;
}

.cover-meta {
    font-size: 11pt;
    color: #6b7280;
    margin-top: 2pt;
}

.cover-date {
    font-size: 12pt;
    color: #374151;
    margin-top: 20pt;
    margin-bottom: 16pt;
}

h1 {
    font-size: 17pt;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 18pt;
    line-height: 1.4;
}

.cover-body p {
    font-size: 13.5pt;
    line-height: 1.7;
    color: #1f2937;
    text-align: justify;
    margin-bottom: 12pt;
}

.cover-accent-bar {
    width: 36pt;
    height: 3pt;
    background-color: #1d4ed8;
    margin-bottom: 18pt;
}

.cover-closing {
    margin-top: 28pt;
    font-size: 13.5pt;
    color: #1f2937;
}

.cover-sig {
    margin-top: 16pt;
    font-weight: bold;
    font-size: 13.5pt;
    color: #1e3a8a;
}
"""

COVER_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ─────────────────────────────────────────────
#  Markdown → structured HTML processors
# ─────────────────────────────────────────────

def _parse_resume_header(lines):
    """
    Extracts the top h1 block from the resume markdown.
    Expects lines like:
      # [Full Name]
      # Health AI Product Manager | ...
      # Colombia (Remote) · email · linkedin
    Returns (header_html, remaining_lines_start_index).
    """
    name = ""
    title = ""
    contact = ""

    idx = 0
    header_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            header_lines.append(stripped[2:])
            idx = i + 1
        elif stripped == "---" and header_lines:
            idx = i + 1
            break
        elif header_lines:
            break

    if len(header_lines) >= 1:
        name = header_lines[0]
    if len(header_lines) >= 2:
        title = header_lines[1]
    if len(header_lines) >= 3:
        contact_raw = header_lines[2]
        # linkify LinkedIn & email
        contact_raw = re.sub(
            r'(https?://[^\s·]+)',
            r'<a href="\1">\1</a>',
            contact_raw
        )
        contact_raw = re.sub(
            r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
            r'<a href="mailto:\1">\1</a>',
            contact_raw
        )
        contact = contact_raw

    header_html = f"""
<div class="doc-header">
  <div class="candidate-name">{name}</div>
  {'<div class="candidate-title">' + title + '</div>' if title else ''}
  {'<div class="candidate-contact">' + contact + '</div>' if contact else ''}
</div>
"""
    return header_html, idx


def _style_resume_body(raw_html: str) -> str:
    """Post-process xhtml2pdf-safe HTML for resume body."""
    # Style the _relevance_ italic blocks
    raw_html = re.sub(
        r'<p><em>(\*\*Relevance[^<]*)\*\*([^<]*)</em></p>',
        r'<p class="relevance-tag"><em>\1\2</em></p>',
        raw_html
    )
    raw_html = re.sub(
        r'<p><em>(Relevance[^<]*)</em></p>',
        r'<p class="relevance-tag"><em>\1</em></p>',
        raw_html
    )
    return raw_html


def build_resume_html(content: str) -> str:
    lines = content.splitlines()
    header_html, body_start = _parse_resume_header(lines)
    body_md = "\n".join(lines[body_start:])

    # Remove stray H1s that duplicate the header
    body_md = re.sub(r'^# .+$', '', body_md, flags=re.MULTILINE)

    body_html = md_lib.markdown(body_md, extensions=["extra", "nl2br"])
    body_html = _style_resume_body(body_html)

    full_body = header_html + body_html
    return RESUME_HTML_TEMPLATE.format(css=RESUME_CSS, body=full_body)


def build_cover_html(content: str, candidate_name: str = "", contact_info: str = "") -> str:
    """Build a polished cover letter HTML."""
    lines = content.splitlines()

    # Extract title line (# Cover Letter Seed — ...)
    title_line = ""
    body_lines = []
    skip_first_hr = True

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and not title_line:
            title_line = stripped[2:]
        elif stripped == "---" and skip_first_hr:
            skip_first_hr = False
        else:
            body_lines.append(line)

    body_md = "\n".join(body_lines).strip()
    body_html = md_lib.markdown(body_md, extensions=["extra", "nl2br"])

    # Wrap paragraphs in cover-body
    body_html = f'<div class="cover-body">{body_html}</div>'

    # If title has "—" or "@", split it nicely
    position = title_line
    if "—" in title_line:
        parts = title_line.split("—", 1)
        position = parts[1].strip() if len(parts) > 1 else title_line

    # Build the header block
    if not candidate_name or not contact_info:
        p_name, p_contact = get_personal_info()
        candidate_name = candidate_name or p_name
        contact_info = contact_info or p_contact

    from datetime import date
    today = date.today().strftime("%B %d, %Y")

    header_html = f"""
<div class="cover-header">
  <div class="cover-name">{candidate_name}</div>
  <div class="cover-meta">{contact_info}</div>
</div>
<div class="cover-date">{today}</div>
<div class="cover-accent-bar"></div>
<h1>{position}</h1>
"""

    full_body = header_html + body_html

    return COVER_HTML_TEMPLATE.format(css=COVER_CSS, body=full_body)


# ─────────────────────────────────────────────
#  Main export function
# ─────────────────────────────────────────────

def export_pdf(content: str, doc_type: str | None = None) -> bytes:
    """
    Convert markdown content to a styled PDF.
    
    Args:
        content: Markdown text of the document.
        doc_type: 'resume' | 'cover' | None (auto-detect).
    
    Returns:
        PDF bytes.
    
    Raises:
        RuntimeError: if PDF generation fails.
    """
    if doc_type is None:
        doc_type = detect_doc_type(content)

    if doc_type == "cover":
        html = build_cover_html(content)
    else:
        html = build_resume_html(content)

    pdf_buffer = io.BytesIO()
    result = pisa.CreatePDF(
        src=io.StringIO(html),
        dest=pdf_buffer,
        encoding="utf-8"
    )

    if result.err:
        raise RuntimeError(f"xhtml2pdf error code: {result.err}")

    return pdf_buffer.getvalue()
