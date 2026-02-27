import sqlite3
import os
from typing import Optional


DB_PATH = "tasks.db"

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT DEFAULT '',
    status      TEXT DEFAULT 'todo',
    priority    TEXT DEFAULT 'Medium',
    tags        TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);
"""

MIGRATION_V2 = """
ALTER TABLE tasks ADD COLUMN due_date TEXT DEFAULT NULL;
"""


class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")

    def migrate(self):
        """Run schema migrations based on version tracking."""
        self.conn.executescript(SCHEMA_V1)

        version = self._get_version()

        if version < 1:
            self._set_version(1)

        if version < 2:
            try:
                self.conn.execute(MIGRATION_V2)
                self.conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
            self._set_version(2)

        self.conn.commit()

    def _get_version(self) -> int:
        row = self.conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0

    def _set_version(self, v: int):
        self.conn.execute("INSERT OR REPLACE INTO schema_version(version) VALUES(?)", (v,))
        self.conn.commit()

    # CRUD 

    def add_task(self, title: str, description: str = "", status: str = "todo",
                 priority: str = "Medium", tags: str = "", due_date: str = None):
        self.conn.execute(
            "INSERT INTO tasks(title, description, status, priority, tags, due_date) VALUES(?,?,?,?,?,?)",
            (title, description, status, priority, tags, due_date)
        )
        self.conn.commit()

    def update_task(self, task_id: int, title: str, description: str,
                    status: str, priority: str, tags: str, due_date: str = None):
        self.conn.execute("""
            UPDATE tasks SET title=?, description=?, status=?, priority=?, tags=?,
            due_date=?, updated_at=datetime('now') WHERE id=?
        """, (title, description, status, priority, tags, due_date, task_id))
        self.conn.commit()

    def update_task_status(self, task_id: int, status: str):
        self.conn.execute(
            "UPDATE tasks SET status=?, updated_at=datetime('now') WHERE id=?",
            (status, task_id)
        )
        self.conn.commit()

    def delete_task(self, task_id: int):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def get_task_by_id(self, task_id: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def get_tasks(self, tag: str = None, priority: str = None, search: str = None) -> list[dict]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if tag:
            query += " AND (',' || tags || ',') LIKE ?"
            params.append(f"%,{tag},%")

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        if search:
            query += " AND (title LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, created_at DESC"

        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_all_tags(self) -> list[str]:
        rows = self.conn.execute("SELECT tags FROM tasks WHERE tags != ''").fetchall()
        tag_set = set()
        for row in rows:
            for tag in row[0].split(","):
                t = tag.strip()
                if t:
                    tag_set.add(t)
        return sorted(tag_set)

    def get_all_tasks(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
