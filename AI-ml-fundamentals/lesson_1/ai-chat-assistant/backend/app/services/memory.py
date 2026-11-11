"""
Memory store for the chat assistant (save as app/services/memory.py).

Three kinds of memory, all stored in one SQLite file:
  1. messages  - every message, saved on the server (survives page refresh)
  2. summaries - a short running summary of older messages
  3. facts     - lasting facts about the user ("Name is Sam", "Learning Python")

`session_id` identifies one person/browser. In a real app with logins,
use the user's id instead.
"""
import os
import sqlite3
from contextlib import contextmanager

from typing import Dict, List, Tuple

DB_PATH = os.getenv("MEMORY_DB_PATH", "memory.db")
MAX_FACTS = 30        # keep at most this many facts per session
MAX_FACT_LENGTH = 200  # characters


class MemoryStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connect(self):
        # A new connection per call is simple and safe across threads.
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id, id);

                CREATE TABLE IF NOT EXISTS summaries (
                    session_id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    last_message_id INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    UNIQUE(session_id, fact)
                );
                """
            )

    # ---------- messages ----------

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )

    def get_messages_after(self, session_id: str, after_id: int) -> List[Dict]:
        """All messages newer than `after_id`, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, role, content FROM messages "
                "WHERE session_id = ? AND id > ? ORDER BY id ASC",
                (session_id, after_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_last_messages(self, session_id: str, n: int) -> List[Dict]:
        """The last `n` messages, oldest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, role, content FROM messages "
                "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, n),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ---------- summaries ----------

    def get_summary(self, session_id: str) -> Tuple[str, int]:
        """Returns (summary_text, id_of_last_message_it_covers)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT summary, last_message_id FROM summaries WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return (row["summary"], row["last_message_id"]) if row else ("", 0)

    def save_summary(self, session_id: str, summary: str, last_message_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO summaries (session_id, summary, last_message_id) "
                "VALUES (?, ?, ?)",
                (session_id, summary, last_message_id),
            )

    # ---------- facts ----------

    def get_facts(self, session_id: str) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT fact FROM facts WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        return [r["fact"] for r in rows]

    def add_facts(self, session_id: str, facts: List[str]) -> None:
        with self._connect() as conn:
            for fact in facts:
                fact = fact.strip()[:MAX_FACT_LENGTH]
                if fact:
                    conn.execute(
                        "INSERT OR IGNORE INTO facts (session_id, fact) VALUES (?, ?)",
                        (session_id, fact),
                    )
            # Keep only the newest MAX_FACTS facts
            conn.execute(
                "DELETE FROM facts WHERE session_id = ? AND id NOT IN ("
                "  SELECT id FROM facts WHERE session_id = ? ORDER BY id DESC LIMIT ?)",
                (session_id, session_id, MAX_FACTS),
            )

    # ---------- forget everything ----------

    def clear(self, session_id: str) -> None:
        with self._connect() as conn:
            for table in ("messages", "summaries", "facts"):
                conn.execute(f"DELETE FROM {table} WHERE session_id = ?", (session_id,))