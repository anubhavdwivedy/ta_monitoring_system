from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
from datetime import datetime, timedelta, date
import csv
from io import TextIOWrapper
from datetime import datetime, timedelta
import traceback
import os

app = Flask(__name__)
app.secret_key = 'secret123'  # Use environment variable in production

def get_db():
    return sqlite3.connect("database.db")

def get_week_date_range(week_label):
    """Convert 'YYYY-Www' to readable format."""
    year, week = map(int, week_label.split('-W'))
    monday = datetime.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    return f"Week {week} ({monday.strftime('%b %d')}–{sunday.strftime('%d, %Y')})"

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None 
    
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        email = request.form['email']
        password = request.form['password']
        user = cursor.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['is_admin'] = user[4]
            return redirect('/admin' if user[4] else '/dashboard')
        else:
            error = "Invalid email or password. Please try again."

    return render_template("login.html", error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        # If admin checkbox is ticked, this will be 1; else 0
        is_admin = 1 if 'is_admin' in request.form else 0

        db = get_db()
        try:
            db.execute("INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)",
                       (name, email, password, is_admin))
            db.commit()
            return redirect('/')
        except sqlite3.IntegrityError:
            return "Email already registered!"
    return render_template("register.html")

@app.route('/bulk_add', methods=['GET', 'POST'])
def bulk_add():
    if not session.get('is_admin'):
        return redirect('/')

    message = None

    if request.method == 'POST':
        file = request.files['csvfile']
        if not file or not file.filename.endswith('.csv'):
            message = "❌ Please upload a valid .csv file"
            return render_template("bulk_add.html", message=message)

        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)

        db = get_db()
        added = 0
        skipped = []

        for row in reader:
            name = row['name'].strip()
            email = row['email'].strip()
            password = generate_password_hash(row['password'].strip())

            try:
                db.execute("INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, 0)",
                           (name, email, password))
                added += 1
            except sqlite3.IntegrityError:
                skipped.append(email)

        db.commit()

        message = (
            f"✅ {added} TAs added. ⚠️ Skipped: {', '.join(skipped)}"
            if skipped else
            f"✅ {added} TAs added."
        )

    return render_template("bulk_add.html", message=message)


    
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect('/')
    db = get_db()
    cursor = db.cursor()
    logs = cursor.execute("SELECT * FROM logs WHERE user_id = ?", (session['user_id'],)).fetchall()
    return render_template("dashboard.html", logs=logs)


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        user_id = session['user_id']
        date_str = request.form['date']
        hours = int(request.form['hours'])
        minutes = int(request.form['minutes'])
        description = request.form['description']

        # Convert to float hours
        total_hours = hours + (minutes / 60)

        db = get_db()
        db.execute("INSERT INTO logs (user_id, date, hours, description, approved) VALUES (?, ?, ?, ?, 0)",
                   (user_id, date_str, total_hours, description))
        db.commit()
        return redirect('/dashboard')

    today = date.today().isoformat()
    return render_template("submit_log.html", today=today)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('user_id'):
        return redirect('/')

    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed_pw = generate_password_hash(new_password)
        db = get_db()
        db.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, session['user_id']))
        db.commit()
        return redirect('/dashboard' if not session.get('is_admin') else '/admin')

    return render_template("reset_password.html")


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        message = request.form['message']

        db = get_db()
        db.execute("INSERT INTO reset_requests (email, message) VALUES (?, ?)", (email, message))
        db.commit()

        return render_template('login.html', success="Request submitted. Please wait for admin approval.")

    return render_template('forgot_password.html')


@app.route('/admin-requests')
def admin_requests():
    if not session.get('is_admin'):
        return redirect('/')

    db = get_db()
    db.row_factory = sqlite3.Row  # Enable dict-style access
    requests = db.execute("SELECT * FROM reset_requests").fetchall()
    return render_template("admin_requests.html", requests=requests)


@app.route('/approve-reset/<int:req_id>', methods=['POST'])
def approve_reset(req_id):
    if not session.get('is_admin'):
        return redirect('/')

    new_password = request.form['new_password']
    hashed_pw = generate_password_hash(new_password)

    db = get_db()
    db.row_factory = sqlite3.Row  # Enable dict-style access
    request_data = db.execute("SELECT email FROM reset_requests WHERE id = ?", (req_id,)).fetchone()

    if request_data:
        db.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, request_data['email']))
        db.execute("DELETE FROM reset_requests WHERE id = ?", (req_id,))
        db.commit()

    return redirect('/admin-requests')

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect('/')
    try:
        db = get_db()
        logs = db.execute("""
            SELECT logs.id, users.name, date, hours, description, approved
            FROM logs
            JOIN users ON logs.user_id = users.id
        """).fetchall()
        return render_template("admin.html", logs=logs)
    except Exception as e:
        print("⚠️ Error in /admin route:", e)
        traceback.print_exc()
        return "Internal Server Error"

@app.route('/approve/<int:log_id>')
def approve(log_id):
    if not session.get('is_admin'):
        return redirect('/')
    db = get_db()
    db.execute("UPDATE logs SET approved = 1 WHERE id = ?", (log_id,))
    db.commit()
    return redirect('/admin')

@app.route('/reject/<int:log_id>')
def reject(log_id):
    if not session.get('is_admin'):
        return redirect('/')
    db = get_db()
    db.execute("UPDATE logs SET approved = -1 WHERE id = ?", (log_id,))
    db.commit()
    return redirect('/admin')

@app.route('/summary')
def summary():
    if not session.get('is_admin'):
        return redirect('/')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT users.name, date, hours
        FROM logs
        JOIN users ON logs.user_id = users.id
        WHERE approved = 1
    """)
    data = cursor.fetchall()

    summary_data = defaultdict(lambda: defaultdict(float))
    for name, date_str, hours in data:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        week_key = f"{date.strftime('%Y')}-W{date.isocalendar()[1]}"
        summary_data[name][week_key] += hours

    result = []
    for name in sorted(summary_data):
        for week in sorted(summary_data[name]):
            total = summary_data[name][week]
            readable_week = get_week_date_range(week)
            result.append((name, readable_week, round(total, 2)))

    return render_template("summary.html", summary=result)

@app.route('/manage-users')
def manage_users():
    if not session.get('is_admin'):
        return redirect('/')
    db = get_db()
    users = db.execute("SELECT id, name, email, is_admin FROM users").fetchall()
    return render_template("manage_users.html", users=users)

@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('is_admin'):
        return redirect('/')

    # Prevent admin from deleting themselves
    if user_id == session.get('user_id'):
        return "❌ You cannot delete your own account."

    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return redirect('/manage-users')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
    
# Required for Render deployment
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
