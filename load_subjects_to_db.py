"""
Load subject list into the subjects table
"""

import json
import sqlite3
import os


def load_subjects_to_db():
    db_path = os.getenv("DB_PATH", "database/courses.db")

    print("Reading subjects.json...")
    with open("subjects.json", "r", encoding="utf-8") as f:
        subjects = json.load(f)

    print(f"   Found {len(subjects)} raw subjects")

    print(f"\nConnecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("   Connected")

    inserted = 0
    skipped = 0
    seen_codes = set()

    print("\nInserting subjects into subjects table...")

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
            print(f"   Error inserting {subject_code}: {e}")
            skipped += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM subjects")
    total = cursor.fetchone()[0]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Subjects inserted: {inserted}")
    print(f"Skipped: {skipped}")
    print(f"Total subjects in database: {total}")
    print("=" * 60)

    print("\nSample subjects:")
    cursor.execute("""
        SELECT code, name
        FROM subjects
        ORDER BY code
        LIMIT 5
    """)
    for code, name in cursor.fetchall():
        print(f"   {code}: {name}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    load_subjects_to_db()
