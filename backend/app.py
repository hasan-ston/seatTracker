"""
Flask web application for McMaster Seat Tracker
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database.db_helper import (
    get_or_create_user,
    get_or_create_course,
    create_course_watch,
    get_active_course_watches,
    get_connection
)

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


@app.route('/')
@app.route('/admin/')
def index():
    watches = get_active_course_watches()
    return render_template('index.html', watches=watches)


@app.route('/add-watch', methods=['GET', 'POST'])
@app.route('/admin/add-watch', methods=['GET', 'POST'])
def add_watch():
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
                return redirect(url_for('add_watch'))

            user_id = get_or_create_user(email, phone)
            course_id = get_or_create_course(subject, course_number, term)
            watch_id = create_course_watch(user_id, course_id, notify_on_open)

            flash(f'Successfully added watch for {subject} {course_number}!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'Error adding watch: {str(e)}', 'error')
            return redirect(url_for('add_watch'))

    return render_template('add_watch.html')


@app.route('/api/watches')
@app.route('/admin/api/watches')
def api_watches():
    watches = get_active_course_watches()
    return jsonify(watches)


@app.route('/api/watch/<int:watch_id>/delete', methods=['POST'])
@app.route('/admin/api/watch/<int:watch_id>/delete', methods=['POST'])
def delete_watch(watch_id):
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


@app.route('/users')
@app.route('/admin/users')
def users():
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

    return render_template('users.html', users=users_list)


@app.route('/subjects')
@app.route('/admin/subjects')
def subjects():
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

    return render_template('subjects.html', subjects=subjects_list, search=search)


if __name__ == '__main__':
    print("\nStarting McMaster Seat Tracker Web Interface...")
    print("   Open your browser to: http://127.0.0.1:5000")
    print("   Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
