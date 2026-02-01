"""
Database helper functions for seat tracker
"""

import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime


DB_PATH = os.getenv("DB_PATH", "database/courses.db")


def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


def get_active_course_watches() -> List[Dict]:
    """
    Get all active course watches from the database

    Returns:
        List of dicts with course watch info including user and course details
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT
            cw.id as watch_id,
            cw.user_id,
            cw.course_id,
            cw.status as current_status,
            cw.notify_on_open,
            cw.last_checked,
            c.subject,
            c.course_number,
            c.course_name,
            c.term,
            u.email,
            u.phone
        FROM course_watches cw
        JOIN courses c ON cw.course_id = c.id
        JOIN users u ON cw.user_id = u.id
        WHERE cw.active = 1
        ORDER BY cw.last_checked ASC NULLS FIRST
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    watches = [dict(row) for row in rows]

    cursor.close()
    conn.close()

    return watches


def update_course_watch_status(watch_id: int, new_status: str) -> bool:
    """
    Update the status of a course watch and record in history

    Args:
        watch_id: The course watch ID
        new_status: The new status ('open', 'closed', 'waitlist')

    Returns:
        True if status changed, False if same
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM course_watches WHERE id = ?", (watch_id,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        conn.close()
        return False

    current_status = result[0]

    status_changed = current_status != new_status

    cursor.execute("""
        UPDATE course_watches
        SET status = ?, last_checked = ?
        WHERE id = ?
    """, (new_status, datetime.now(), watch_id))

    conn.commit()
    cursor.close()
    conn.close()

    return status_changed


def create_notification(user_id: int, course_watch_id: int, notification_type: str):
    """
    Create a notification record

    Args:
        user_id: User ID
        course_watch_id: Course watch ID
        notification_type: Type of notification ('email', 'sms', 'both')
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notifications (user_id, course_watch_id, notification_type)
        VALUES (?, ?, ?)
    """, (user_id, course_watch_id, notification_type))

    conn.commit()
    cursor.close()
    conn.close()


def get_or_create_course(subject: str, course_number: str, term: str, course_name: Optional[str] = None) -> int:
    """
    Get course ID or create if doesn't exist

    Args:
        subject: Subject code (e.g., 'COMPSCI')
        course_number: Course number (e.g., '1MD3')
        term: Term (e.g., '2026 Winter')
        course_name: Optional course name

    Returns:
        Course ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM courses
        WHERE subject = ? AND course_number = ? AND term = ?
    """, (subject, course_number, term))

    result = cursor.fetchone()

    if result:
        course_id = result[0]
    else:
        cursor.execute("""
            INSERT INTO courses (subject, course_number, course_name, term)
            VALUES (?, ?, ?, ?)
        """, (subject, course_number, course_name, term))
        course_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()

    return course_id


def get_or_create_user(email: str, phone: Optional[str] = None) -> int:
    """
    Get user ID or create if doesn't exist

    Args:
        email: User email
        phone: Optional phone number

    Returns:
        User ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()

    if result:
        user_id = result[0]
    else:
        cursor.execute("""
            INSERT INTO users (email, phone)
            VALUES (?, ?)
        """, (email, phone))
        user_id = cursor.lastrowid
        conn.commit()

    cursor.close()
    conn.close()

    return user_id


def cleanup_old_records(retention_days: int = 4) -> dict:
    """
    Delete old notifications and expired password reset tokens to prevent unbounded database growth.

    Args:
        retention_days: Number of days to keep records (default 4)

    Returns:
        Dict with counts of deleted records
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Delete old notifications records
    cursor.execute("""
        DELETE FROM notifications
        WHERE sent_at < datetime('now', ?)
    """, (f'-{retention_days} days',))
    notifications_deleted = cursor.rowcount

    # Delete expired or used password reset tokens
    cursor.execute("""
        DELETE FROM password_reset_tokens
        WHERE used = 1 OR expires_at < datetime('now')
    """)
    tokens_deleted = cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    return {
        'notifications_deleted': notifications_deleted,
        'tokens_deleted': tokens_deleted
    }


def create_course_watch(user_id: int, course_id: int, notify_on_open: bool = True) -> int:
    """
    Create a new course watch

    Args:
        user_id: User ID
        course_id: Course ID
        notify_on_open: Whether to notify when course opens

    Returns:
        Course watch ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO course_watches (user_id, course_id, notify_on_open)
        VALUES (?, ?, ?)
    """, (user_id, course_id, notify_on_open))

    watch_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return watch_id
