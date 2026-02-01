"""
Flask web application for McMaster Seat Tracker (User + Admin)
"""

import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database.db_helper import (
    get_or_create_user,
    get_or_create_course,
    create_course_watch,
    get_active_course_watches,
    get_connection
)

app = Flask(__name__,
            template_folder='../frontend/user_templates',
            static_folder='../frontend/static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

MAX_WATCHES_PER_USER = 2

# Admin credentials
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')


def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/google4f429853378b8a4f.html')
def google_verification():
    """Google site verification"""
    return 'google-site-verification: google4f429853378b8a4f.html'


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip() or None

        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('register'))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            flash('Email already registered', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (email, phone, password_hash, role)
            VALUES (?, ?, ?, 'user')
        """, (email, phone, password_hash))

        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        session['user_id'] = user_id
        session['email'] = email
        session['role'] = 'user'

        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('login'))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, email, password_hash, role FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or not user[2]:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

        if not check_password_hash(user[2], password):
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

        session['user_id'] = user[0]
        session['email'] = user[1]
        session['role'] = user[3] or 'user'

        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Please enter your email address', 'error')
            return redirect(url_for('forgot_password'))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            user_id = user[0]

            # Delete any existing unused tokens for this user
            cursor.execute(
                'DELETE FROM password_reset_tokens WHERE user_id = ? AND used = 0',
                (user_id,)
            )

            # Create new token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)

            cursor.execute("""
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, token, expires_at))

            conn.commit()

            # Send email
            from scraper.notifier import send_email
            reset_url = url_for('reset_password', token=token, _external=True)

            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #7A003C;">Password Reset Request</h2>

                <p>You requested to reset your password for McMaster Seat Tracker.</p>

                <p>Click the link below to reset your password:</p>

                <p>
                    <a href="{reset_url}"
                       style="background-color: #7A003C; color: white; padding: 10px 20px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </p>

                <p>Or copy this link: {reset_url}</p>

                <p style="color: #666; font-size: 12px;">
                    This link expires in 1 hour. If you didn't request this, you can ignore this email.
                </p>
            </body>
            </html>
            """

            send_email(email, "Password Reset - McMaster Seat Tracker", email_body)

        cursor.close()
        conn.close()

        # Always show success (don't reveal if email exists)
        flash('If an account with that email exists, you will receive a password reset link shortly.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    conn = get_connection()
    cursor = conn.cursor()

    # Validate token
    cursor.execute("""
        SELECT id, user_id, expires_at, used
        FROM password_reset_tokens
        WHERE token = ?
    """, (token,))

    token_record = cursor.fetchone()

    if not token_record:
        flash('Invalid or expired reset link', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('forgot_password'))

    token_id, user_id, expires_at, used = token_record

    # Check if used
    if used:
        flash('This reset link has already been used', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('forgot_password'))

    # Check if expired
    try:
        if '.' in expires_at:
            expiry_time = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f')
        else:
            expiry_time = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
        if expiry_time < datetime.now():
            flash('This reset link has expired', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('forgot_password'))
    except ValueError:
        flash('Invalid reset link', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('reset_password', token=token))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('reset_password', token=token))

        # Update password
        password_hash = generate_password_hash(password)
        cursor.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (password_hash, user_id)
        )

        # Mark token as used
        cursor.execute(
            'UPDATE password_reset_tokens SET used = 1 WHERE id = ?',
            (token_id,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash('Password reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('login'))

    cursor.close()
    conn.close()
    return render_template('reset_password.html', token=token)


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - shows their watches"""
    user_id = session['user_id']

    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cw.id as watch_id,
            c.subject,
            c.course_number,
            c.course_name,
            c.term,
            cw.status,
            cw.notify_on_open,
            cw.last_checked,
            cw.created_at
        FROM course_watches cw
        JOIN courses c ON cw.course_id = c.id
        WHERE cw.user_id = ? AND cw.active = 1
        ORDER BY cw.created_at DESC
    """, (user_id,))

    watches = cursor.fetchall()
    watch_count = len(watches)
    can_add_more = watch_count < MAX_WATCHES_PER_USER

    cursor.close()
    conn.close()

    return render_template('dashboard.html',
                          watches=watches,
                          watch_count=watch_count,
                          max_watches=MAX_WATCHES_PER_USER,
                          can_add_more=can_add_more)


@app.route('/add-watch', methods=['GET', 'POST'])
@login_required
def add_watch():
    """Add a new course watch"""
    user_id = session['user_id']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM course_watches
        WHERE user_id = ? AND active = 1
    """, (user_id,))
    watch_count = cursor.fetchone()[0]

    if watch_count >= MAX_WATCHES_PER_USER:
        flash(f'You can only watch up to {MAX_WATCHES_PER_USER} courses. Delete a watch to add a new one.', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip().upper()
        course_number = request.form.get('course_number', '').strip().upper()
        term = request.form.get('term', '').strip()
        notify_on_open = request.form.get('notify_on_open') == 'on'

        if not subject or not course_number or not term:
            flash('All fields are required', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('add_watch'))

        course_id = get_or_create_course(subject, course_number, term)

        cursor.execute("""
            SELECT id, active FROM course_watches
            WHERE user_id = ? AND course_id = ?
        """, (user_id, course_id))

        existing_watch = cursor.fetchone()

        if existing_watch:
            watch_id, is_active = existing_watch
            if is_active:
                flash('You are already watching this course', 'error')
                cursor.close()
                conn.close()
                return redirect(url_for('add_watch'))
            else:
                cursor.execute("""
                    UPDATE course_watches
                    SET active = 1, notify_on_open = ?, status = 'closed', last_checked = NULL
                    WHERE id = ?
                """, (notify_on_open, watch_id))
                conn.commit()
                flash(f'Successfully re-added watch for {subject} {course_number}!', 'success')
                cursor.close()
                conn.close()
                return redirect(url_for('dashboard'))

        try:
            watch_id = create_course_watch(user_id, course_id, notify_on_open)
            flash(f'Successfully added watch for {subject} {course_number}!', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error adding watch: {str(e)}', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('add_watch'))

    cursor.close()
    conn.close()
    return render_template('add_watch_user.html',
                          watch_count=watch_count,
                          max_watches=MAX_WATCHES_PER_USER)


@app.route('/delete-watch/<int:watch_id>', methods=['POST'])
@login_required
def delete_watch(watch_id):
    """Delete a course watch"""
    user_id = session['user_id']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM course_watches WHERE id = ?', (watch_id,))
    result = cursor.fetchone()

    if not result or result[0] != user_id:
        flash('Unauthorized', 'error')
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    cursor.execute('UPDATE course_watches SET active = 0 WHERE id = ?', (watch_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Watch deleted successfully', 'success')
    return jsonify({'success': True})


@app.route('/status')
def status():
    """Public status page showing system statistics"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    # Get total active watches
    cursor.execute('SELECT COUNT(*) FROM course_watches WHERE active = 1')
    total_watches = cursor.fetchone()[0]

    # Get total courses being monitored
    cursor.execute('SELECT COUNT(DISTINCT course_id) FROM course_watches WHERE active = 1')
    total_courses = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template('status.html',
                          total_users=total_users,
                          total_watches=total_watches,
                          total_courses=total_courses)


@app.route('/api/subjects/search')
def api_subjects_search():
    """API endpoint for subject autocomplete"""
    search = request.args.get('q', '').strip()

    if len(search) < 1:
        return jsonify([])

    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT code, name
        FROM subjects
        WHERE code LIKE ? OR name LIKE ?
        ORDER BY
            CASE
                WHEN code LIKE ? THEN 0
                ELSE 1
            END,
            code
        LIMIT 10
    """, (f'{search}%', f'%{search}%', f'{search}%'))

    subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(subjects)


# =============================================================================
# ADMIN ROUTES
# =============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_index'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/')
@admin_required
def admin_index():
    """Admin dashboard - shows all active watches"""
    watches = get_active_course_watches()
    return render_template('admin_index.html', watches=watches)


@app.route('/admin/add-watch', methods=['GET', 'POST'])
@admin_required
def admin_add_watch():
    """Admin add watch for any user"""
    if request.method == 'POST':
        try:
            email = request.form.get('email').strip()
            phone = request.form.get('phone', '').strip() or None
            subject = request.form.get('subject').strip().upper()
            course_number = request.form.get('course_number').strip().upper()
            term = request.form.get('term').strip()
            notify_on_open = request.form.get('notify_on_open') == 'on'

            if not email or not subject or not course_number or not term:
                flash('All fields except phone are required', 'error')
                return redirect(url_for('admin_add_watch'))

            user_id = get_or_create_user(email, phone)
            course_id = get_or_create_course(subject, course_number, term)
            watch_id = create_course_watch(user_id, course_id, notify_on_open)

            flash(f'Successfully added watch for {subject} {course_number}!', 'success')
            return redirect(url_for('admin_index'))

        except Exception as e:
            flash(f'Error adding watch: {str(e)}', 'error')
            return redirect(url_for('admin_add_watch'))

    return render_template('admin_add_watch.html')


@app.route('/admin/api/watches')
@admin_required
def admin_api_watches():
    """API endpoint for admin watches"""
    watches = get_active_course_watches()
    return jsonify(watches)


@app.route('/admin/api/watch/<int:watch_id>/delete', methods=['POST'])
@admin_required
def admin_delete_watch(watch_id):
    """Admin delete any watch"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE course_watches SET active = 0 WHERE id = ?', (watch_id,))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Watch deleted successfully', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin view all users"""
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.id,
            u.email,
            u.phone,
            COUNT(cw.id) as watch_count,
            u.created_at
        FROM users u
        LEFT JOIN course_watches cw ON u.id = cw.user_id AND cw.active = 1
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)

    users_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_users.html', users=users_list)


@app.route('/admin/subjects')
@admin_required
def admin_subjects():
    """Admin view subjects"""
    conn = get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()

    search = request.args.get('search', '').strip()

    if search:
        cursor.execute("""
            SELECT code, name
            FROM subjects
            WHERE code LIKE ? OR name LIKE ?
            ORDER BY code
            LIMIT 50
        """, (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("""
            SELECT code, name
            FROM subjects
            ORDER BY code
            LIMIT 50
        """)

    subjects_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_subjects.html', subjects=subjects_list, search=search)


@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for search engine crawlers"""
    robots_content = """User-agent: *
Allow: /
Allow: /register
Allow: /login
Allow: /status
Disallow: /admin/
Disallow: /dashboard
Disallow: /add-watch
Disallow: /delete-watch
Disallow: /forgot-password
Disallow: /reset-password

Sitemap: {}/sitemap.xml
""".format(request.url_root.rstrip('/'))

    return robots_content, 200, {'Content-Type': 'text/plain'}


@app.route('/sitemap.xml')
def sitemap_xml():
    """Generate XML sitemap for search engines"""
    from datetime import datetime

    base_url = request.url_root.rstrip('/')
    today = datetime.now().strftime('%Y-%m-%d')

    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/register</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>{base_url}/login</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/status</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>""".format(base_url=base_url, today=today)

    return sitemap_content, 200, {'Content-Type': 'application/xml'}


if __name__ == '__main__':
    print("\nStarting McMaster Seat Tracker...")
    print("   User portal: http://127.0.0.1:5001")
    print("   Admin panel: http://127.0.0.1:5001/admin/login")
    print("   Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
