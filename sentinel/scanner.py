"""The scan trigger source.

In a real deployment this reads from GitHub Dependabot alerts
(`GET /repos/{owner}/{repo}/dependabot/alerts`) or a CI security scan. For a
self-contained demo it reads a findings file and files one GitHub issue per
finding, each carrying the trigger label. Filing the issue is itself the event
that drives remediation — closing the loop scan -> issue -> Devin -> PR.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .github_client import GitHubClientProtocol
from .logging_conf import get_logger
from .models import Finding

log = get_logger("sentinel.scanner")

DEFAULT_FINDINGS = Path("data/sample_findings.json")


def load_findings(path: Path | str = DEFAULT_FINDINGS) -> list[Finding]:
    raw = json.loads(Path(path).read_text())
    return [Finding(**item) for item in raw]


def issue_labels(finding: Finding, trigger_label: str) -> list[str]:
    return [
        trigger_label,
        f"severity:{finding.severity}",
        f"category:{finding.category}",
    ]


async def run_scan(
    github: GitHubClientProtocol,
    *,
    trigger_label: str,
    findings_path: Path | str = DEFAULT_FINDINGS,
) -> list[dict[str, Any]]:
    """File an issue for each finding. Returns the created issue payloads, which
    the caller feeds into the orchestrator (mirroring a webhook delivery)."""
    findings = load_findings(findings_path)
    issues: list[dict[str, Any]] = []
    for finding in findings:
        labels = issue_labels(finding, trigger_label)
        issue = await github.create_issue(finding, labels)
        # Normalise label shape to what the orchestrator expects.
        issue["labels"] = [{"name": l} for l in labels]
        issues.append(issue)
    log.info("scan complete", extra={"ctx_findings": len(findings)})
    return issues
