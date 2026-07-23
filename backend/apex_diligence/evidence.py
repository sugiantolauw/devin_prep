"""The Evidence Pack (ADR-0002).

The single structured object the LLM narrates from. It bundles every grounded number — FY
summary, the metric registry, the material anomalies, the normalisation items, and the
EBITDA bridges — plus (from Phase 5) the extracted Board-Paper narrative. The LLM may only
reference numbers present here, and the numeric guardrail validates its output against
``allowed_numbers()``.
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from .anomalies import Anomaly
from .ingest import load_income_statement
from .metrics import MetricRegistry, build_registry, fy_summary
from .normalisation import (
    EBITDABridge,
    NormalisationItem,
    _selected_anomalies,
    build_bridge,
    build_normalisation_items,
)


class FYRow(BaseModel):
    entity: str
    fy: int
    revenue: float
    cogs: float
    gross_profit: float
    opex: float
    ebitda: float
    ebitda_margin_pct: float
    gross_margin_pct: float
    revenue_yoy_pct: float | None
    ebitda_yoy_pct: float | None


class NarrativeClaim(BaseModel):
    """One statement extracted from a Board Paper (populated in Phase 5)."""

    claim_id: str
    source: str  # "FY2023" | "FY2024" | "FY2023-AppendixB"
    topic: str
    text: str
    entity: str | None = None


class NarrativeContext(BaseModel):
    claims: list[NarrativeClaim] = []
    excerpts: dict[str, str] = {}  # source -> raw text (for citation/traceability)


class EvidencePack(BaseModel):
    fy_summary: list[FYRow]
    registry: MetricRegistry
    anomalies: list[Anomaly]
    normalisation_items: list[NormalisationItem]
    bridges: list[EBITDABridge]
    narrative: NarrativeContext | None = None

    def allowed_numbers(self) -> list[float]:
        """Every figure the system will stand behind — the guardrail's ground truth."""
        nums: list[float] = list(self.registry.numbers())
        for r in self.fy_summary:
            nums += [r.revenue, r.cogs, r.gross_profit, r.opex, r.ebitda,
                     r.ebitda_margin_pct, r.gross_margin_pct]
            if r.revenue_yoy_pct is not None:
                nums.append(r.revenue_yoy_pct)
            if r.ebitda_yoy_pct is not None:
                nums.append(r.ebitda_yoy_pct)
        for a in self.anomalies:
            nums += [a.observed, a.baseline, a.deviation, a.score]
        for item in self.normalisation_items:
            nums.append(item.ebitda_impact)
            if item.revenue_impact is not None:
                nums.append(item.revenue_impact)
            nums += list(item.context.values())
        for b in self.bridges:
            nums += [b.reported_ebitda, b.normalised_ebitda]
            nums += [s.delta for s in b.steps] + [s.running for s in b.steps]
        return [float(n) for n in nums]


def build_evidence_pack(
    df: pd.DataFrame | None = None, narrative: NarrativeContext | None = None
) -> EvidencePack:
    df = load_income_statement() if df is None else df

    fy = fy_summary(df)
    rows = [
        FYRow(
            entity=r.entity, fy=int(r.fy), revenue=r.revenue, cogs=r.cogs,
            gross_profit=r.gross_profit, opex=r.opex, ebitda=r.ebitda,
            ebitda_margin_pct=r.ebitda_margin_pct, gross_margin_pct=r.gross_margin_pct,
            revenue_yoy_pct=None if pd.isna(r.revenue_yoy_pct) else r.revenue_yoy_pct,
            ebitda_yoy_pct=None if pd.isna(r.ebitda_yoy_pct) else r.ebitda_yoy_pct,
        )
        for r in fy.itertuples()
    ]

    # Bridges live where the adjustments are (AU, NZ); a Group bridge would misleadingly
    # equal reported since no entity-level item is tagged to Group.
    bridges = [build_bridge(e, 2024, df) for e in ("AU", "NZ")]

    return EvidencePack(
        fy_summary=rows,
        registry=build_registry(df),
        anomalies=_selected_anomalies(df),
        normalisation_items=build_normalisation_items(df),
        bridges=bridges,
        narrative=narrative,
    )
