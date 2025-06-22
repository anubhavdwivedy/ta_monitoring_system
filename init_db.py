import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

with open('schema.sql', 'r') as f:
    cursor.executescript(f.read())

cursor.execute("SELECT * FROM users WHERE email = ?", ('admin@ta.com',))
if not cursor.fetchone():
    hashed_pw = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO users (name, email, password, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ('Default Admin', 'admin@ta.com', hashed_pw, 1))
    print("✅ Default admin account created.")
else:
    print("ℹ️ Default admin already exists.")

conn.commit()
conn.close()
print("✅ Database initialized successfully.")
