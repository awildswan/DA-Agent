"""会话持久化：SQLite chat 表（消息 + trace）+ sessions 表（标题/置顶）。"""

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
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS sessions ("
            "session_id TEXT PRIMARY KEY, title TEXT, pinned INTEGER DEFAULT 0,"
            "created_at TEXT DEFAULT (datetime('now','localtime')))"
        )
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(chat)").fetchall()]
        if "trace" not in cols:
            self.conn.execute("ALTER TABLE chat ADD COLUMN trace TEXT")
        # 旧数据迁移：把 chat 里出现过的 session 补进 sessions
        self.conn.execute("INSERT OR IGNORE INTO sessions (session_id) SELECT DISTINCT session_id FROM chat")
        self.conn.commit()

    def save(self, session_id: str, role: str, content: str, trace=None) -> None:
        self.conn.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (session_id,))
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
            SELECT s.session_id, s.title, s.pinned, COUNT(c.id) AS cnt,
                   (SELECT content FROM chat c2 WHERE c2.session_id=s.session_id AND c2.role='user' ORDER BY c2.id LIMIT 1)
            FROM sessions s LEFT JOIN chat c ON c.session_id=s.session_id
            GROUP BY s.session_id
            ORDER BY s.pinned DESC, MIN(c.id) DESC
            """
        ).fetchall()
        return [
            {
                "session_id": r[0],
                "title": r[1],
                "pinned": bool(r[2]),
                "count": r[3],
                "first_question": r[4],
            }
            for r in rows
        ]

    def toggle_pin(self, session_id: str) -> None:
        self.conn.execute("UPDATE sessions SET pinned = 1 - pinned WHERE session_id=?", (session_id,))
        self.conn.commit()

    def rename(self, session_id: str, title: str) -> None:
        self.conn.execute("UPDATE sessions SET title=? WHERE session_id=?", (title, session_id))
        self.conn.commit()

    def delete(self, session_id: str) -> None:
        self.conn.execute("DELETE FROM chat WHERE session_id=?", (session_id,))
        self.conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        self.conn.commit()
