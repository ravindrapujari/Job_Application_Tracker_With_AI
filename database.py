import sqlite3
from contextlib import contextmanager

DB_NAME = "jobs.db"

@contextmanager
def get_connection():
    """
    Context manager that provides a SQLite connection with row factory
    and ensures proper closing to prevent database locks.
    """
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Creates the applications table if it does not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                salary TEXT,
                stage TEXT NOT NULL,
                applied_on TEXT NOT NULL,
                link TEXT
            )
        """)
        conn.commit()

def add_application(company, role, salary, stage, applied_on, link):
    """Inserts a new job application into the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (company, role, salary, stage, applied_on, link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company, role, salary, stage, applied_on, link))
        conn.commit()

def get_applications(stage=None, search_query=None):
    """
    Retrieves job applications with optional stage filtering and company/role search.
    Ordered newest first.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM applications WHERE 1=1"
        params = []

        # Filter by stage if specified and not 'All'
        if stage and stage != "All":
            query += " AND stage = ?"
            params.append(stage)

        # Search filter across company or role
        if search_query:
            query += " AND (company LIKE ? OR role LIKE ?)"
            search_param = f"%{search_query.strip()}%"
            params.extend([search_param, search_param])

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_stats():
    """
    Calculates dashboard metrics:
    - Total applications
    - Interviews
    - Offers Accepted
    - Offers Rejected
    - Response rate percentage
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # Total applications
        cursor.execute("SELECT COUNT(*) FROM applications")
        total = cursor.fetchone()[0]

        # Interviews scheduled
        cursor.execute("SELECT COUNT(*) FROM applications WHERE stage = 'Interview Scheduled'")
        interviews = cursor.fetchone()[0]

        # Offers accepted
        cursor.execute("SELECT COUNT(*) FROM applications WHERE stage = 'Offer Accepted'")
        offers_accepted = cursor.fetchone()[0]

        # Offers rejected
        cursor.execute("SELECT COUNT(*) FROM applications WHERE stage = 'Offer Rejected'")
        offers_rejected = cursor.fetchone()[0]

        # Applications that received any response (Interview or Offer stage)
        cursor.execute("""
            SELECT COUNT(*) FROM applications 
            WHERE stage IN ('Interview Scheduled', 'Offer Generated', 'Offer Accepted', 'Offer Rejected')
        """)
        responses = cursor.fetchone()[0]

        response_rate = (responses / total * 100.0) if total > 0 else 0.0

        return {
            "total": total,
            "interviews": interviews,
            "offers_accepted": offers_accepted,
            "offers_rejected": offers_rejected,
            "response_rate": response_rate,
        }

def update_stage(app_id, new_stage):
    """Updates the stage of an existing job application."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE applications
            SET stage = ?
            WHERE id = ?
        """, (new_stage, app_id))
        conn.commit()

def delete_application(app_id):
    """Deletes a job application by its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
