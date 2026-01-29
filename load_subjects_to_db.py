"""
Load subject list into the subjects table
"""

import json
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


def load_subjects_to_db():
    db_path = os.getenv("DB_PATH", "database/courses.db")

    logger.info("Reading subjects.json...")
    with open("subjects.json", "r", encoding="utf-8") as f:
        subjects = json.load(f)

    logger.info(f"Found {len(subjects)} raw subjects")

    logger.info(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    logger.info("Connected")

    inserted = 0
    skipped = 0
    seen_codes = set()

    logger.info("Inserting subjects into subjects table...")

    for s in subjects:
        subject_code = s.get("code", "").strip()
        subject_name = s.get("name", "").strip()
        subject_action = s.get("action", "").strip()

        if not subject_code or subject_code.lower() == "select":
            skipped += 1
            continue

        if subject_code in seen_codes:
            skipped += 1
            continue

        seen_codes.add(subject_code)

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO subjects
                    (code, name, action)
                VALUES (?, ?, ?)
            """, (
                subject_code,
                subject_name,
                subject_action
            ))

            if cursor.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

        except Exception as e:
            logger.error(f"Error inserting {subject_code}: {e}")
            skipped += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM subjects")
    total = cursor.fetchone()[0]

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Subjects inserted: {inserted}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Total subjects in database: {total}")
    logger.info("=" * 60)

    logger.info("Sample subjects:")
    cursor.execute("""
        SELECT code, name
        FROM subjects
        ORDER BY code
        LIMIT 5
    """)
    for code, name in cursor.fetchall():
        logger.info(f"   {code}: {name}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_subjects_to_db()
