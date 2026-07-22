"""Normalisation engine and the Reported -> Normalised EBITDA bridge (ADR-0006).

Turns detected anomalies into normalisation items with deterministic dollar impact, then
assembles the EBITDA bridge. Two adjustments are *applied*; the sustained salary reset is
*noted but not adjusted out* (trap #2) because it is a genuine run-rate improvement, not a
one-off. Every figure originates here in Python and later passes the guardrail; the LLM only
decides — against the Board narrative — which items are real (the "both sides" rule).
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from .anomalies import (
    Anomaly,
    detect_point_anomalies,
    detect_runrate_shifts,
    detect_transient_revenue_spikes,
)
from .domain import BRANCH_OPEX
from .ingest import load_income_statement
from .metrics import fy_summary

TARGET_FY = 2024


class NormalisationItem(BaseModel):
    item_id: str
    entity: str
    fy: int
    kind: str  # one_off_addback | non_recurring_revenue | sustained_reset
    label: str
    description: str
    anomaly_id: str
    ebitda_impact: float  # signed, applied to the bridge (0.0 for noted-only items)
    applied: bool
    revenue_impact: float | None = None
    assumption: str | None = None
    context: dict[str, float] = {}


class BridgeStep(BaseModel):
    label: str
    delta: float
    running: float
    item_id: str | None = None


class EBITDABridge(BaseModel):
    entity: str
    fy: int
    reported_ebitda: float
    steps: list[BridgeStep]
    normalised_ebitda: float
    noted_items: list[NormalisationItem]


def _line_branch(df: pd.DataFrame) -> dict[str, str]:
    return dict(df.drop_duplicates("line_item")[["line_item", "branch"]].to_records(index=False))


def build_normalisation_items(df: pd.DataFrame | None = None) -> list[NormalisationItem]:
    df = load_income_statement() if df is None else df
    branch = _line_branch(df)
    gm = _gross_margins(df)  # entity -> {fy: gross_margin_fraction}
    items: list[NormalisationItem] = []

    # Promo months (per entity): an extra-cost spike in one of these is promo-period labour,
    # reconciled with the promo — not a separate restructuring one-off.
    promo_periods = {
        (a.entity, a.period) for a in detect_transient_revenue_spikes(df)
    }

    # 1. One-off cost add-back: the largest extra-cost point spike in an Opex line in the
    #    target FY, per entity, excluding promo months (the Sep-2024 AU restructuring).
    points = detect_point_anomalies(df)
    for entity in ("AU", "NZ"):
        cand = [
            a
            for a in points
            if a.entity == entity
            and a.period.startswith(str(TARGET_FY))
            and (entity, a.period) not in promo_periods
            and a.observed < 0
            and a.direction == "down"  # extra cost
            and branch.get(a.series) == BRANCH_OPEX
        ]
        if cand:
            a = max(cand, key=lambda x: abs(x.deviation))
            add_back = abs(a.deviation)
            items.append(
                NormalisationItem(
                    item_id=f"norm.oneoff.{entity}.FY{TARGET_FY}",
                    entity=entity, fy=TARGET_FY, kind="one_off_addback",
                    label=f"One-off restructuring cost ({entity}, {a.period})",
                    description=(
                        f"{a.series} in {a.period} was {a.observed:,.0f} vs a run-rate of "
                        f"{a.baseline:,.0f} — an abnormal one-month cost of {add_back:,.0f}. "
                        "Added back to reveal underlying earnings."
                    ),
                    anomaly_id=a.anomaly_id, ebitda_impact=add_back, applied=True,
                    context={"observed": a.observed, "run_rate": a.baseline},
                )
            )

    # 2. Non-recurring promo revenue: the transient one-month revenue spike, removed at the
    #    entity's gross margin (a stated proxy for incremental margin).
    for a in detect_transient_revenue_spikes(df):
        if not a.period.startswith(str(TARGET_FY)):
            continue
        margin = gm.get(a.entity, {}).get(TARGET_FY, 0.0)
        ebitda_effect = -a.deviation * margin
        items.append(
            NormalisationItem(
                item_id=f"norm.promo.{a.entity}.FY{TARGET_FY}",
                entity=a.entity, fy=TARGET_FY, kind="non_recurring_revenue",
                label=f"Non-recurring promo revenue ({a.entity}, {a.period})",
                description=(
                    f"{a.entity} total revenue in {a.period} was {a.observed:,.0f} vs an "
                    f"adjacent-month baseline of {a.baseline:,.0f} — a non-recurring uplift of "
                    f"{a.deviation:,.0f} that reverted the next month. Removed at the FY gross "
                    f"margin of {margin * 100:.1f}%."
                ),
                anomaly_id=a.anomaly_id, ebitda_impact=ebitda_effect, applied=True,
                revenue_impact=-a.deviation,
                assumption=(
                    "Incremental margin on the promo is proxied by the entity's FY gross "
                    "margin; the true contribution margin may be lower for discounted promo "
                    "volume."
                ),
                context={"uplift_revenue": a.deviation, "gross_margin_pct": margin * 100},
            )
        )

    # 3. Sustained run-rate reset: NOTED, not adjusted (trap #2). A novel cost reduction that
    #    persists to year-end is a genuine improvement, not a one-off.
    for a in detect_runrate_shifts(df):
        if a.period.startswith(str(TARGET_FY)) and a.direction == "up":  # cost decreasing
            annualised = a.deviation * 12
            items.append(
                NormalisationItem(
                    item_id=f"norm.reset.{a.entity}.FY{TARGET_FY}",
                    entity=a.entity, fy=TARGET_FY, kind="sustained_reset",
                    label=f"Sustained salary run-rate reset ({a.entity})",
                    description=(
                        f"{a.series} stepped from {a.baseline:,.0f} to {a.observed:,.0f} per "
                        f"month and held to year-end — an annualised saving of ~{annualised:,.0f}. "
                        "Noted, not normalised out: this is a real run-rate improvement."
                    ),
                    anomaly_id=a.anomaly_id, ebitda_impact=0.0, applied=False,
                    context={"annualised_saving": annualised, "new_run_rate": a.observed},
                )
            )

    return items


def build_bridge(entity: str, fy: int = TARGET_FY, df: pd.DataFrame | None = None) -> EBITDABridge:
    df = load_income_statement() if df is None else df
    fy_rows = fy_summary(df)
    reported = float(
        fy_rows[(fy_rows["entity"] == entity) & (fy_rows["fy"] == fy)]["ebitda"].iloc[0]
    )

    items = [i for i in build_normalisation_items(df) if i.entity == entity and i.fy == fy]
    applied = [i for i in items if i.applied]
    noted = [i for i in items if not i.applied]

    steps = [BridgeStep(label="Reported EBITDA", delta=reported, running=reported)]
    running = reported
    for item in applied:
        running += item.ebitda_impact
        steps.append(
            BridgeStep(label=item.label, delta=item.ebitda_impact, running=running,
                       item_id=item.item_id)
        )

    return EBITDABridge(
        entity=entity, fy=fy, reported_ebitda=reported, steps=steps,
        normalised_ebitda=running, noted_items=noted,
    )


def _gross_margins(df: pd.DataFrame) -> dict[str, dict[int, float]]:
    fy = fy_summary(df)
    out: dict[str, dict[int, float]] = {}
    for row in fy.itertuples():
        out.setdefault(row.entity, {})[int(row.fy)] = row.gross_margin_pct / 100.0
    return out


def _selected_anomalies(df: pd.DataFrame | None = None) -> list[Anomaly]:
    """The material anomalies that drive normalisation — used by the Evidence Pack."""
    df = load_income_statement() if df is None else df
    ids = {i.anomaly_id for i in build_normalisation_items(df)}
    return [a for a in (
        detect_point_anomalies(df)
        + detect_transient_revenue_spikes(df)
        + detect_runrate_shifts(df)
    ) if a.anomaly_id in ids]
