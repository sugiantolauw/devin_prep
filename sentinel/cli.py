"""Command-line driver — run the whole pipeline once without the web server.

    python -m sentinel.cli demo     # scan -> dispatch -> poll to completion -> report
    python -m sentinel.cli report   # print current metrics

Useful for the Loom (deterministic, no ports) and for CI smoke tests.
"""
from __future__ import annotations

import asyncio
import json
import sys

from .config import get_settings
from .devin_client import build_devin_client
from .github_client import build_github_client
from .logging_conf import configure_logging
from .metrics import compute_metrics
from .orchestrator import Orchestrator
from .poller import Tracker
from .scanner import run_scan
from .store import Store


async def _demo() -> None:
    settings = get_settings()
    store = Store(settings.db_path)
    devin = build_devin_client(settings)
    github = build_github_client(settings)
    orchestrator = Orchestrator(
        store, devin, github,
        repo=settings.target_repo,
        trigger_label=settings.trigger_label,
        max_acu_limit=settings.devin_max_acu_limit,
    )
    tracker = Tracker(store, devin, github, interval_seconds=0)

    print(f"▶ scanning {settings.target_repo} (mode={settings.mode})")
    issues = await run_scan(github, trigger_label=settings.trigger_label)
    print(f"  filed {len(issues)} issues")

    for issue in issues:
        task = await orchestrator.handle_issue_event(issue)
        if task:
            print(f"  → issue #{issue['number']} dispatched to {task.session_id}")

    # Drive the tracker to completion (bounded so a hung session can't loop forever).
    for _ in range(50):
        if not store.list_active():
            break
        await tracker.poll_once()
    await devin.aclose()
    await github.aclose()

    print("\n── Metrics ──")
    print(json.dumps(compute_metrics(store), indent=2))


def _report() -> None:
    settings = get_settings()
    store = Store(settings.db_path)
    print(json.dumps(compute_metrics(store), indent=2))


def main() -> None:
    configure_logging()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if cmd == "demo":
        asyncio.run(_demo())
    elif cmd == "report":
        _report()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
