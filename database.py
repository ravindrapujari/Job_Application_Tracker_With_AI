import sqlite3

DB_NAME = "jobs.db"

def get_connection():
    """Helper function to get a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

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

def get_applications():
    """Retrieves all job applications from the database, ordered newest first."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY id DESC")
        rows = cursor.fetchall()
        # Convert sqlite3.Row objects to standard Python dictionaries
        return [dict(row) for row in rows]

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
