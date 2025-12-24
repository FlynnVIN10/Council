#!/usr/bin/env python3
import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "council_memory.db")

def main():
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

if __name__ == "__main__":
    raise SystemExit(main())
