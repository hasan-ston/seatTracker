"""
Notification module - handles sending emails and SMS
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send email notification

    Args:
        to_email: Recipient email
        subject: Email subject
        body: Email body (can include HTML)

    Returns:
        True if sent successfully, False otherwise
    """
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', smtp_username)

    if not smtp_username or not smtp_password:
        print("Email not configured (missing SMTP credentials in .env)")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        html_part = MIMEText(body, 'html')
        msg.attach(html_part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        print(f"Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_course_open_notification(email: str, subject: str, course_number: str, term: str):
    """
    Send notification that a course is now open

    Args:
        email: User's email
        subject: Course subject code
        course_number: Course number
        term: Term
    """
    email_subject = f"{subject} {course_number} is now OPEN!"

    email_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #7A003C;">Course Now Available!</h2>

        <p>Good news! A course you're tracking is now open for registration:</p>

        <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #7A003C; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Course:</strong> {subject} {course_number}</p>
            <p style="margin: 5px 0;"><strong>Term:</strong> {term}</p>
            <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: green; font-weight: bold;">OPEN</span></p>
        </div>

        <p><strong>Register now before seats fill up!</strong></p>

        <p>
            <a href="https://csprd.mcmaster.ca/psc/prcsprd/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL"
               style="background-color: #7A003C; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Go to Mosaic
            </a>
        </p>

        <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
        <p style="color: #666; font-size: 12px;">
            You're receiving this because you're tracking this course in McMaster Seat Tracker.
        </p>
    </body>
    </html>
    """

    return send_email(email, email_subject, email_body)


def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS notification (using Twilio or similar service)

    Args:
        phone: Phone number
        message: SMS message

    Returns:
        True if sent successfully, False otherwise
    """
    print(f"SMS to {phone}: {message}")
    print(f"SMS not implemented yet")
    return False


if __name__ == "__main__":
    print("Testing email notification...")
    send_course_open_notification(
        email="test@example.com",
        subject="COMPSCI",
        course_number="1MD3",
        term="2026 Winter"
    )
