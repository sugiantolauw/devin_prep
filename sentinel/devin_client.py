"""Clients for the Devin API.

`DevinClient` talks to the real API (https://docs.devin.ai/api-reference).
`MockDevinClient` simulates the full session lifecycle in-process so the entire
pipeline can be demoed and tested with zero credits and no network.

Both expose the same async interface, so the rest of the system never knows
which one it is using.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional, Protocol

import httpx

from .logging_conf import get_logger

log = get_logger("sentinel.devin")

# Devin's granular session states that mean "no longer making progress on its
# own". `blocked`/`finished` are success-ish (Devin is done or waiting for us);
# the suspended reasons are failures we surface to the dashboard.
TERMINAL_STATUS_ENUMS = {"finished", "blocked", "expired", "stopped"}
FAILURE_STATUS_ENUMS = {
    "usage_limit_exceeded", "out_of_credits", "out_of_quota",
    "no_quota_allocation", "payment_declined", "org_usage_limit_exceeded",
    "total_session_limit_exceeded", "error",
}


class DevinSession(dict):
    """Thin dict wrapper with typed accessors for the fields we care about."""

    @property
    def session_id(self) -> Optional[str]:
        return self.get("session_id")

    @property
    def status_enum(self) -> Optional[str]:
        return self.get("status_enum") or self.get("status")

    @property
    def structured_output(self) -> dict[str, Any]:
        return self.get("structured_output") or {}

    @property
    def pull_request_url(self) -> Optional[str]:
        pr = self.get("pull_request")
        if isinstance(pr, dict):
            return pr.get("url")
        # Devin may also surface the PR via structured output.
        return self.structured_output.get("pull_request_url") or None


class DevinClientProtocol(Protocol):
    async def create_session(
        self, prompt: str, *, title: str, tags: list[str],
        structured_output_schema: Optional[dict] = None,
        max_acu_limit: Optional[int] = None,
    ) -> dict: ...

    async def get_session(self, session_id: str) -> DevinSession: ...

    async def aclose(self) -> None: ...


class DevinClient:
    """Real Devin API client."""

    def __init__(self, api_key: str, base_url: str = "https://api.devin.ai/v1") -> None:
        if not api_key:
            raise ValueError("DEVIN_API_KEY is required in live mode")
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def create_session(
        self, prompt: str, *, title: str, tags: list[str],
        structured_output_schema: Optional[dict] = None,
        max_acu_limit: Optional[int] = None,
    ) -> dict:
        body: dict[str, Any] = {
            "prompt": prompt,
            "title": title,
            "tags": tags,
            # Idempotency keeps duplicate webhook deliveries from double-spending.
            "idempotent": True,
        }
        if structured_output_schema is not None:
            body["structured_output_schema"] = structured_output_schema
        if max_acu_limit is not None:
            body["max_acu_limit"] = max_acu_limit

        resp = await self._client.post("/sessions", json=body)
        resp.raise_for_status()
        data = resp.json()
        log.info("created devin session", extra={
            "ctx_session_id": data.get("session_id"),
            "ctx_is_new": data.get("is_new_session"),
        })
        return data

    async def get_session(self, session_id: str) -> DevinSession:
        # Devin's detail endpoint is singular: /v1/session/{id}
        resp = await self._client.get(f"/session/{session_id}")
        resp.raise_for_status()
        return DevinSession(resp.json())

    async def send_message(self, session_id: str, message: str) -> None:
        resp = await self._client.post(
            f"/session/{session_id}/message", json={"message": message}
        )
        resp.raise_for_status()

    async def aclose(self) -> None:
        await self._client.aclose()


class MockDevinClient:
    """In-process simulation of a Devin session lifecycle.

    Each session advances one "step" per poll. After `polls_to_finish` polls it
    reports a finished session with a synthetic PR URL and structured output,
    exactly mirroring the shape the real API returns. One session id (chosen by
    its title hash) is steered into a `needs_human` outcome so the demo shows the
    non-happy path too.
    """

    def __init__(self, polls_to_finish: int = 3) -> None:
        self._polls_to_finish = max(1, polls_to_finish)
        self._sessions: dict[str, dict] = {}
        self._counter = 0

    @staticmethod
    def _needs_human(session_id: str) -> bool:
        """Outcome is a pure function of the session number, so the simulation
        is stable across process restarts (a known session shows the same final
        state whether or not this process created it)."""
        try:
            return int(session_id.split("-")[1]) % 4 == 0
        except (IndexError, ValueError):
            return False

    async def create_session(
        self, prompt: str, *, title: str, tags: list[str],
        structured_output_schema: Optional[dict] = None,
        max_acu_limit: Optional[int] = None,
    ) -> dict:
        await asyncio.sleep(0)  # behave like a coroutine that yields
        self._counter += 1
        session_id = f"mock-{self._counter:04d}"
        self._sessions[session_id] = {"title": title, "polls": 0}
        log.info("created mock devin session", extra={"ctx_session_id": session_id})
        return {
            "session_id": session_id,
            "url": f"https://app.devin.ai/sessions/{session_id}",
            "is_new_session": True,
        }

    async def get_session(self, session_id: str) -> DevinSession:
        await asyncio.sleep(0)
        state = self._sessions.get(session_id)
        if state is None:
            # Session created before this process started (e.g. the DB was
            # populated by an earlier `make demo`/`make serve`). Real Devin
            # sessions live server-side and survive restarts; the simulator
            # reconstructs the same stable terminal state instead of erroring.
            if session_id.startswith("mock-"):
                return self._terminal(session_id)
            return DevinSession({"session_id": session_id, "status": "error",
                                 "status_enum": "error"})
        state["polls"] += 1
        if state["polls"] < self._polls_to_finish:
            return DevinSession({
                "session_id": session_id,
                "status": "running",
                "status_enum": "working",
            })
        return self._terminal(session_id)

    def _terminal(self, session_id: str) -> DevinSession:
        n = int(session_id.split("-")[1])
        if self._needs_human(session_id):
            return DevinSession({
                "session_id": session_id,
                "status": "blocked",
                "status_enum": "blocked",
                "structured_output": {
                    "outcome": "needs_human",
                    "summary": ("Fix requires a major-version dependency bump "
                                "with breaking API changes; escalating for a "
                                "human decision rather than guessing."),
                    "files_changed": [],
                },
            })
        return DevinSession({
            "session_id": session_id,
            "status": "blocked",
            "status_enum": "finished",
            "pull_request": {
                "url": f"https://github.com/your-org/superset/pull/{9000 + n}",
            },
            "structured_output": {
                "outcome": "fixed",
                "pull_request_url":
                    f"https://github.com/your-org/superset/pull/{9000 + n}",
                "summary": "Bumped the pinned dependency to the target version "
                           "within the allowed constraint and adapted the call "
                           "sites affected by the API change.",
                "files_changed": ["requirements/base.txt", "pyproject.toml"],
                "verification": "Ran the touched unit tests and pre-commit hooks; "
                                "all green.",
            },
        })

    async def aclose(self) -> None:
        return None


def build_devin_client(settings) -> DevinClientProtocol:
    if settings.is_live:
        return DevinClient(settings.devin_api_key, settings.devin_base_url)
    return MockDevinClient(polls_to_finish=settings.mock_polls_to_finish)
