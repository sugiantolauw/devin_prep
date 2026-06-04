"""SQLite persistence for tasks. Thread-safe enough for our single-process
async service: each operation opens a short-lived connection.

We use plain sqlite3 (stdlib) rather than an ORM to keep the moving parts
visible and the dependency surface small.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from .models import Task, TaskStatus, utcnow_iso

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_number      INTEGER NOT NULL,
    issue_title       TEXT NOT NULL,
    repo              TEXT NOT NULL,
    severity          TEXT,
    category          TEXT,
    status            TEXT NOT NULL,
    session_id        TEXT,
    session_url       TEXT,
    pull_request_url  TEXT,
    summary           TEXT,
    devin_status_enum TEXT,
    error             TEXT,
    poll_count        INTEGER DEFAULT 0,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    completed_at      TEXT,
    UNIQUE(repo, issue_number)
);
"""

_COLUMNS = [
    "issue_number", "issue_title", "repo", "severity", "category", "status",
    "session_id", "session_url", "pull_request_url", "summary",
    "devin_status_enum", "error", "poll_count", "created_at", "updated_at",
    "completed_at",
]


class Store:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # -- writes -------------------------------------------------------------
    def upsert_task(self, task: Task) -> Task:
        """Insert a task, or return the existing one for the same issue.

        Idempotency at the storage layer means a webhook delivered twice (GitHub
        does this) never spawns two Devin sessions for the same issue.
        """
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT * FROM tasks WHERE repo = ? AND issue_number = ?",
                (task.repo, task.issue_number),
            ).fetchone()
            if existing:
                return _row_to_task(existing)
            cur = conn.execute(
                f"INSERT INTO tasks ({','.join(_COLUMNS)}) "
                f"VALUES ({','.join(['?'] * len(_COLUMNS))})",
                tuple(_task_values(task)),
            )
            task.id = cur.lastrowid
            return task

    def update_task(self, task: Task) -> None:
        task.updated_at = utcnow_iso()
        with self._conn() as conn:
            conn.execute(
                f"UPDATE tasks SET {', '.join(f'{c} = ?' for c in _COLUMNS)} "
                f"WHERE id = ?",
                (*_task_values(task), task.id),
            )

    # -- reads --------------------------------------------------------------
    def get_by_issue(self, repo: str, issue_number: int) -> Optional[Task]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE repo = ? AND issue_number = ?",
                (repo, issue_number),
            ).fetchone()
            return _row_to_task(row) if row else None

    def list_tasks(self) -> list[Task]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC"
            ).fetchall()
            return [_row_to_task(r) for r in rows]

    def list_active(self) -> list[Task]:
        """Tasks that still need polling (have a session, not yet terminal)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE session_id IS NOT NULL "
                "AND status NOT IN (?, ?)",
                (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value),
            ).fetchall()
            return [_row_to_task(r) for r in rows]


def _task_values(task: Task) -> list:
    return [
        task.issue_number, task.issue_title, task.repo, task.severity,
        task.category, task.status.value, task.session_id, task.session_url,
        task.pull_request_url, task.summary, task.devin_status_enum,
        task.error, task.poll_count, task.created_at, task.updated_at,
        task.completed_at,
    ]


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        issue_number=row["issue_number"],
        issue_title=row["issue_title"],
        repo=row["repo"],
        severity=row["severity"],
        category=row["category"],
        status=TaskStatus(row["status"]),
        session_id=row["session_id"],
        session_url=row["session_url"],
        pull_request_url=row["pull_request_url"],
        summary=row["summary"],
        devin_status_enum=row["devin_status_enum"],
        error=row["error"],
        poll_count=row["poll_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )
