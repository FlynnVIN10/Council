import sqlite3
import json
import os
from datetime import datetime

# Support Docker volume persistence via DATA_DIR environment variable
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(DATA_DIR, "council_memory.db")

def init_db():
    """Initialize the SQLite database with sessions and reflections tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  prompt TEXT,
                  final_answer TEXT,
                  reasoning TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reflections
                 (session_id INTEGER,
                  insight TEXT,
                  FOREIGN KEY(session_id) REFERENCES sessions(id))''')
    conn.commit()
    conn.close()

def save_session(prompt, final_answer, reasoning):
    """Save a council session to the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (timestamp, prompt, final_answer, reasoning) VALUES (?, ?, ?, ?)",
              (datetime.now().isoformat(), prompt, final_answer, reasoning))
    session_id = c.lastrowid
    # Example reflection
    c.execute("INSERT INTO reflections (session_id, insight) VALUES (?, ?)",
              (session_id, "Council demonstrated bold deliberation on self-evolution."))
    conn.commit()
    conn.close()
    return session_id

def get_recent_sessions(n=5):
    """Retrieve the most recent N sessions from the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (n,))
    rows = c.fetchall()
    conn.close()
    return rows

# Initialize database on import
init_db()

