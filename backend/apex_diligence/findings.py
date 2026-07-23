"""The Finding — the single first-class output object (ADR-0007)."""

from __future__ import annotations

from pydantic import BaseModel

# Fixed category set.
CATEGORIES = (
    "Profitability/Margin",
    "Growth/Trend",
    "Normalisation",
    "Narrative-vs-Data Contradiction",
    "Concentration/Dependency",
    "Data Quality/Verifiability",
    "Seasonality/Cost-structure",
)

MATERIALITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


class Evidence(BaseModel):
    metric_ids: list[str] = []
    values: list[float] = []  # figures cited, for lineage (figure -> source)
    claim_ids: list[str] = []  # narrative claims reconciled


class Finding(BaseModel):
    finding_id: str
    category: str
    entity: str  # AU | NZ | Group
    title: str
    observation: str
    evidence: Evidence
    management_questions: list[str]
    materiality: str  # High | Medium | Low
    dollar_impact: float | None = None


def rank(findings: list[Finding]) -> list[Finding]:
    """Rank by materiality, then by dollar impact within a tier (ADR-0007)."""
    return sorted(
        findings,
        key=lambda f: (MATERIALITY_ORDER.get(f.materiality, 3), -abs(f.dollar_impact or 0)),
    )
