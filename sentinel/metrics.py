"""Analytics over the task store. Answers the leader's question directly:
"How do I know this is working?" — success rate, throughput, and mean time to
remediation (MTTR), plus a live breakdown by status and severity.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .models import Task, TaskStatus
from .store import Store


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def compute_metrics(store: Store) -> dict[str, Any]:
    tasks = store.list_tasks()
    total = len(tasks)

    by_status: dict[str, int] = {s.value: 0 for s in TaskStatus}
    by_severity: dict[str, int] = {}
    durations: list[float] = []
    now = datetime.now(timezone.utc)
    completed_last_hour = 0

    for t in tasks:
        by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
        by_severity[t.severity] = by_severity.get(t.severity, 0) + 1
        if t.status is TaskStatus.COMPLETED:
            start, end = _parse(t.created_at), _parse(t.completed_at)
            if start and end:
                durations.append((end - start).total_seconds())
                if end >= now - timedelta(hours=1):
                    completed_last_hour += 1

    completed = by_status.get(TaskStatus.COMPLETED.value, 0)
    failed = by_status.get(TaskStatus.FAILED.value, 0)
    resolved = completed + failed
    success_rate = (completed / resolved) if resolved else 0.0
    mttr = (sum(durations) / len(durations)) if durations else 0.0

    return {
        "total_tasks": total,
        "active": by_status.get(TaskStatus.RUNNING.value, 0)
        + by_status.get(TaskStatus.PENDING.value, 0),
        "completed": completed,
        "failed": failed,
        "needs_input": by_status.get(TaskStatus.NEEDS_INPUT.value, 0),
        "success_rate": round(success_rate, 3),
        "mttr_seconds": round(mttr, 1),
        "completed_last_hour": completed_last_hour,
        "by_status": by_status,
        "by_severity": by_severity,
        "generated_at": now.isoformat(),
    }


def task_rows(store: Store) -> list[dict[str, Any]]:
    """Flattened task view for the dashboard table."""
    return [_row(t) for t in store.list_tasks()]


def _row(t: Task) -> dict[str, Any]:
    return {
        "issue_number": t.issue_number,
        "issue_title": t.issue_title,
        "severity": t.severity,
        "category": t.category,
        "status": t.status.value,
        "session_url": t.session_url,
        "pull_request_url": t.pull_request_url,
        "summary": t.summary,
        "poll_count": t.poll_count,
        "created_at": t.created_at,
        "completed_at": t.completed_at,
    }
