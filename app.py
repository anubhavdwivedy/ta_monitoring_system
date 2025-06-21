from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from collections import defaultdict
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
    """Convert 'YYYY-Www' to a date range string like 'Week 25 (June 16–22, 2025)'."""
    year, week = week_label.split('-W')
    year = int(year)
    week = int(week)

    # Get the Monday of that ISO week
    monday = datetime.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)

    return f"Week {week} ({monday.strftime('%b %d')}–{sunday.strftime('%d, %Y')})"



@app.route('/', methods=['GET', 'POST'])
def login():
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
        return "Invalid login"
    return render_template("login.html")

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
    
    if request.method == 'POST':
        file = request.files['csvfile']
        if not file.filename.endswith('.csv'):
            return "Please upload a .csv file"

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
        return f"✅ {added} TAs added. ⚠️ Skipped: {', '.join(skipped)}" if skipped else f"✅ {added} TAs added."
    
    return render_template("bulk_add.html")
    
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect('/')
    db = get_db()
    cursor = db.cursor()
    logs = cursor.execute("SELECT * FROM logs WHERE user_id = ?", (session['user_id'],)).fetchall()
    return render_template("dashboard.html", logs=logs)

from datetime import date

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
    raw_data = db.execute("""
        SELECT users.name, strftime('%Y-W%W', date) as week, SUM(hours)
        FROM logs
        JOIN users ON logs.user_id = users.id
        WHERE approved = 1
        GROUP BY users.name, week
        ORDER BY week
    """).fetchall()

    # Format week labels
    summary_data = []
    for row in raw_data:
        name, week_label, total_hours = row
        readable_week = get_week_date_range(week_label)
        summary_data.append((name, readable_week, round(total_hours, 2)))

    return render_template("summary.html", data=summary_data)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
    
@app.route('/initdb')
def initdb():
    import init_db
    return "✅ Database initialized."

# Required for Render deployment
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
