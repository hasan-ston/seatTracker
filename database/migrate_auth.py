"""
Migration script to add authentication fields to users table
"""

import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "database/courses.db")

def migrate():
    """Add password and role fields to users table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Adding authentication fields to users table...")

    try:
        cursor.execute("""
            ALTER TABLE users ADD COLUMN password_hash TEXT;
        """)
        print("   Added password_hash column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("   password_hash column already exists")
        else:
            raise

    try:
        cursor.execute("""
            ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
        """)
        print("   Added role column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("   role column already exists")
        else:
            raise

    try:
        cursor.execute("""
            ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1;
        """)
        print("   Added is_verified column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("   is_verified column already exists")
        else:
            raise

    conn.commit()
    cursor.close()
    conn.close()

    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()
