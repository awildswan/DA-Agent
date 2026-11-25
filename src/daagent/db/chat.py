"""会话持久化：SQLite chat 表（session_id / role / content）。"""

import sqlite3
from pathlib import Path


class ChatStore:
    def __init__(self, db_path: str = "data/chat.db"):
        self.db = Path(db_path)
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db))
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS chat ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "session_id TEXT, role TEXT, content TEXT,"
            "created_at TEXT DEFAULT (datetime('now','localtime')))"
        )
        self.conn.commit()

    def save(self, session_id: str, role: str, content: str) -> None:
        self.conn.execute(
            "INSERT INTO chat (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        self.conn.commit()

    def load(self, session_id: str, limit: int = 50) -> list[tuple[str, str]]:
        rows = self.conn.execute(
            "SELECT role, content FROM chat WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return list(reversed(rows))
