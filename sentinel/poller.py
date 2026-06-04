"""Background tracker that keeps task state in sync with Devin sessions.

It polls every active session, maps Devin's granular `status_enum` onto our
Task lifecycle, captures the resulting PR, and posts a closing comment on the
issue. This is what lets a leader watch progress without opening Devin.
"""
from __future__ import annotations

import asyncio

from .devin_client import (
    FAILURE_STATUS_ENUMS,
    TERMINAL_STATUS_ENUMS,
    DevinClientProtocol,
    DevinSession,
)
from .github_client import GitHubClientProtocol
from .logging_conf import get_logger
from .models import Task, TaskStatus, utcnow_iso
from .store import Store

log = get_logger("sentinel.poller")


class Tracker:
    def __init__(
        self,
        store: Store,
        devin: DevinClientProtocol,
        github: GitHubClientProtocol,
        *,
        interval_seconds: int,
    ) -> None:
        self.store = store
        self.devin = devin
        self.github = github
        self.interval = interval_seconds
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    # -- lifecycle ----------------------------------------------------------
    def start(self) -> None:
        if self._task is None:
            self._stopped.clear()
            self._task = asyncio.create_task(self._run(), name="sentinel-tracker")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        log.info("tracker started", extra={"ctx_interval": self.interval})
        while not self._stopped.is_set():
            try:
                await self.poll_once()
            except Exception:  # noqa: BLE001 - never let the loop die
                log.exception("poll cycle failed")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass

    # -- core ---------------------------------------------------------------
    async def poll_once(self) -> int:
        """Poll all active tasks once. Returns how many reached a terminal state.

        Exposed separately so tests (and the CLI) can drive the tracker
        deterministically without the timing loop.
        """
        active = self.store.list_active()
        completed = 0
        for task in active:
            session = await self.devin.get_session(task.session_id)
            if await self._apply(task, session):
                completed += 1
        return completed

    async def _apply(self, task: Task, session: DevinSession) -> bool:
        task.poll_count += 1
        status_enum = (session.status_enum or "").lower()
        task.devin_status_enum = status_enum

        if status_enum in FAILURE_STATUS_ENUMS:
            return await self._finish(task, TaskStatus.FAILED,
                                      error=f"Devin session {status_enum}")

        if status_enum in TERMINAL_STATUS_ENUMS:
            outcome = session.structured_output.get("outcome")
            summary = session.structured_output.get("summary")
            pr_url = session.pull_request_url
            if outcome == "needs_human":
                task.summary = summary
                task.status = TaskStatus.NEEDS_INPUT
                task.updated_at = utcnow_iso()
                self.store.update_task(task)
                await self.github.comment(
                    task.issue_number,
                    f"⚠️ **Sentinel** — Devin paused for human input.\n\n{summary}\n\n"
                    f"Session: {task.session_url}",
                )
                # Not terminal for our accounting: a human may unblock it.
                return False
            if pr_url:
                task.pull_request_url = pr_url
                task.summary = summary
                return await self._finish(task, TaskStatus.COMPLETED)
            # Finished but no PR and not flagged: treat as failure to investigate.
            return await self._finish(
                task, TaskStatus.FAILED,
                error="session finished without a pull request")

        # Still working / waiting — keep it in RUNNING.
        task.status = TaskStatus.RUNNING
        task.updated_at = utcnow_iso()
        self.store.update_task(task)
        return False

    async def _finish(self, task: Task, status: TaskStatus, error: str | None = None) -> bool:
        task.status = status
        task.error = error
        task.completed_at = utcnow_iso()
        task.updated_at = task.completed_at
        self.store.update_task(task)
        if status is TaskStatus.COMPLETED:
            await self.github.comment(
                task.issue_number,
                f"✅ **Sentinel** — Devin opened a pull request.\n\n"
                f"- PR: {task.pull_request_url}\n- {task.summary or ''}\n\n"
                f"Session: {task.session_url}",
            )
        elif status is TaskStatus.FAILED:
            await self.github.comment(
                task.issue_number,
                f"❌ **Sentinel** — remediation did not complete: {error}\n\n"
                f"Session: {task.session_url}",
            )
        log.info("task reached terminal state", extra={
            "ctx_issue": task.issue_number, "ctx_status": status.value})
        return True
