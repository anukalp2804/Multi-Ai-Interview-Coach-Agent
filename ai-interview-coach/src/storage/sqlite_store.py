# sqlite_store.py — FINAL THREAD-SAFE VERSION
import sqlite3
import json
from pathlib import Path

class SQLiteStore:
    def __init__(self, db_path: Path):
        self.db_path = str(db_path)
        self._init_db()

    def _get_conn(self):
        # Create a NEW connection each time (Thread-safe for Streamlit)
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                data TEXT
            )
        """)
        conn.commit()
        conn.close()

    # -----------------------------
    # SAVE SESSION (Thread-safe)
    # -----------------------------
    def save_session(self, session_id: str, user_id: str, session_dict: dict):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO sessions (session_id, user_id, data) VALUES (?, ?, ?)",
            (session_id, user_id, json.dumps(session_dict))
        )
        conn.commit()
        conn.close()

    # -----------------------------
    # LOAD SESSION
    # -----------------------------
    def load_session(self, session_id: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return json.loads(row[0])
