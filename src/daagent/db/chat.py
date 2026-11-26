"""会话持久化：SQLite chat 表（session_id / role / content / trace）。"""

import json
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
            "session_id TEXT, role TEXT, content TEXT, trace TEXT,"
            "created_at TEXT DEFAULT (datetime('now','localtime')))"
        )
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(chat)").fetchall()]
        if "trace" not in cols:
            self.conn.execute("ALTER TABLE chat ADD COLUMN trace TEXT")
        self.conn.commit()

    def save(self, session_id: str, role: str, content: str, trace=None) -> None:
        self.conn.execute(
            "INSERT INTO chat (session_id, role, content, trace) VALUES (?, ?, ?, ?)",
            (session_id, role, content, json.dumps(trace, ensure_ascii=False) if trace else None),
        )
        self.conn.commit()

    def load(self, session_id: str, limit: int = 50) -> list[tuple[str, str, list | None]]:
        rows = self.conn.execute(
            "SELECT role, content, trace FROM chat WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        out = []
        for role, content, trace in reversed(rows):
            out.append((role, content, json.loads(trace) if trace else None))
        return out

    def list_sessions(self) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT c1.session_id,
                   (SELECT content FROM chat c2 WHERE c2.session_id=c1.session_id AND c2.role='user' ORDER BY c2.id LIMIT 1),
                   COUNT(*)
            FROM chat c1 GROUP BY c1.session_id ORDER BY MIN(c1.id) DESC
            """
        ).fetchall()
        return [{"session_id": r[0], "first_question": r[1], "count": r[2]} for r in rows]
