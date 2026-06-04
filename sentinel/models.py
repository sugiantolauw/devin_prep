"""Domain models shared across the pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStatus(str, Enum):
    """Lifecycle of a single remediation task, independent of Devin's own
    granular session states. This is the vocabulary the dashboard speaks."""

    PENDING = "pending"        # event received, session not yet created
    RUNNING = "running"        # Devin session is actively working
    NEEDS_INPUT = "needs_input"  # Devin is blocked waiting on a human
    COMPLETED = "completed"    # Devin produced a PR / finished successfully
    FAILED = "failed"          # session errored, ran out of credits, etc.

    @property
    def is_terminal(self) -> bool:
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED)


@dataclass
class Finding:
    """A single scanner finding that becomes a GitHub issue."""

    id: str
    title: str
    severity: str          # critical | high | medium | low
    category: str          # vulnerability | dependency | code-quality
    body: str
    package: Optional[str] = None
    cve: Optional[str] = None

    def to_issue_body(self) -> str:
        meta = [f"- **Severity:** {self.severity}", f"- **Category:** {self.category}"]
        if self.package:
            meta.append(f"- **Package:** `{self.package}`")
        if self.cve:
            meta.append(f"- **Advisory:** {self.cve}")
        return "\n".join(
            [self.body, "", "### Finding metadata", *meta, "",
             "_Filed automatically by the Sentinel scanner._"]
        )


@dataclass
class Task:
    """One unit of autonomous remediation work, tracked end-to-end."""

    issue_number: int
    issue_title: str
    repo: str
    severity: str = "unknown"
    category: str = "unknown"
    status: TaskStatus = TaskStatus.PENDING
    session_id: Optional[str] = None
    session_url: Optional[str] = None
    pull_request_url: Optional[str] = None
    summary: Optional[str] = None
    devin_status_enum: Optional[str] = None
    error: Optional[str] = None
    poll_count: int = 0
    created_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)
    completed_at: Optional[str] = None
    id: Optional[int] = None  # DB primary key

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d
