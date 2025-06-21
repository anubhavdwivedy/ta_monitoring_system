import sqlite3
from werkzeug.security import generate_password_hash

schema = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    hours REAL,
    description TEXT,
    approved BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.executescript(schema)

# Create default admin user
email = "admin@ta.com"
password = generate_password_hash("admin123")
try:
    cursor.execute("INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)",
                   ("Admin", email, password, 1))
    print(f"Default admin user created (email: {email}, password: admin123)")
except sqlite3.IntegrityError:
    print("Admin user already exists.")

conn.commit()
conn.close()
print("database.db created successfully.")
