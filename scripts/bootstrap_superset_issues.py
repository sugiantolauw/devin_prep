#!/usr/bin/env python3
"""Part 1 helper: file the remediation issues into your Superset fork.

Reads data/sample_findings.json and opens one labelled GitHub issue per finding
in TARGET_REPO. Run this once after forking apache/superset so you have real
issues for Sentinel to remediate.

    GITHUB_TOKEN=ghp_... TARGET_REPO=your-org/superset \
        python scripts/bootstrap_superset_issues.py

Use --dry-run to preview without creating anything.
"""
from __future__ import annotations

import asyncio
import os
import sys

# Allow running as a loose script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentinel.config import get_settings  # noqa: E402
from sentinel.github_client import GitHubClient  # noqa: E402
from sentinel.scanner import issue_labels, load_findings  # noqa: E402


async def main(dry_run: bool) -> None:
    settings = get_settings()
    findings = load_findings()
    print(f"Filing {len(findings)} issues into {settings.target_repo} "
          f"(label: {settings.trigger_label})")

    if dry_run:
        for f in findings:
            print(f"  [dry-run] #{f.id} [{f.severity}] {f.title} "
                  f"labels={issue_labels(f, settings.trigger_label)}")
        return

    client = GitHubClient(settings.github_token, settings.target_repo)
    try:
        for f in findings:
            issue = await client.create_issue(f, issue_labels(f, settings.trigger_label))
            print(f"  created #{issue['number']}: {issue['html_url']}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main("--dry-run" in sys.argv))
