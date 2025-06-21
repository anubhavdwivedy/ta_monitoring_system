# 👨‍🏫 TA Work Log Monitoring System

This is a web-based system for managing and monitoring weekly Teaching Assistant (TA) work logs. It allows TAs to submit their work logs, and administrators to approve, reject, and summarize logs to ensure compliance for scholarship eligibility.

---

## 🚀 Features

* 📝 TA login and dashboard
* ⏱ Submit work logs (date, hours, description)
* ✅ Admin approval and rejection of logs
* 📊 Weekly/monthly summary dashboard
* 📾 Bulk TA upload via CSV by admins
* 🔐 Secure login with hashed passwords
* 👤 Add or remove TAs/Admins by admins
* 📁 SQLite backend for lightweight deployment

---

## 🔤 Tech Stack

* **Frontend**: HTML, CSS, Bootstrap
* **Backend**: Flask (Python)
* **Database**: SQLite3
* **Password Hashing**: Werkzeug
* **Deployment**: Render.com or local server

---

## 🗂 Directory Structure

```
ta-monitoring-system/
│
├── app.py                     # Main Flask app
├── init_db.py                 # Initializes the SQLite DB
├── database.db                # (Optional) SQLite DB file
├── requirements.txt
├── render.yaml                # For Render deployment
│
├── templates/                 # HTML templates
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── admin.html
│   ├── summary.html
│   └── ...
│
├── static/
│   └── style.css              # Custom CSS styling
│
└── README.md
```

---

## ⚙️ Setup Instructions

### ✅ Local Deployment

1. **Clone the repo**

   ```bash
   git clone https://github.com/anubhavdwivedy/ta-monitoring-system.git
   cd ta-monitoring-system
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**

   ```bash
   python init_db.py
   ```

5. **Run the server**

   ```bash
   python app.py
   ```

6. **Visit in browser**:
   [http://localhost:5000/](http://localhost:5000/)

---

### ☁️ Deploy to Render

1. Push your project to GitHub.
2. Go to [https://render.com](https://render.com) and create a new Web Service.
3. Set the following:

   * **Start command**: `python app.py`
   * **Environment**: Python 3.13+
   * **Build Command**: `pip install -r requirements.txt`
4. Add Environment Variable:

   ```
   SECRET_KEY = your_secure_secret_key
   ```

---

## 📄 CSV Format for Bulk TA Upload

Use a `.csv` file like:

```
name,email,password
John Doe,john@example.com,password123
Jane Smith,jane@example.com,securepass456
```

---

## 🔐 Security

* Passwords are stored hashed with `werkzeug.security`
* Sessions are secured via `app.secret_key`
* Only admins can approve logs or add/remove users

---

## 👷‍♂️ Admin Tips

* Log in using the **default admin account**: `admin@ta.com` with password `admin123`
* After logging in, **go to the registration page (without logging out)** to create a new admin account
* Then **log in with the new admin account**
* Finally, go to the user management panel to **delete the default admin** for security
* Admin dashboard: `/admin`
* Summary dashboard: `/summary`

---

