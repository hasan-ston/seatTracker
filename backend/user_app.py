"""
User-facing Flask web application for McMaster Seat Tracker
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database.db_helper import (
    get_or_create_course,
    create_course_watch,
    get_connection
)

app = Flask(__name__,
            template_folder='../frontend/user_templates',
            static_folder='../frontend/static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

MAX_WATCHES_PER_USER = 3


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue', 'error')
            return redirect(url_for('login'))
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


if __name__ == '__main__':
    print("\nStarting McMaster Seat Tracker - User Portal...")
    print("   Open your browser to: http://127.0.0.1:5001")
    print("   Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
