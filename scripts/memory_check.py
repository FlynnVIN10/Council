#!/usr/bin/env python3
import os
import sqlite3
import json
import time
import resource
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "council_memory.db")
PERF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "perf_profile.json")

def _normalize_rss(rss_kb: int) -> int:
    if rss_kb < 100_000_000:
        return int(rss_kb * 1024)
    return int(rss_kb)

def _persistence_enabled() -> bool:
    return os.getenv("COUNCIL_ENABLE_PERSISTENCE", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _memory_check() -> int:
    if not _persistence_enabled():
        print("persistence_disabled: skipping database checks")
        return 0

    if not os.path.exists(DB_PATH):
        print("memory_check: council_memory.db not found")
        return 1

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    tables = ["sessions", "messages", "summaries", "facts", "preferences"]
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
        except sqlite3.OperationalError:
            count = 0
        print(f"{table}: {count}")

    try:
        cur.execute("SELECT summary FROM summaries ORDER BY rowid DESC LIMIT 1")
        row = cur.fetchone()
        summary = row[0] if row else ""
        if summary:
            print("latest_summary:", (summary[:200] + "...") if len(summary) > 200 else summary)
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("SELECT fact FROM facts ORDER BY id DESC LIMIT 5")
        facts = [r[0] for r in cur.fetchall()]
        if facts:
            print("latest_facts:", facts)
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("SELECT key, value FROM preferences ORDER BY key ASC")
        prefs = {k: v for k, v in cur.fetchall()}
        if prefs:
            print("preferences:", json.dumps(prefs, indent=2))
    except sqlite3.OperationalError:
        pass

    conn.close()
    return 0

def _profile_mode(label: str, persistence_enabled: bool) -> dict:
    os.environ["COUNCIL_ENABLE_PERSISTENCE"] = "true" if persistence_enabled else "false"
    start_time = time.time()
    _memory_check()
    wall_time = time.time() - start_time
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "mode": label,
        "persistence_enabled": persistence_enabled,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "wall_time_seconds": round(wall_time, 4),
        "peak_rss_bytes": _normalize_rss(int(rss_kb)),
    }

def main():
    results = [
        _profile_mode("baseline", False),
        _profile_mode("persistence_enabled", True),
    ]

    os.makedirs(os.path.dirname(PERF_PATH), exist_ok=True)
    with open(PERF_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
