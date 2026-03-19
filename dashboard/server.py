"""
Lightweight Flask API to serve data to the local dashboard.
"""

import threading
import webbrowser
import warnings
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

warnings.filterwarnings("ignore")
from flask import Flask, jsonify, request, send_from_directory
from scripts.database import get_connection, update_job_status, delete_job
from scripts.discover import run_discovery
from scripts.score import run_scoring
from scripts.keywords import build_skills_log
from scripts.tailor import tailor_resume
from scripts.job_scraper_apis import run_all_apis
from scripts.job_scraper_jobspy import run_jobspy_scraper
from config import DASHBOARD_DIR, SEARCH_QUERIES

app = Flask(__name__, static_folder=str(DASHBOARD_DIR))

# CORS allow local
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route("/api/jobs")
def api_jobs():
    conn = get_connection()
    from config import SCORE_SHOW_THRESHOLD
    query = """
        SELECT j.*, 
               (SELECT resume_path FROM applications a WHERE a.job_id = j.id ORDER BY id DESC LIMIT 1) as resume_path
        FROM jobs j
        WHERE j.score >= ? OR j.status != 'new'
        ORDER BY j.score DESC, j.discovered_at DESC
    """
    rows = conn.execute(query, (SCORE_SHOW_THRESHOLD,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/jobs/<int:job_id>/status", methods=["PUT"])
def api_update_status(job_id):
    data = request.json
    status = data.get("status")
    if status:
        update_job_status(job_id, status)
        return jsonify({"success": True})
    return jsonify({"error": "Bad Request"}), 400

@app.route("/api/jobs/<int:job_id>/description", methods=["PUT"])
def api_update_description(job_id):
    data = request.json
    description = data.get("description")
    if description is not None:
        conn = get_connection()
        conn.execute("UPDATE jobs SET description = ? WHERE id = ?", (description, job_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    return jsonify({"error": "Bad Request"}), 400

@app.route("/api/jobs/<int:job_id>/notes", methods=["PUT"])
def api_update_notes(job_id):
    data = request.json
    notes = data.get("notes")
    if notes is not None:
        conn = get_connection()
        conn.execute("UPDATE jobs SET notes = ? WHERE id = ?", (notes, job_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    return jsonify({"error": "Bad Request"}), 400

@app.route("/api/discover", methods=["POST"])
def api_discover():
    # Run the deep pipeline: APIs + JobSpy, then the original scrapers, then score
    run_all_apis()
    run_jobspy_scraper(SEARCH_QUERIES, results_wanted=15)
    ds_summary = run_discovery()
    sc_summary = run_scoring()
    return jsonify({
        "discovery": ds_summary,
        "scoring": sc_summary
    })

@app.route("/api/jobs/<int:job_id>", methods=["DELETE"])
def api_delete_job(job_id):
    delete_job(job_id)
    return jsonify({"success": True})


@app.route("/api/tailor/<int:job_id>", methods=["POST"])
def api_tailor(job_id):
    path = tailor_resume(job_id)
    if path:
        return jsonify({"success": True, "path": str(path)})
    return jsonify({"error": "Tailoring failed"}), 500

@app.route("/api/jobs/<int:job_id>/files", methods=["GET"])
def api_get_files(job_id):
    conn = get_connection()
    row = conn.execute("SELECT resume_path FROM applications WHERE job_id = ? ORDER BY id DESC LIMIT 1", (job_id,)).fetchone()
    conn.close()
    if not row or not row["resume_path"]:
        return jsonify({"error": "Not tailored yet"}), 404
    
    import pathlib
    pdf_path = pathlib.Path(row["resume_path"])
    out_dir = pdf_path.parent
    
    resume_md = ""
    cover_md = ""
    artifacts_md = ""
    try:
        resume_md = (out_dir / "resume.md").read_text(encoding="utf-8")
    except Exception: pass
    
    try:
        cover_md = (out_dir / "cover_seed.md").read_text(encoding="utf-8")
    except Exception: pass
    
    try:
        artifacts_md = (out_dir / "artifacts.md").read_text(encoding="utf-8")
    except Exception: pass
    
    return jsonify({
        "success": True,
        "resume": resume_md,
        "cover_seed": cover_md,
        "artifacts": artifacts_md
    })

@app.route("/api/jobs/<int:job_id>/chat", methods=["POST"])
def api_chat(job_id):
    data = request.json
    instruction = data.get("instruction")
    current_doc = data.get("document", "")
    doc_type = data.get("doc_type", "resume")
    image_b64 = data.get("image")
    image_mime_type = data.get("image_mime_type")
    
    if not instruction:
        return jsonify({"error": "Missing instruction"}), 400
        
    import sys
    import base64
    from google import genai as genai_sdk
    from google.genai import types as genai_types
    from config import GEMINI_API_KEY, GEMINI_MODEL, BASE_RESUME
    _chat_client = genai_sdk.Client(api_key=GEMINI_API_KEY)
    
    conn = get_connection()
    job = conn.execute("SELECT description FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    
    job_desc = job["description"] if job and job["description"] else "No description available."
    base_resume = ""
    if BASE_RESUME.exists():
        base_resume = BASE_RESUME.read_text(encoding="utf-8")
    
    prompt_text = f"""
You are an expert career consultant editing a candidate's {doc_type}.

### CONTEXT:
Job Description:
{job_desc[:4000]}

Candidate Base Resume:
{base_resume}

### TASK:
Apply the following instruction to the document below.

Instruction: {instruction}

Current Document String:
{current_doc}

Return ONLY the fully updated {doc_type} text in formatting appropriate for the document (usually markdown). 
Do not include any conversational preamble or explanations.
"""
    contents = [prompt_text]
    
    if image_b64 and image_mime_type:
        try:
            image_data = base64.b64decode(image_b64)
            contents.append(genai_types.Part.from_bytes(data=image_data, mime_type=image_mime_type))
        except Exception as e:
            print(f"[API Chat Error] Image processing failed: {e}", file=sys.stderr)

    try:
        response = _chat_client.models.generate_content(model=GEMINI_MODEL, contents=contents)
        updated_md = response.text.strip()
        # Clean up markdown fences if present
        if updated_md.startswith("```markdown"):
            updated_md = updated_md[11:-3].strip()
        elif updated_md.startswith("```"):
            updated_md = updated_md[3:-3].strip()
        return jsonify({"success": True, "document": updated_md})
    except Exception as e:
        print(f"[API Chat Error] {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route("/api/jobs/<int:job_id>/save-file", methods=["POST"])
def api_save_file(job_id):
    data = request.json
    doc_type = data.get("doc_type", "resume")
    content = data.get("content")
    
    conn = get_connection()
    row = conn.execute("SELECT resume_path FROM applications WHERE job_id = ? ORDER BY id DESC LIMIT 1", (job_id,)).fetchone()
    conn.close()
    
    if not row or not row["resume_path"]:
        return jsonify({"error": "No tailored resume found"}), 404
        
    import pathlib
    base_dir = pathlib.Path(row["resume_path"]).parent
    
    try:
        if doc_type == "resume":
            (base_dir / "resume.md").write_text(content, encoding="utf-8")
        elif doc_type == "cover":
            (base_dir / "cover_seed.md").write_text(content, encoding="utf-8")
        else:
            (base_dir / "artifacts.md").write_text(content, encoding="utf-8")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/jobs/<int:job_id>/export-pdf", methods=["POST"])
def api_export_pdf(job_id):
    import sys
    import io
    from flask import send_file
    from scripts.pdf_export import export_pdf
    
    data = request.json
    content = data.get("content")
    if not content:
        return jsonify({"error": "Missing content"}), 400
        
    try:
        pdf_bytes = export_pdf(content)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="document.pdf"
        )
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route("/api/skills")
def api_skills():
    log = build_skills_log()
    return jsonify(log)


def run_server(port=8080):
    print(f"\n[Dashboard] Starting on http://localhost:{port}/")
    print("  Press Ctrl+C to quit.")
    
    # Auto-open browser
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}/")).start()
    
    # Run server (single-threaded for SQLite safety)
    app.run(host="127.0.0.1", port=port, debug=False)

if __name__ == "__main__":
    run_server()
