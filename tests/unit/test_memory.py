import importlib
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.fixture
def memory_module(tmp_path, monkeypatch):
    monkeypatch.setenv("COUNCIL_ENABLE_PERSISTENCE", "true")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    import src.memory as memory
    memory = importlib.reload(memory)
    memory.init_db()
    return memory


def _table_names(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name ASC")
        return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


def test_init_db_creates_tables(memory_module):
    tables = _table_names(memory_module.DB_PATH)
    assert {
        "sessions",
        "reflections",
        "messages",
        "summaries",
        "facts",
        "embeddings",
        "fact_scores",
        "preferences",
    }.issubset(tables)


def test_session_crud(memory_module):
    session_id = memory_module.save_session("prompt", "answer", "reasoning")
    assert session_id is not None
    rows = memory_module.get_recent_sessions(1)
    assert len(rows) == 1
    row = rows[0]
    assert row[0] == session_id
    assert row[2] == "prompt"
    assert row[3] == "answer"
    assert row[4] == "reasoning"


def test_message_persistence(memory_module):
    memory_module.add_message("user", "hello")
    memory_module.add_message("assistant", "hi there")
    messages = memory_module.get_recent_messages(2)
    assert messages == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]


def test_fact_storage_and_embeddings(memory_module, monkeypatch):
    monkeypatch.setattr(memory_module, "_get_embedding", lambda text: [0.1, 0.2])
    session_id = memory_module.save_session("p", "a", "r")
    memory_module.save_facts(session_id, [" fact one ", "", "fact two"])

    conn = sqlite3.connect(memory_module.DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM facts")
        assert cur.fetchone()[0] == 2
        cur.execute("SELECT COUNT(*) FROM embeddings")
        assert cur.fetchone()[0] == 2
        cur.execute("SELECT COUNT(*) FROM fact_scores")
        assert cur.fetchone()[0] == 2
    finally:
        conn.close()

    facts = memory_module.get_recent_facts(10)
    assert set(facts) == {"fact one", "fact two"}


def test_summary_generation_and_storage(memory_module):
    summary = memory_module.build_session_summary(
        "prompt text",
        "answer text",
        "reasoning text",
        max_chars=20,
    )
    assert summary.endswith("...")
    session_id = memory_module.save_session("p", "a", "r")
    memory_module.save_summary(session_id, "short summary")
    assert memory_module.get_latest_summary() == "short summary"


def test_preference_management(memory_module):
    memory_module.set_preference("tone", "bold")
    assert memory_module.get_preference("tone") == "bold"
    memory_module.set_preference("tone", "precise")
    assert memory_module.get_preference("tone") == "precise"
    prefs = memory_module.get_all_preferences()
    assert prefs["tone"] == "precise"


def test_prune_messages(memory_module):
    conn = sqlite3.connect(memory_module.DB_PATH)
    try:
        cur = conn.cursor()
        for i in range(25):
            cur.execute(
                "INSERT INTO messages (session_id, timestamp, role, content) VALUES (?, ?, ?, ?)",
                (None, "2000-01-01T00:00:00", "user", f"old {i}"),
            )
        cur.execute(
            "INSERT INTO messages (session_id, timestamp, role, content) VALUES (?, ?, ?, ?)",
            (None, "2099-01-01T00:00:00", "assistant", "recent"),
        )
        conn.commit()
    finally:
        conn.close()

    memory_module.prune_messages(retain_days=1)

    conn = sqlite3.connect(memory_module.DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM messages")
        assert cur.fetchone()[0] == 20
    finally:
        conn.close()


def test_missing_db_reinitialization(memory_module):
    memory_module.init_db()
    os_db_path = memory_module.DB_PATH
    import os
    os.remove(os_db_path)
    memory_module.init_db()
    assert memory_module.get_recent_sessions(1) == []
    tables = _table_names(os_db_path)
    assert "sessions" in tables


def test_concurrent_access(memory_module):
    def worker(i):
        for _ in range(3):
            try:
                memory_module.add_message("user", f"msg {i}")
                return
            except sqlite3.OperationalError:
                time.sleep(0.01)
        raise

    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(worker, range(10)))

    conn = sqlite3.connect(memory_module.DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM messages")
        assert cur.fetchone()[0] >= 10
    finally:
        conn.close()
