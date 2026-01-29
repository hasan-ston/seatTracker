"""
Initialize database schema
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "database/courses.db")

def init_database():
    logger.info("Creating database schema...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: Add password_hash and role columns if they don't exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'password_hash' not in columns:
        logger.info("Migrating users table: adding password_hash column")
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    
    if 'role' not in columns:
        logger.info("Migrating users table: adding role column")
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            action TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            course_number TEXT NOT NULL,
            course_name TEXT,
            term TEXT NOT NULL,
            UNIQUE(subject, course_number, term)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_watches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            status TEXT DEFAULT 'closed',
            active BOOLEAN DEFAULT 1,
            notify_on_open BOOLEAN DEFAULT 1,
            last_checked TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            UNIQUE(user_id, course_id)
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_watch_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_watch_id) REFERENCES course_watches(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create indexes for query optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_course_watches_user_id ON course_watches(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_course_watches_active ON course_watches(active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_course_watches_course_id ON course_watches(course_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_name ON subjects(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token)")

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("Database created successfully!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
