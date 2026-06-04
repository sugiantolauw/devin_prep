"""GitHub clients for filing issues and posting status comments.

`GitHubClient` uses the REST API; `MockGitHubClient` records calls in memory so
the demo and tests run without a token or network.
"""
from __future__ import annotations

from typing import Any, Optional, Protocol

import httpx

from .logging_conf import get_logger
from .models import Finding

log = get_logger("sentinel.github")


class GitHubClientProtocol(Protocol):
    async def create_issue(self, finding: Finding, labels: list[str]) -> dict: ...
    async def comment(self, issue_number: int, body: str) -> None: ...
    async def aclose(self) -> None: ...


class GitHubClient:
    def __init__(self, token: str, repo: str) -> None:
        if not token:
            raise ValueError("GITHUB_TOKEN is required in live mode")
        self._repo = repo
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    async def create_issue(self, finding: Finding, labels: list[str]) -> dict:
        resp = await self._client.post(
            f"/repos/{self._repo}/issues",
            json={
                "title": finding.title,
                "body": finding.to_issue_body(),
                "labels": labels,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        log.info("filed github issue", extra={"ctx_issue": data.get("number")})
        return data

    async def comment(self, issue_number: int, body: str) -> None:
        resp = await self._client.post(
            f"/repos/{self._repo}/issues/{issue_number}/comments",
            json={"body": body},
        )
        resp.raise_for_status()

    async def aclose(self) -> None:
        await self._client.aclose()


class MockGitHubClient:
    """Records issues/comments in memory and assigns sequential issue numbers."""

    def __init__(self, repo: str) -> None:
        self.repo = repo
        self.issues: dict[int, dict] = {}
        self.comments: list[dict[str, Any]] = []
        self._next_number = 101

    async def create_issue(self, finding: Finding, labels: list[str]) -> dict:
        number = self._next_number
        self._next_number += 1
        issue = {
            "number": number,
            "title": finding.title,
            "body": finding.to_issue_body(),
            "labels": [{"name": l} for l in labels],
            "html_url": f"https://github.com/{self.repo}/issues/{number}",
        }
        self.issues[number] = issue
        log.info("filed mock github issue", extra={"ctx_issue": number})
        return issue

    async def comment(self, issue_number: int, body: str) -> None:
        self.comments.append({"issue": issue_number, "body": body})
        log.info("commented on mock issue", extra={"ctx_issue": issue_number})

    async def aclose(self) -> None:
        return None


def build_github_client(settings) -> GitHubClientProtocol:
    if settings.is_live:
        return GitHubClient(settings.github_token, settings.target_repo)
    return MockGitHubClient(settings.target_repo)
