"""
Main scraper loop - checks all active course watches
"""

import sys
import os
import time
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_SCRAPE_INTERVAL_MINUTES = 5
BROWSER_RESTART_CHECK_COUNT = 2880  # ~12 hours at 15 sec intervals
COURSE_CHECK_DELAY_SECONDS = 2
CLEANUP_RETENTION_DAYS = 4


def send_notification(user_email, user_phone, course_info, status):
    """
    Send notification to user about course status change

    Args:
        user_email: User's email
        user_phone: User's phone (optional)
        course_info: Dict with course details
        status: New status
    """
    logger.info(f"Sending notification to {user_email} for {course_info['subject']} {course_info['course_number']} - Status: {status.upper()}")

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
    logger.info("=" * 70)
    logger.info(f"Starting scraper run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    watches = get_active_course_watches()

    if not watches:
        logger.info("No active course watches found in database")
        return browser, page

    logger.info(f"Found {len(watches)} active course watch(es)")

    # Only create browser if not provided
    if browser is None:
        logger.info("Launching browser...")
        p = sync_playwright().start()
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page()

        logger.info("Logging in to Mosaic...")
        try:
            login_to_mosaic(page)
            logger.info("Logged in successfully")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            browser.close()
            return None, None
    else:
        logger.debug("Reusing existing browser session...")

    logger.info(f"Checking {len(watches)} course(s)...")
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
                logger.info(f"Status changed: {old_status} -> {new_status}")

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

            time.sleep(COURSE_CHECK_DELAY_SECONDS)

        except Exception as e:
            errors += 1
            logger.error(f"Error checking {watch['subject']} {watch['course_number']}: {e}")
            continue

    # Cleanup old records to prevent database growth
    cleanup_result = cleanup_old_records(retention_days=CLEANUP_RETENTION_DAYS)

    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Courses checked: {checked}/{len(watches)}")
    logger.info(f"Status changes: {status_changed}")
    logger.info(f"Errors: {errors}")
    if cleanup_result['notifications_deleted'] > 0:
        logger.info(f"Cleaned up: {cleanup_result['notifications_deleted']} old notifications")
    logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    return browser, page


def run_continuous(interval_minutes=DEFAULT_SCRAPE_INTERVAL_MINUTES):
    """
    Run scraper continuously with specified interval

    Args:
        interval_minutes: Minutes between scraper runs
    """
    logger.info(f"Running in continuous mode (every {interval_minutes} minutes)")
    logger.info(f"Browser will restart every {BROWSER_RESTART_CHECK_COUNT} checks (~12 hours) to prevent memory buildup")
    logger.info("Press Ctrl+C to stop")

    browser = None
    page = None
    check_count = 0

    try:
        while True:
            try:
                # Restart browser periodically to prevent memory buildup
                if check_count > 0 and check_count % BROWSER_RESTART_CHECK_COUNT == 0:
                    logger.info(f"[MEMORY MANAGEMENT] Restarting browser after {check_count} checks...")
                    if browser is not None:
                        browser.close()
                    browser = None
                    page = None

                browser, page = scrape_all_courses(browser, page)
                check_count += 1

                logger.info(f"Waiting {interval_minutes} minutes until next check...")
                time.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.info(f"Retrying in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        logger.info("Stopping scraper...")
    finally:
        # Clean up browser when stopping
        if browser is not None:
            logger.info("Closing browser...")
            browser.close()
            logger.info("Browser closed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SCRAPE_INTERVAL_MINUTES
        run_continuous(interval)
    else:
        browser, page = scrape_all_courses()
        if browser is not None:
            logger.info("Closing browser...")
            browser.close()
