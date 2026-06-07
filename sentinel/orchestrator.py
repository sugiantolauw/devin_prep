"""The orchestrator turns a qualifying issue event into a managed Devin session.

This is where Devin becomes a *primitive*: an issue arrives, we hand Devin a
precise task, and we own the bookkeeping (idempotency, tracking, status
comments) around its autonomous work.
"""
from __future__ import annotations

from typing import Any

from .devin_client import DevinClientProtocol
from .github_client import GitHubClientProtocol
from .logging_conf import get_logger
from .models import Task, TaskStatus
from .prompts import STRUCTURED_OUTPUT_SCHEMA, build_remediation_prompt
from .store import Store

log = get_logger("sentinel.orchestrator")


class Orchestrator:
    def __init__(
        self,
        store: Store,
        devin: DevinClientProtocol,
        github: GitHubClientProtocol,
        *,
        repo: str,
        trigger_label: str,
        max_acu_limit: int,
    ) -> None:
        self.store = store
        self.devin = devin
        self.github = github
        self.repo = repo
        self.trigger_label = trigger_label
        self.max_acu_limit = max_acu_limit

    def _qualifies(self, labels: list[str]) -> bool:
        return self.trigger_label in labels

    async def handle_issue_event(self, issue: dict[str, Any]) -> Task | None:
        """Entry point for a GitHub `issues` webhook payload (or a simulated one).

        Returns the Task if a session was (or already had been) created, else None
        when the issue doesn't carry the trigger label.
        """
        number = issue["number"]
        title = issue.get("title", "")
        body = issue.get("body", "") or ""
        labels = [
            l["name"] if isinstance(l, dict) else l
            for l in issue.get("labels", [])
        ]
        severity = _label_value(labels, "severity") or _guess_severity(labels)
        category = _label_value(labels, "category") or "vulnerability"

        if not self._qualifies(labels):
            log.info("issue ignored (no trigger label)", extra={
                "ctx_issue": number, "ctx_labels": labels})
            return None

        # Storage-level idempotency: never create two sessions for one issue.
        existing = self.store.get_by_issue(self.repo, number)
        if existing and existing.session_id:
            log.info("issue already has a session", extra={
                "ctx_issue": number, "ctx_session_id": existing.session_id})
            return existing

        task = self.store.upsert_task(Task(
            issue_number=number,
            issue_title=title,
            repo=self.repo,
            severity=severity,
            category=category,
            status=TaskStatus.PENDING,
        ))

        prompt = build_remediation_prompt(
            repo=self.repo,
            issue_number=number,
            issue_title=title,
            issue_body=body,
            severity=severity,
            category=category,
            trigger_label=self.trigger_label,
        )

        try:
            created = await self.devin.create_session(
                prompt,
                title=f"Remediate #{number}: {title}"[:120],
                tags=["sentinel", f"sentinel-issue-{number}",
                      f"severity:{severity}", f"category:{category}"],
                structured_output_schema=STRUCTURED_OUTPUT_SCHEMA,
                max_acu_limit=self.max_acu_limit,
            )
        except Exception as exc:  # noqa: BLE001 - surface any failure as task state
            task.status = TaskStatus.FAILED
            task.error = f"session creation failed: {exc}"
            self.store.update_task(task)
            log.exception("failed to create session", extra={"ctx_issue": number})
            return task

        task.session_id = created.get("session_id")
        task.session_url = created.get("url")
        task.status = TaskStatus.RUNNING
        self.store.update_task(task)

        await self.github.comment(
            number,
            f"🤖 **Sentinel** dispatched an autonomous Devin session to remediate "
            f"this issue.\n\n- Session: {task.session_url}\n- Status: working\n\n"
            f"Sentinel will update this thread when a pull request is ready.",
        )
        log.info("dispatched remediation", extra={
            "ctx_issue": number, "ctx_session_id": task.session_id})
        return task


def _label_value(labels: list[str], prefix: str) -> str | None:
    """Reads `prefix:value` style labels, e.g. `severity:high`."""
    for label in labels:
        if label.startswith(f"{prefix}:"):
            return label.split(":", 1)[1]
    return None


def _guess_severity(labels: list[str]) -> str:
    for level in ("critical", "high", "medium", "low"):
        if level in labels:
            return level
    return "unknown"
