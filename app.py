from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from collections import defaultdict
import traceback
import os

app = Flask(__name__)
app.secret_key = 'secret123'  # Use environment variable in production

def get_db():
    return sqlite3.connect("database.db")

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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect('/')
    db = get_db()
    cursor = db.cursor()
    logs = cursor.execute("SELECT * FROM logs WHERE user_id = ?", (session['user_id'],)).fetchall()
    return render_template("dashboard.html", logs=logs)

@app.route('/submit', methods=['GET', 'POST'])
def submit_log():
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO logs (user_id, date, hours, description) VALUES (?, ?, ?, ?)",
                   (session['user_id'], request.form['date'], request.form['hours'], request.form['description']))
        db.commit()
        return redirect('/dashboard')
    return render_template("submit_log.html")

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

@app.route('/summary')
def summary():
    if not session.get('is_admin'):
        return redirect('/')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT users.name, date, hours FROM logs JOIN users ON logs.user_id = users.id WHERE approved = 1")
    data = cursor.fetchall()
    summary_data = defaultdict(lambda: defaultdict(float))
    for name, date_str, hours in data:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        week = f"{date.strftime('%Y')}-W{date.isocalendar()[1]}"
        summary_data[name][week] += hours
    result = []
    for name, weeks in summary_data.items():
        for week, total in weeks.items():
            result.append((name, week, round(total, 2)))
    return render_template("summary.html", summary=result)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Required for Render deployment
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
