"""
db.py - Database Setup and Helper Functions
This file creates the SQLite database and defines all database operations.
SQLite is built into Python, so no extra installation is needed!
"""

import sqlite3  # Built into Python - no installation needed
import random
import string
from datetime import datetime

# The name of our database file - will be created automatically
DATABASE_NAME = "govbot.db"


def get_connection():
    """
    Opens a connection to the database.
    Think of this like opening a file - you need to open it before reading/writing.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This lets us access columns by name (like a dictionary)
    return conn


def create_tables():
    """
    Creates the database tables if they don't exist yet.
    Run this once when starting the app.
    """
    conn = get_connection()
    cursor = conn.cursor()  # A cursor is like a pen we use to write/read data

    # Create the applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,   -- Auto-numbering ID
            app_id      TEXT UNIQUE NOT NULL,                -- e.g., LIC-AB12CD
            service     TEXT NOT NULL,                       -- license / certificate / complaint
            name        TEXT NOT NULL,
            age         TEXT,
            phone       TEXT,
            email       TEXT,
            address     TEXT,
            details     TEXT,                                -- Extra info depending on service
            status      TEXT DEFAULT 'Pending',              -- Pending / In Review / Approved / Rejected
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)

    # Create the admin table (one default admin account)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Insert a default admin if none exists
    cursor.execute("SELECT COUNT(*) FROM admins")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )
        print("✅ Default admin created: username=admin, password=admin123")

    conn.commit()   # Save changes
    conn.close()    # Close the connection
    print("✅ Database tables created successfully!")


def generate_app_id(service):
    """
    Generates a unique Application ID like LIC-AB12CD.
    service: 'license' → LIC, 'certificate' → CRT, 'complaint' → CMP
    """
    prefixes = {
        "license":     "LIC",
        "certificate": "CRT",
        "complaint":   "CMP"
    }
    prefix = prefixes.get(service, "APP")
    # Random 6-character alphanumeric string
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{random_part}"


def save_application(service, data):
    """
    Saves a new application to the database.
    Returns the generated application ID.
    data: a dictionary with keys like name, age, phone, etc.
    """
    conn = get_connection()
    cursor = conn.cursor()

    app_id = generate_app_id(service)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO applications
            (app_id, service, name, age, phone, email, address, details, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
    """, (
        app_id,
        service,
        data.get("name", ""),
        data.get("age", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("address", ""),
        data.get("details", ""),
        now,
        now
    ))

    conn.commit()
    conn.close()
    return app_id


def get_application(app_id):
    """
    Looks up an application by its ID.
    Returns a dictionary of the application data, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE app_id = ?", (app_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)  # Convert to a regular dictionary
    return None


def get_all_applications():
    """
    Returns ALL applications (used in admin panel).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_status(app_id, new_status):
    """
    Updates the status of an application.
    new_status: 'Pending', 'In Review', 'Approved', or 'Rejected'
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "UPDATE applications SET status = ?, updated_at = ? WHERE app_id = ?",
        (new_status, now, app_id)
    )
    conn.commit()
    conn.close()


def check_admin(username, password):
    """
    Returns True if username/password match an admin record.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM admins WHERE username = ? AND password = ?",
        (username, password)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None
