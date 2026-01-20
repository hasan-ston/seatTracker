"""
Main scraper loop - checks all active course watches
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from scraper.mosaic_scraper import login_to_mosaic, check_course_status
from scraper.notifier import send_course_open_notification, send_sms
from database.db_helper import (
    get_active_course_watches,
    update_course_watch_status,
    create_notification,
    cleanup_old_records
)


def send_notification(user_email, user_phone, course_info, status):
    """
    Send notification to user about course status change

    Args:
        user_email: User's email
        user_phone: User's phone (optional)
        course_info: Dict with course details
        status: New status
    """
    print(f"\nSENDING NOTIFICATION:")
    print(f"   To: {user_email}")
    print(f"   Course: {course_info['subject']} {course_info['course_number']}")
    print(f"   Status: {status.upper()}")

    if status == 'open':
        send_course_open_notification(
            email=user_email,
            subject=course_info['subject'],
            course_number=course_info['course_number'],
            term=course_info['term']
        )

        if user_phone:
            message = f"{course_info['subject']} {course_info['course_number']} is now OPEN! Register at mosaic.mcmaster.ca"
            send_sms(user_phone, message)


def scrape_all_courses(browser=None, page=None):
    """
    Main scraping function - checks all active course watches

    Args:
        browser: Optional existing browser instance (for reuse)
        page: Optional existing page instance (for reuse)

    Returns:
        tuple: (browser, page) for reuse in next iteration
    """
    print("\n" + "=" * 70)
    print(f"Starting scraper run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    watches = get_active_course_watches()

    if not watches:
        print("\nNo active course watches found in database")
        print("   Add some watches first!")
        return browser, page

    print(f"\nFound {len(watches)} active course watch(es)")

    # Only create browser if not provided
    if browser is None:
        print("\nLaunching browser...")
        p = sync_playwright().start()
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page()

        print("Logging in to Mosaic...")
        try:
            login_to_mosaic(page)
            print("Logged in successfully")
        except Exception as e:
            print(f"Login failed: {e}")
            browser.close()
            return None, None
    else:
        print("\nReusing existing browser session...")

    print(f"\nChecking {len(watches)} course(s)...")
    checked = 0
    status_changed = 0
    errors = 0

    for watch in watches:
        try:
            result = check_course_status(
                subject=watch['subject'],
                course_number=watch['course_number'],
                term=watch['term'],
                browser=browser,
                page=page
            )

            new_status = result['status']
            old_status = watch['current_status']

            changed = update_course_watch_status(watch['watch_id'], new_status)

            if changed:
                status_changed += 1
                print(f"Status changed: {old_status} -> {new_status}")

                if new_status == 'open' and watch['notify_on_open']:
                    send_notification(
                        watch['email'],
                        watch['phone'],
                        watch,
                        new_status
                    )
                    create_notification(
                        watch['user_id'],
                        watch['watch_id'],
                        'email'
                    )

            checked += 1

            time.sleep(2)

        except Exception as e:
            errors += 1
            print(f"Error checking {watch['subject']} {watch['course_number']}: {e}")
            continue

    # Cleanup old records to prevent database growth
    cleanup_result = cleanup_old_records(retention_days=4)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Courses checked: {checked}/{len(watches)}")
    print(f"Status changes: {status_changed}")
    print(f"Errors: {errors}")
    if cleanup_result['notifications_deleted'] > 0:
        print(f"Cleaned up: {cleanup_result['notifications_deleted']} old notifications")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    return browser, page


def run_continuous(interval_minutes=5):
    """
    Run scraper continuously with specified interval

    Args:
        interval_minutes: Minutes between scraper runs
    """
    print(f"\nRunning in continuous mode (every {interval_minutes} minutes)")
    print("   Browser will restart every 2880 checks (~12 hours) to prevent memory buildup")
    print("   Press Ctrl+C to stop")

    browser = None
    page = None
    check_count = 0

    try:
        while True:
            try:
                # Restart browser every 2880 checks (~12 hours at 15 sec intervals)
                if check_count > 0 and check_count % 2880 == 0:
                    print(f"\n[MEMORY MANAGEMENT] Restarting browser after {check_count} checks...")
                    if browser is not None:
                        browser.close()
                    browser = None
                    page = None

                browser, page = scrape_all_courses(browser, page)
                check_count += 1

                print(f"\nWaiting {interval_minutes} minutes until next check...")
                time.sleep(interval_minutes * 60)
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                print(f"   Retrying in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\n\nStopping scraper...")
    finally:
        # Clean up browser when stopping
        if browser is not None:
            print("Closing browser...")
            browser.close()
            print("Browser closed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else 5
        run_continuous(interval)
    else:
        browser, page = scrape_all_courses()
        if browser is not None:
            print("\nClosing browser...")
            browser.close()
