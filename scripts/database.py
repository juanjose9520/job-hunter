"""
Database initialization and helper functions.
Creates jobs.db with all required tables on first run.
"""

import sqlite3
from config import DB_PATH


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            company         TEXT,
            url             TEXT UNIQUE NOT NULL,
            board           TEXT,
            description     TEXT,
            salary_raw      TEXT,
            salary_monthly  REAL,
            salary_listed   INTEGER DEFAULT 0,  -- 1=yes, 0=no
            remote          INTEGER DEFAULT 1,
            score           REAL,
            score_breakdown TEXT,               -- JSON string
            status          TEXT DEFAULT 'new', -- new|shortlisted|applied|response|closed|archived
            discovered_at   TEXT DEFAULT (datetime('now')),
            notes           TEXT
        );

        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id          INTEGER NOT NULL REFERENCES jobs(id),
            applied_at      TEXT DEFAULT (datetime('now')),
            resume_path     TEXT,
            cover_seed      TEXT,
            response_status TEXT DEFAULT 'pending', -- pending|interview|rejected|offer|ghosted
            notes           TEXT
        );

        CREATE TABLE IF NOT EXISTS keywords (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      INTEGER REFERENCES jobs(id),
            keyword     TEXT NOT NULL,
            category    TEXT,   -- tool|skill|signal
            frequency   INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_status  ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_score   ON jobs(score);
        CREATE INDEX IF NOT EXISTS idx_keywords_kw  ON keywords(keyword);
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")


def get_jobs(status=None, min_score=None):
    conn = get_connection()
    q = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if status:
        q += " AND status = ?"
        params.append(status)
    if min_score is not None:
        q += " AND score >= ?"
        params.append(min_score)
    q += " ORDER BY score DESC, discovered_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_job_status(job_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()


def upsert_job(job: dict) -> int | None:
    """Insert or skip if URL already exists. Returns new id or None."""
    conn = get_connection()
    try:
        c = conn.execute("""
            INSERT INTO jobs (title, company, url, board, description,
                              salary_raw, salary_monthly, salary_listed, remote)
            VALUES (:title, :company, :url, :board, :description,
                    :salary_raw, :salary_monthly, :salary_listed, :remote)
        """, job)
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None  # duplicate URL
    finally:
        conn.close()


def save_application(job_id: int, resume_path: str, cover_seed: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO applications (job_id, resume_path, cover_seed)
        VALUES (?, ?, ?)
    """, (job_id, resume_path, cover_seed))
    conn.execute("UPDATE jobs SET status = 'applied' WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def save_keywords(job_id: int, keywords: list[dict]):
    conn = get_connection()
    conn.executemany("""
        INSERT INTO keywords (job_id, keyword, category)
        VALUES (:job_id, :keyword, :category)
    """, [{"job_id": job_id, **kw} for kw in keywords])
    conn.commit()
    conn.close()


def migrate_db():
    """Apply schema migrations for existing databases."""
    conn = get_connection()
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN follow_up_date TEXT")
        conn.commit()
    except Exception:
        pass  # Column already exists
    conn.close()


def delete_job(job_id: int):
    """Hard delete a job and its associated keywords/applications."""
    conn = get_connection()
    # Delete from dependent tables first (if FKs aren't cascading)
    conn.execute("DELETE FROM keywords WHERE job_id = ?", (job_id,))
    conn.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
