import sqlite3
from werkzeug.security import generate_password_hash

# Connect to the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Step 1: Execute schema.sql to create tables
with open('schema.sql', 'r') as f:
    cursor.executescript(f.read())

# Step 2: Insert default admin if not already present
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

# Finalize setup
conn.commit()
conn.close()
print("✅ Database initialized successfully.")
