"""
Database migration script - handles schema updates for existing databases
"""

import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "database/courses.db")


def get_existing_columns(cursor, table_name: str) -> set:
    """Get set of column names for a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def add_column_if_missing(conn, cursor, table_name: str, column_name: str, column_def: str):
    """Add a column to a table if it doesn't exist"""
    columns = get_existing_columns(cursor, table_name)
    if column_name not in columns:
        print(f"  Adding column {table_name}.{column_name}...")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
        conn.commit()
        return True
    return False


def table_exists(cursor, table_name: str) -> bool:
    """Check if a table exists"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def migrate_database():
    """Run all database migrations"""
    print("Running database migrations...")
    
    if not os.path.exists(DB_PATH):
        print("Database does not exist yet. Run init_db.py first.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    migrations_applied = 0
    
    # Migration 1: Add password_hash and role to users table
    if table_exists(cursor, "users"):
        if add_column_if_missing(conn, cursor, "users", "password_hash", "TEXT"):
            migrations_applied += 1
        if add_column_if_missing(conn, cursor, "users", "role", "TEXT DEFAULT 'user'"):
            migrations_applied += 1
    
    # Migration 2: Ensure password_reset_tokens table exists (for older schemas)
    if not table_exists(cursor, "password_reset_tokens"):
        print("  Creating password_reset_tokens table...")
        cursor.execute("""
            CREATE TABLE password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token)")
        conn.commit()
        migrations_applied += 1
    
    cursor.close()
    conn.close()
    
    if migrations_applied > 0:
        print(f"Applied {migrations_applied} migration(s)")
    else:
        print("No migrations needed - database is up to date")


if __name__ == "__main__":
    migrate_database()
