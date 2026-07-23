"""Service layer between FastAPI and the engine (ADR-0004).

Deterministic metrics are computed live on every request. The LLM-derived findings are
generated once and cached to disk; a regenerate action re-runs the reconciliation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from apex_diligence.evidence import build_evidence_pack
from apex_diligence.metrics import (
    cost_structure,
    fy_summary,
    monthly_series,
    product_mix,
    seasonality,
)
from apex_diligence.narrative import build_narrative_context
from apex_diligence.normalisation import build_bridge
from apex_diligence.reconcile import ReconciliationResult, reconcile

_CACHE = Path(__file__).resolve().parents[1] / ".cache"
_FINDINGS_CACHE = _CACHE / "findings.json"


def _records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> JSON-safe records (NaN -> None)."""
    return df.replace({np.nan: None}).to_dict(orient="records")


def get_metrics() -> dict:
    return {
        "fy_summary": _records(fy_summary()),
        "monthly": _records(monthly_series()),
        "seasonality": _records(seasonality()),
        "cost_structure": _records(cost_structure()),
        "product_mix": _records(product_mix()),
    }


def get_bridges() -> list[dict]:
    return [build_bridge(e, 2024).model_dump() for e in ("AU", "NZ")]


def get_evidence() -> dict:
    pack = build_evidence_pack()
    return {
        "anomalies": [a.model_dump() for a in pack.anomalies],
        "normalisation_items": [i.model_dump() for i in pack.normalisation_items],
        "registry_size": len(pack.registry.values),
    }


def get_findings(regenerate: bool = False) -> ReconciliationResult:
    if not regenerate and _FINDINGS_CACHE.exists():
        return ReconciliationResult.model_validate_json(_FINDINGS_CACHE.read_text())

    pack = build_evidence_pack(narrative=build_narrative_context())
    result = reconcile(pack)
    _CACHE.mkdir(exist_ok=True)
    _FINDINGS_CACHE.write_text(result.model_dump_json(indent=2))
    return result


def get_findings_payload(regenerate: bool = False) -> dict:
    result = get_findings(regenerate=regenerate)
    return {
        "source": result.source,
        "dropped": result.dropped,
        "findings": [f.model_dump() for f in result.findings],
        "guardrail": {
            "checked": sum(len(r.checks) for r in result.reports),
            "flagged": sum(len(r.unmatched) for r in result.reports),
        },
    }
