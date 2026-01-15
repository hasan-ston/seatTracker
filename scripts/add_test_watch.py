"""
Script to add a test course watch to the database
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_helper import (
    get_or_create_user,
    get_or_create_course,
    create_course_watch
)


def add_test_watch():
    """Add a test course watch for testing the scraper"""

    print("\nAdding test course watch...")

    email = input("Enter your email: ").strip()
    phone = input("Enter your phone (optional, press Enter to skip): ").strip() or None

    user_id = get_or_create_user(email, phone)
    print(f"   User ID: {user_id}")

    subject = input("Enter subject code (e.g., INSPIRE): ").strip().upper()
    course_number = input("Enter course number (e.g., 1PL3): ").strip()
    term = input("Enter term (e.g., 2026 Winter): ").strip()

    course_id = get_or_create_course(subject, course_number, term)
    print(f"   Course ID: {course_id}")

    notify = input("Notify when open? (y/n, default=y): ").strip().lower() != 'n'

    watch_id = create_course_watch(user_id, course_id, notify)
    print(f"   Course watch ID: {watch_id}")

    print("\nTest watch added successfully!")
    print(f"   {email} is now watching {subject} {course_number} ({term})")


if __name__ == "__main__":
    add_test_watch()
