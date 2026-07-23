"""Build the NarrativeContext from the Board Papers (ADR-0003, ADR-0005).

Two LLM-backed steps, each with a cached-fixture fallback so the pipeline runs without a key:
1. **Appendix B** — the scanned page is transcribed by Claude vision (or read from cache);
2. **Claim extraction** — the paper texts are turned into structured NarrativeClaims by
   Claude structured output (or read from cache).

The extracted claims are what the reconciliation step (Phase 6) matches numeric anomalies
against — including the FY2023 vs FY2024 leadership contradiction.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from pydantic import BaseModel

from .documents import fy2023_text, fy2024_text, render_pdf_page_png
from .evidence import NarrativeClaim, NarrativeContext
from .llm import MODEL, get_client

_FIXTURES = Path(__file__).parent / "fixtures"


def extract_appendix_b() -> tuple[str, bool]:
    """Return (appendix_text, used_live_vision). Uses Claude vision if a key is present,
    else the cached transcription."""
    client = get_client()
    if client is None:
        return (_FIXTURES / "appendix_b.txt").read_text(), False

    png = render_pdf_page_png()
    b64 = base64.standard_b64encode(png).decode()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            "This is a scanned appendix from a board paper. Transcribe its "
                            "text verbatim, preserving section headings. Return only the "
                            "transcription."
                        ),
                    },
                ],
            }
        ],
    )
    text = next((b.text for b in resp.content if b.type == "text"), "")
    return text, True


class _ClaimList(BaseModel):
    claims: list[NarrativeClaim]


def extract_claims(sources: dict[str, str]) -> tuple[list[NarrativeClaim], bool]:
    """Return (claims, used_live_llm). Structured extraction via Claude if a key is present,
    else the cached claim set."""
    client = get_client()
    if client is None:
        raw = json.loads((_FIXTURES / "narrative_claims.json").read_text())
        return [NarrativeClaim(**c) for c in raw], False

    joined = "\n\n".join(f"=== {src} ===\n{txt}" for src, txt in sources.items())
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract the material factual claims a diligence team would care about "
                    "from these board-paper excerpts: leadership/management changes, "
                    "restructuring, promotions/one-offs, customer concentration, and "
                    "performance/margin statements. For each claim set: claim_id (c1, c2, ...), "
                    "source (one of the '=== ... ===' section labels), topic (short slug), "
                    "entity (AU | NZ | Group | null), and text (a faithful one-sentence "
                    f"paraphrase).\n\n{joined}"
                ),
            }
        ],
        output_format=_ClaimList,
    )
    return resp.parsed_output.claims, True


def build_narrative_context() -> NarrativeContext:
    appendix_text, _ = extract_appendix_b()
    fy2023 = fy2023_text()
    fy2024 = fy2024_text()
    excerpts = {
        "FY2023": fy2023,
        "FY2023-AppendixB": appendix_text,
        "FY2024": fy2024,
    }
    claims, _ = extract_claims(excerpts)
    return NarrativeContext(claims=claims, excerpts=excerpts)
