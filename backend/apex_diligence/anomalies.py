"""Anomaly detection over the income-statement time series (ADR-0003).

Three complementary detectors, each matched to a real signature in the data rather than
hardcoded to a month. They independently surface the events the normalisation engine and the
LLM later reconcile against the Board Papers:

- **point_spike** — a single month that departs from its own robust local trend (catches the
  Sep-2024 restructuring one-off in AU Salaries & Wages);
- **transient_revenue_spike** — a one-month jump in *total* entity revenue that reverts the
  next month (catches the May-2024 promo, which lifts the whole basket, not one product);
- **runrate_shift** — a sustained within-year level change in a cost line that persists to
  year-end (catches the Oct-2024 AU salary reset, which must be *noted, not normalised out*).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import BaseModel

from .domain import CATEGORY_SALES
from .ingest import load_income_statement

_POINT_Z = 3.5
_TRANSIENT_Z = 3.0
_TRANSIENT_REVERT = 0.5  # next-month growth must fall below this fraction of the spike's
_RUNRATE_MIN_SHIFT_PCT = 8.0  # a sustained level change worth noting
_RUNRATE_MIN_TAIL = 3  # months of the shifted level required at year-end


class Anomaly(BaseModel):
    anomaly_id: str
    entity: str
    series: str
    period: str  # "YYYY-MM"
    kind: str  # point_spike | transient_revenue_spike | runrate_shift
    observed: float
    baseline: float
    deviation: float  # observed - baseline (signed)
    score: float
    direction: str  # up | down


def _mad(resid: pd.Series) -> float:
    return max(float(1.4826 * np.median(np.abs(resid - np.median(resid)))), 1.0)


def _ordered(df: pd.DataFrame, mask) -> tuple[pd.Series, pd.Series]:
    s = df[mask].sort_values(["fy", "month"])
    x = s["amount"].reset_index(drop=True)
    period = (s["fy"].astype(str) + "-" + s["month"].map(lambda m: f"{m:02d}")).reset_index(
        drop=True
    )
    return x, period


def detect_point_anomalies(df: pd.DataFrame) -> list[Anomaly]:
    out: list[Anomaly] = []
    for (entity, line), grp in df.groupby(["entity_short", "line_item"]):
        x, period = _ordered(grp, slice(None))
        if len(x) < 12:
            continue
        baseline = x.rolling(7, center=True, min_periods=3).median()
        resid = x - baseline
        scale = _mad(resid.dropna())
        z = resid / scale
        for i in range(len(x)):
            if pd.notna(z[i]) and abs(z[i]) >= _POINT_Z:
                out.append(
                    Anomaly(
                        anomaly_id=f"pt.{entity}.{_key(line)}.{period[i]}",
                        entity=entity, series=line, period=period[i],
                        kind="point_spike", observed=float(x[i]), baseline=float(baseline[i]),
                        deviation=float(resid[i]), score=float(z[i]),
                        direction="up" if resid[i] > 0 else "down",
                    )
                )
    return out


def detect_transient_revenue_spikes(df: pd.DataFrame) -> list[Anomaly]:
    """A one-month jump in total entity revenue that reverts next month — a promo signature."""
    out: list[Anomaly] = []
    sales = df[df["category"] == CATEGORY_SALES]
    for entity, grp in sales.groupby("entity_short"):
        totals = grp.groupby(["fy", "month"])["amount"].sum().reset_index()
        totals = totals.sort_values(["fy", "month"]).reset_index(drop=True)
        x = totals["amount"]
        period = totals["fy"].astype(str) + "-" + totals["month"].map(lambda m: f"{m:02d}")
        g = x.pct_change()
        gd = g.dropna()
        med = float(gd.median())
        scale = max(float(1.4826 * np.median(np.abs(gd - med))), 1e-6)
        z = (g - med) / scale
        for i in range(1, len(x) - 1):
            reverts = g[i + 1] < g[i] * _TRANSIENT_REVERT
            if pd.notna(z[i]) and z[i] >= _TRANSIENT_Z and reverts and g[i] > 0:
                # counterfactual baseline = mean of the two adjacent months
                baseline = float((x[i - 1] + x[i + 1]) / 2)
                out.append(
                    Anomaly(
                        anomaly_id=f"rev.{entity}.total.{period[i]}",
                        entity=entity, series="Total Revenue", period=period[i],
                        kind="transient_revenue_spike", observed=float(x[i]),
                        baseline=baseline, deviation=float(x[i]) - baseline,
                        score=float(z[i]), direction="up",
                    )
                )
    return out


def _best_within_year_shift(x: pd.Series) -> tuple[int, float, float, float] | None:
    """Return (split_k, before_mean, after_mean, shift_pct) for the strongest sustained
    within-year level change that holds to year-end, or None."""
    best = None
    for k in range(4, 10):
        before, after = x[:k].mean(), x[k:].mean()
        if before == 0:
            continue
        shift_pct = abs(after - before) / abs(before) * 100
        tail_stable = (
            len(x) - k >= _RUNRATE_MIN_TAIL and abs(x[k:].std() / (after or 1)) < 0.15
        )
        if shift_pct >= _RUNRATE_MIN_SHIFT_PCT and tail_stable:
            if best is None or shift_pct > best[3]:
                best = (k, float(before), float(after), float(shift_pct))
    return best


def detect_runrate_shifts(df: pd.DataFrame) -> list[Anomaly]:
    """Sustained within-FY level changes in a cost line, keeping only *novel* ones — a shift
    is reported only when it breaks the line's own pattern in other years (opposite sign to,
    or far larger than, the same line's typical year). This strips recurring seasonal Q4
    cost rises and isolates a genuine structural reset (the Oct-2024 AU salary cut)."""
    out: list[Anomaly] = []
    costs = df[df["amount"] < 0]
    for (entity, line), grp in costs.groupby(["entity_short", "line_item"]):
        # best shift per year
        per_year: dict[int, tuple[int, float, float, float]] = {}
        for fy, yr in grp.groupby("fy"):
            x = yr.sort_values("month")["amount"].reset_index(drop=True)
            if len(x) != 12:
                continue
            b = _best_within_year_shift(x)
            if b is not None:
                per_year[int(fy)] = b

        for fy, (k, before, after, shift_pct) in per_year.items():
            signed = after - before
            others = [per_year[y][2] - per_year[y][1] for y in per_year if y != fy]
            if others:
                other_med = float(np.median(others))
                sign_flip = np.sign(signed) != np.sign(other_med) and other_med != 0
                much_larger = abs(signed) > 2.5 * float(np.median(np.abs(others)))
                novel = sign_flip or much_larger
            else:
                novel = True
            if not novel:
                continue
            out.append(
                Anomaly(
                    anomaly_id=f"rr.{entity}.{_key(line)}.FY{fy}",
                    entity=entity, series=line, period=f"{fy}-{k + 1:02d}",
                    kind="runrate_shift", observed=after, baseline=before,
                    deviation=signed, score=shift_pct,
                    direction="up" if after > before else "down",
                )
            )
    return out


def detect_anomalies(df: pd.DataFrame | None = None) -> list[Anomaly]:
    df = load_income_statement() if df is None else df
    return (
        detect_point_anomalies(df)
        + detect_transient_revenue_spikes(df)
        + detect_runrate_shifts(df)
    )


def _key(text: str) -> str:
    return text.lower().replace(" ", "_").replace("&", "and")
