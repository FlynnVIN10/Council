import sqlite3
import os
import json
import math
import urllib.request
import urllib.error
from datetime import datetime

# Support configurable persistence via environment variables
# COUNCIL_ENABLE_PERSISTENCE: Enable/disable SQLite persistence (default: False for v0.1)
ENABLE_PERSISTENCE = os.getenv("COUNCIL_ENABLE_PERSISTENCE", "false").lower() in {"true", "1", "yes"}
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(DATA_DIR, "council_memory.db")

def init_db():
    """Initialize the SQLite database with sessions and reflections tables (only if persistence enabled)"""
    if not ENABLE_PERSISTENCE:
        return
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
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  timestamp TEXT,
                  role TEXT,
                  content TEXT,
                  FOREIGN KEY(session_id) REFERENCES sessions(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS summaries
                 (session_id INTEGER,
                  timestamp TEXT,
                  summary TEXT,
                  FOREIGN KEY(session_id) REFERENCES sessions(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS facts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER,
                  timestamp TEXT,
                  fact TEXT,
                  FOREIGN KEY(session_id) REFERENCES sessions(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS embeddings
                 (fact_id INTEGER,
                  vector TEXT,
                  FOREIGN KEY(fact_id) REFERENCES facts(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS fact_scores
                 (fact_id INTEGER PRIMARY KEY,
                  confidence REAL,
                  updated_at TEXT,
                  FOREIGN KEY(fact_id) REFERENCES facts(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS preferences
                 (key TEXT PRIMARY KEY,
                  value TEXT,
                  updated_at TEXT)''')
    conn.commit()
    conn.close()

def save_session(prompt, final_answer, reasoning):
    """Save a council session to the database (only if persistence enabled)"""
    if not ENABLE_PERSISTENCE:
        return None
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
    """Retrieve the most recent N sessions from the database (returns empty list if persistence disabled)"""
    if not ENABLE_PERSISTENCE:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (n,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_message(role, content, session_id=None):
    """Persist a conversation message."""
    if not ENABLE_PERSISTENCE:
        return None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (session_id, timestamp, role, content) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now().isoformat(), role, content)
    )
    conn.commit()
    conn.close()

def get_recent_messages(n=6):
    """Retrieve the most recent N messages for context."""
    if not ENABLE_PERSISTENCE:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
        (n,)
    )
    rows = c.fetchall()
    conn.close()
    # Return in chronological order
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def save_summary(session_id, summary):
    """Save a compact summary for a session."""
    if not ENABLE_PERSISTENCE:
        return
    if not session_id or not summary:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO summaries (session_id, timestamp, summary) VALUES (?, ?, ?)",
        (session_id, datetime.now().isoformat(), summary)
    )
    conn.commit()
    conn.close()

def get_latest_summary():
    """Get the latest session summary, if available."""
    if not ENABLE_PERSISTENCE:
        return ""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT summary FROM summaries ORDER BY rowid DESC LIMIT 1"
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def save_facts(session_id, facts):
    """Save extracted facts for a session."""
    if not ENABLE_PERSISTENCE:
        return
    if not session_id or not facts:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for fact in facts:
        cleaned = fact.strip()
        if cleaned:
            c.execute(
                "INSERT INTO facts (session_id, timestamp, fact) VALUES (?, ?, ?)",
                (session_id, datetime.now().isoformat(), cleaned)
            )
            fact_id = c.lastrowid
            embedding = _get_embedding(cleaned)
            if embedding:
                c.execute(
                    "INSERT INTO embeddings (fact_id, vector) VALUES (?, ?)",
                    (fact_id, json.dumps(embedding))
                )
            c.execute(
                "INSERT INTO fact_scores (fact_id, confidence, updated_at) VALUES (?, ?, ?)",
                (fact_id, 0.7, datetime.now().isoformat())
            )
    conn.commit()
    conn.close()

def get_recent_facts(n=20):
    """Retrieve the most recent N facts."""
    if not ENABLE_PERSISTENCE:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT fact FROM facts ORDER BY id DESC LIMIT ?",
        (n,)
    )
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_recent_fact_rows(n=200):
    """Retrieve recent fact rows with ids."""
    if not ENABLE_PERSISTENCE:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, fact FROM facts ORDER BY id DESC LIMIT ?",
        (n,)
    )
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_fact_embeddings(n=200):
    """Retrieve recent fact embeddings with scores."""
    if not ENABLE_PERSISTENCE:
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT f.id, f.fact, e.vector, s.confidence "
        "FROM facts f "
        "JOIN embeddings e ON e.fact_id = f.id "
        "LEFT JOIN fact_scores s ON s.fact_id = f.id "
        "ORDER BY f.id DESC LIMIT ?",
        (n,)
    )
    rows = c.fetchall()
    conn.close()
    result = []
    for fact_id, fact, vec, confidence in rows:
        try:
            result.append((fact_id, fact, json.loads(vec), confidence or 0.7))
        except Exception:
            continue
    return result

def get_relevant_facts(query, limit=5):
    """Retrieve facts by embeddings (optional) or keyword overlap scoring."""
    if not ENABLE_PERSISTENCE:
        return []
    if not query:
        return []
    if _use_embeddings():
        embedding = _get_embedding(query)
        if embedding:
            facts = get_recent_fact_embeddings(200)
            scored = []
            for idx, (fact_id, fact, vec, confidence) in enumerate(facts):
                sim = _cosine_similarity(embedding, vec)
                if sim is None:
                    continue
                recency_boost = 1.0 + (1.0 / (idx + 2))
                score = sim * recency_boost * (confidence or 0.7)
                if score is not None:
                    scored.append((score, fact))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [f for _, f in scored[:limit]]

    terms = {t.lower() for t in query.split() if len(t) > 2}
    if not terms:
        return []
    fact_rows = get_recent_fact_rows(200)
    score_map = _get_fact_scores([row[0] for row in fact_rows])
    scored = []
    for idx, (fact_id, fact) in enumerate(fact_rows):
        words = {w.lower() for w in fact.split() if len(w) > 2}
        score = len(terms & words)
        if score > 0:
            recency_boost = 1.0 + (1.0 / (idx + 2))
            confidence = score_map.get(fact_id, 0.7)
            scored.append((score * recency_boost * confidence, fact))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:limit]]

def set_preference(key, value):
    """Set a persistent preference value."""
    if not ENABLE_PERSISTENCE:
        return
    if not key:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO preferences (key, value, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (key, value, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_preference(key):
    """Get a preference value by key."""
    if not ENABLE_PERSISTENCE:
        return ""
    if not key:
        return ""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM preferences WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def get_all_preferences():
    """Get all preferences as a dict."""
    if not ENABLE_PERSISTENCE:
        return {}
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, value FROM preferences ORDER BY key ASC")
    rows = c.fetchall()
    conn.close()
    return {k: v for k, v in rows}

def prune_messages(retain_days=90):
    """Delete old message rows to keep memory compact."""
    if not ENABLE_PERSISTENCE:
        return
    try:
        cutoff = datetime.now().timestamp() - (retain_days * 86400)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()
    except Exception:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM messages ORDER BY id DESC LIMIT 20")
    keep_ids = {row[0] for row in c.fetchall()}
    if keep_ids:
        placeholders = ",".join("?" for _ in keep_ids)
        c.execute(
            f"DELETE FROM messages WHERE timestamp < ? AND id NOT IN ({placeholders})",
            (cutoff_iso, *keep_ids)
        )
    else:
        c.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff_iso,))
    conn.commit()
    conn.close()

def vacuum_db():
    """Run SQLite VACUUM to reclaim space."""
    if not ENABLE_PERSISTENCE:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("VACUUM")
    conn.commit()
    conn.close()

def _use_embeddings():
    if not ENABLE_PERSISTENCE:
        return False
    return os.getenv("MEMORY_USE_EMBEDDINGS", "0").lower() in {"1", "true", "yes"}

def _get_embedding(text):
    if not text or not _use_embeddings():
        return None
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    payload = json.dumps({"model": model, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("embedding")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None

def _cosine_similarity(a, b):
    if not a or not b or len(a) != len(b):
        return None
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return None
    return dot / (norm_a * norm_b)

def _get_fact_scores(fact_ids):
    if not ENABLE_PERSISTENCE:
        return {}
    if not fact_ids:
        return {}
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    placeholders = ",".join("?" for _ in fact_ids)
    c.execute(
        f"SELECT fact_id, confidence FROM fact_scores WHERE fact_id IN ({placeholders})",
        tuple(fact_ids)
    )
    rows = c.fetchall()
    conn.close()
    return {fact_id: (confidence if confidence is not None else 0.7) for fact_id, confidence in rows}

def build_session_summary(prompt, final_answer, reasoning, max_chars=1200):
    """Create a compact, durable summary for long-term memory."""
    parts = []
    if prompt:
        parts.append(f"Prompt: {prompt.strip()}")
    if final_answer:
        parts.append(f"Answer: {final_answer.strip()}")
    if reasoning:
        parts.append(f"Reasoning: {reasoning.strip()}")
    summary = "\n".join(parts)
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "..."
    return summary

# Initialize database on import (only if persistence enabled)
if ENABLE_PERSISTENCE:
    init_db()
