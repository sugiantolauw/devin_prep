"""Anthropic client wrapper (ADR-0008).

Claude does judgement, never arithmetic. The client is created only when a key is available;
callers fall back to a cached extraction fixture otherwise, so the case study runs offline.
"""

from __future__ import annotations

import os

MODEL = "claude-opus-4-8"


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_client():
    """Return an Anthropic client, or ``None`` if no credentials are configured."""
    if not available():
        return None
    try:
        import anthropic

        return anthropic.Anthropic()
    except Exception:
        return None
