from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def login_to_mosaic(page):

    username = os.getenv('MOSAIC_USERNAME')
    password = os.getenv('MOSAIC_PASSWORD')
    
    page.goto('https://csprd.mcmaster.ca/psp/prcsprd/')
    page.wait_for_selector('input[name="userid"]', timeout=10000)

    page.fill('input[name="userid"]', username)
    page.fill('input[name="pwd"]', password)

    page.click('input[type="submit"][value="Sign In"]')
    page.wait_for_url('**/EMPLOYEE/SA/**', timeout=15000)

def search_for_course(page, subject, course_number, term):
    search_url = "https://csprd.mcmaster.ca/psc/prcsprd/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL"
    page.goto(search_url)
    page.wait_for_load_state('networkidle', timeout=30000)

    time.sleep(1)

    term_dropdown = '#CLASS_SRCH_WRK2_STRM\\$35\\$'

    page.select_option(term_dropdown, label=term)
    options = page.locator(f'{term_dropdown} option').all_inner_texts()

    for i, option_text in enumerate(options):
        if term in option_text or "2026" in option_text and "Winter" in option_text:
            page.select_option(term_dropdown, index=i)
            break

    page.fill('#SSR_CLSRCH_WRK_SUBJECT\\$0', subject)
    page.fill('#SSR_CLSRCH_WRK_CATALOG_NBR\\$1', course_number)
    page.click('#CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')

    page.wait_for_selector('img[src*="STATUS"]', timeout=5000)

def get_course_status(page):
    """
    Get the status of all course sections, excluding legend icons
    
    Returns:
        dict with overall status info
    """
    frames = page.frames
    working_frame = page

    # Check if we're in an iframe
    for frame in frames:
        if frame.name == 'TargetContent':
            working_frame = frame
            print("   Checking inside iframe")
            break

    # Wait for results to load
    time.sleep(2)
    
    # More specific selector: look for status images within table rows
    # This excludes the legend at the top
    status_locator = working_frame.locator('table tr img[alt="Open"], table tr img[alt="Closed"], table tr img[alt="Wait List"]')
    count = status_locator.count()

    if count == 0:
        page_text = working_frame.locator('body').inner_text()

        if 'No classes were found' in page_text or 'no results' in page_text.lower():
            print("   Page says: 'No classes were found'")
            return {'status': 'not_found'}

        if 'INNOVATE' in page_text or 'class section' in page_text.lower():
            print("   Found course text, waiting longer...")
            time.sleep(5)

            count = status_locator.count()
            print(f"   Retry: Found {count} status indicator(s)")

            if count == 0:
                print("   Still no status found")
                print(f"\n   Page content preview:\n{page_text[:500]}...\n")
                return {'status': 'not_found'}
        else:
            print("   Not on results page")
            return {'status': 'not_found'}

    # Skip first 3 icons (legend) and only count actual course sections
    # The legend always shows: Open, Closed, Wait List icons
    actual_sections_count = max(0, count - 3)
    print(f"   Found {count} status indicators (3 legend + {actual_sections_count} actual sections)")

    status_counts = {
        'open': 0,
        'closed': 0,
        'waitlist': 0
    }

    status_map = {
        'Open': 'open',
        'Closed': 'closed',
        'Wait List': 'waitlist'
    }

    # Count each status type, skipping the first 3 (legend icons)
    for i in range(3, count):
        alt_text = status_locator.nth(i).get_attribute('alt')
        status = status_map.get(alt_text, 'unknown')
        if status in status_counts:
            status_counts[status] += 1

    print(f"   Status breakdown (excluding legend): {status_counts['open']} open, {status_counts['closed']} closed, {status_counts['waitlist']} waitlist")
    
    if status_counts['open'] > 0:
        overall_status = 'open'
    elif status_counts['waitlist'] > 0:
        overall_status = 'waitlist'
    else:
        overall_status = 'closed'
    
    return {
        'status': overall_status,
        'details': status_counts,
        'total_sections': actual_sections_count
    }


def check_course_status(subject, course_number, term, browser=None, page=None):
    """
    Check course status for a single course

    Args:
        subject: Subject code (e.g., 'INSPIRE')
        course_number: Course number (e.g., '1PL3')
        term: Term (e.g., '2026 Winter')
        browser: Optional existing browser instance
        page: Optional existing page instance

    Returns:
        dict with status info
    """
    close_browser = False
    if browser is None:
        p = sync_playwright().start()
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page()
        login_to_mosaic(page)
        close_browser = True

    try:
        search_for_course(page, subject, course_number, term)

        status_info = get_course_status(page)

        result = {
            'course': f"{subject} {course_number}",
            'term': term,
            'status': status_info['status'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"   {subject} {course_number}: {result['status'].upper()}")

        return result

    finally:
        if close_browser:
            time.sleep(2)
            browser.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 4:
        subject = sys.argv[1]
        course_number = sys.argv[2]
        term = sys.argv[3]
    else:
        subject = "INSPIRE"
        course_number = "1PL3"
        term = "2026 Winter"

    print(f"Checking {subject} {course_number} ({term})...")
    result = check_course_status(subject, course_number, term)
    print(f"Final Status: {result['status'].upper()}")
    