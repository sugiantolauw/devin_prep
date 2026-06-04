"""Builds the remediation prompt and the structured-output contract we hand to
Devin. The prompt is the real product surface here: it turns a terse issue into
a precise, autonomously-executable engineering task.
"""
from __future__ import annotations

from typing import Any

# We ask Devin to return a machine-readable result so the orchestrator never has
# to scrape free text to learn the PR URL or outcome.
STRUCTURED_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {
            "type": "string",
            "enum": ["fixed", "needs_human", "not_reproducible"],
            "description": "Final disposition of the remediation attempt.",
        },
        "pull_request_url": {
            "type": "string",
            "description": "URL of the PR opened with the fix, or empty if none.",
        },
        "summary": {
            "type": "string",
            "description": "One-paragraph summary of what was changed and why.",
        },
        "files_changed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Paths of files modified.",
        },
        "verification": {
            "type": "string",
            "description": "How the fix was validated (tests run, lint, etc.).",
        },
    },
    "required": ["outcome", "summary"],
}


def build_remediation_prompt(
    *,
    repo: str,
    issue_number: int,
    issue_title: str,
    issue_body: str,
    severity: str,
    category: str,
    trigger_label: str,
) -> str:
    """Compose a self-contained instruction for a Devin session.

    Note the explicit guardrails: scope to one issue, open a PR (never push to
    default), run the project's checks, and ask for help rather than guessing on
    anything risky. These are exactly the constraints a senior engineer would put
    on a junior picking up the ticket.
    """
    return f"""\
You are remediating a single tracked issue in the repository `{repo}`.

## Issue #{issue_number}: {issue_title}
Severity: {severity} | Category: {category}

{issue_body}

## Your task
1. Reproduce / confirm the problem described above. If you cannot, set the
   structured output `outcome` to `not_reproducible` and explain why.
2. Implement the smallest correct fix. For dependency or vulnerability findings,
   bump to the nearest non-vulnerable version and adapt any breaking changes.
3. Run the repository's existing checks for the code you touched (unit tests,
   linters, type checks). Do not weaken or delete tests to make them pass.
4. Open a pull request from a new branch named
   `sentinel/issue-{issue_number}` that closes issue #{issue_number}. The PR
   description must explain the root cause, the fix, and how you verified it.

## Guardrails
- Touch only what is needed for THIS issue. No drive-by refactors.
- Never force-push or commit directly to the default branch.
- If the correct fix is ambiguous or risky (e.g. a major version bump with wide
  blast radius), stop and set `outcome` to `needs_human` with your reasoning
  rather than guessing.

When finished, populate the structured output with the PR URL, a summary, the
files you changed, and how you verified the fix.
"""
