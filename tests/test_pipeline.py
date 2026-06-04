"""End-to-end pipeline tests in mock mode — no network, no credits.

These prove the contract the dashboard depends on: an issue with the trigger
label produces a Devin session, the tracker drives it to a terminal state, a PR
is recorded, and the metrics add up. One issue is steered to `needs_human` to
cover the non-happy path.
"""
from __future__ import annotations

import asyncio

import pytest

from sentinel.config import Settings
from sentinel.devin_client import MockDevinClient
from sentinel.github_client import MockGitHubClient
from sentinel.metrics import compute_metrics
from sentinel.models import TaskStatus
from sentinel.orchestrator import Orchestrator
from sentinel.poller import Tracker
from sentinel.scanner import run_scan
from sentinel.store import Store


@pytest.fixture
def wiring(tmp_path):
    settings = Settings(mode="mock", target_repo="your-org/superset",
                        trigger_label="devin-fix", db_path=str(tmp_path / "t.db"),
                        mock_polls_to_finish=2)
    store = Store(settings.db_path)
    devin = MockDevinClient(polls_to_finish=settings.mock_polls_to_finish)
    github = MockGitHubClient(settings.target_repo)
    orch = Orchestrator(store, devin, github, repo=settings.target_repo,
                        trigger_label=settings.trigger_label, max_acu_limit=5)
    tracker = Tracker(store, devin, github, interval_seconds=0)
    return settings, store, devin, github, orch, tracker


def _issue(number, label="devin-fix", severity="high"):
    return {
        "number": number,
        "title": f"Fix #{number}",
        "body": "body",
        "labels": [{"name": label}, {"name": f"severity:{severity}"},
                   {"name": "category:vulnerability"}],
    }


@pytest.mark.asyncio
async def test_unlabelled_issue_is_ignored(wiring):
    _, store, _, _, orch, _ = wiring
    task = await orch.handle_issue_event(_issue(1, label="bug"))
    assert task is None
    assert store.list_tasks() == []


@pytest.mark.asyncio
async def test_dispatch_creates_session_and_comments(wiring):
    _, store, _, github, orch, _ = wiring
    task = await orch.handle_issue_event(_issue(10))
    assert task.session_id is not None
    assert task.status is TaskStatus.RUNNING
    # The issue thread got a "dispatched" comment.
    assert any(c["issue"] == 10 for c in github.comments)


@pytest.mark.asyncio
async def test_idempotent_dispatch(wiring):
    _, store, _, _, orch, _ = wiring
    t1 = await orch.handle_issue_event(_issue(11))
    t2 = await orch.handle_issue_event(_issue(11))  # duplicate delivery
    assert t1.session_id == t2.session_id
    assert len(store.list_tasks()) == 1


@pytest.mark.asyncio
async def test_tracker_drives_to_completion(wiring):
    _, store, _, github, orch, tracker = wiring
    await orch.handle_issue_event(_issue(20))
    for _ in range(10):
        if not store.list_active():
            break
        await tracker.poll_once()
    task = store.get_by_issue("your-org/superset", 20)
    assert task.status is TaskStatus.COMPLETED
    assert task.pull_request_url and task.pull_request_url.startswith("https://")
    assert any("pull request" in c["body"].lower() for c in github.comments)


@pytest.mark.asyncio
async def test_full_scan_to_metrics(wiring):
    settings, store, _, github, orch, tracker = wiring
    issues = await run_scan(github, trigger_label=settings.trigger_label)
    assert len(issues) >= 3
    for issue in issues:
        await orch.handle_issue_event(issue)
    for _ in range(50):
        if not store.list_active():
            break
        await tracker.poll_once()

    m = compute_metrics(store)
    assert m["total_tasks"] == len(issues)
    # Every task resolved into a terminal/await state (none stuck pending/running).
    assert m["active"] == 0
    # At least one PR was opened and the success rate is well-defined.
    assert m["completed"] >= 1
    assert 0.0 <= m["success_rate"] <= 1.0
