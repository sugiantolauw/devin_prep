"""Deterministic metric engine (ADR-0002, ADR-0006).

Python computes *every* figure the system will ever show. Each scalar is registered with a
stable ``metric_id`` so Findings can cite it and the numeric guardrail can validate against
it. The LLM never does arithmetic; it only references ids that exist here.

Two shapes of output:
- tabular views (``fy_summary``, ``monthly_series``, ``seasonality``, ``cost_structure``,
  ``product_mix``) that the API/UI render as charts and tables;
- a flat :class:`MetricRegistry` of scalars that grounds the LLM and the guardrail.
"""

from __future__ import annotations

import re

import pandas as pd
from pydantic import BaseModel

from .domain import BRANCH_OPEX, CATEGORY_COGS, CATEGORY_SALES
from .ingest import load_income_statement

GROUP = "Group"


class MetricValue(BaseModel):
    """One grounded scalar the system will stand behind."""

    metric_id: str
    label: str
    entity: str  # "AU" | "NZ" | "Group"
    period: str  # "FY2024" | "2024-05"
    value: float
    unit: str  # "AUD" | "%" | "ratio"


class MetricRegistry(BaseModel):
    """All grounded scalars, keyed by ``metric_id``."""

    values: dict[str, MetricValue]

    def get(self, metric_id: str) -> MetricValue | None:
        return self.values.get(metric_id)

    def numbers(self) -> list[float]:
        return [v.value for v in self.values.values()]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# --------------------------------------------------------------------------- views


def fy_summary(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per (entity, FY): revenue, cogs, gross_profit, opex, ebitda, margins, YoY growth.

    Includes a synthetic ``Group`` entity (AU + NZ) for group-level views.
    """
    df = load_income_statement() if df is None else df

    def _agg(frame: pd.DataFrame) -> pd.DataFrame:
        g = frame.groupby("fy")
        revenue = g.apply(lambda x: x.loc[x["category"] == CATEGORY_SALES, "amount"].sum())
        cogs = g.apply(lambda x: x.loc[x["category"] == CATEGORY_COGS, "amount"].sum())
        opex = g.apply(lambda x: x.loc[x["branch"] == BRANCH_OPEX, "amount"].sum())
        ebitda = g["amount"].sum()
        out = pd.DataFrame(
            {
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": revenue + cogs,  # cogs is negative
                "opex": opex,
                "ebitda": ebitda,
            }
        )
        out["ebitda_margin_pct"] = out["ebitda"] / out["revenue"] * 100
        out["gross_margin_pct"] = out["gross_profit"] / out["revenue"] * 100
        out["revenue_yoy_pct"] = out["revenue"].pct_change() * 100
        out["ebitda_yoy_pct"] = out["ebitda"].pct_change() * 100
        return out

    frames = []
    for entity, sub in df.groupby("entity_short"):
        f = _agg(sub)
        f.insert(0, "entity", entity)
        frames.append(f)
    grp = _agg(df)
    grp.insert(0, "entity", GROUP)
    frames.append(grp)

    return pd.concat(frames).reset_index().rename(columns={"index": "fy"})


def monthly_series(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per (entity, fy, month): revenue, opex, ebitda — the monthly trend series."""
    df = load_income_statement() if df is None else df

    def _agg(frame: pd.DataFrame) -> pd.DataFrame:
        g = frame.groupby(["fy", "month"])
        revenue = g.apply(lambda x: x.loc[x["category"] == CATEGORY_SALES, "amount"].sum())
        opex = g.apply(lambda x: x.loc[x["branch"] == BRANCH_OPEX, "amount"].sum())
        ebitda = g["amount"].sum()
        return pd.DataFrame({"revenue": revenue, "opex": opex, "ebitda": ebitda})

    frames = []
    for entity, sub in df.groupby("entity_short"):
        f = _agg(sub)
        f.insert(0, "entity", entity)
        frames.append(f)
    grp = _agg(df)
    grp.insert(0, "entity", GROUP)
    frames.append(grp)

    out = pd.concat(frames).reset_index()
    out["period"] = out["fy"].astype(str) + "-" + out["month"].map(lambda m: f"{m:02d}")
    return out


def seasonality(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per (entity, month): a revenue seasonal index = mean across years of the month's
    revenue divided by that year's mean monthly revenue. 1.0 == an average month."""
    df = load_income_statement() if df is None else df
    m = monthly_series(df)
    m = m[m["entity"] != GROUP].copy()
    m["year_mean"] = m.groupby(["entity", "fy"])["revenue"].transform("mean")
    m["index"] = m["revenue"] / m["year_mean"]
    return (
        m.groupby(["entity", "month"])["index"]
        .mean()
        .reset_index()
        .rename(columns={"index": "seasonal_index"})
    )


def cost_structure(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per (entity, fy): each cost line's share of total cost (COGS lines + Opex
    categories), as a positive percentage."""
    df = load_income_statement() if df is None else df
    costs = df[df["amount"] < 0].copy()
    # COGS is broken out by line item; Opex by category.
    costs["cost_name"] = costs.apply(
        lambda r: r["line_item"] if r["category"] == CATEGORY_COGS else r["category"], axis=1
    )
    grouped = (
        costs.groupby(["entity_short", "fy", "cost_name"])["amount"].sum().abs().reset_index()
    )
    grouped["total"] = grouped.groupby(["entity_short", "fy"])["amount"].transform("sum")
    grouped["share_pct"] = grouped["amount"] / grouped["total"] * 100
    return grouped.rename(columns={"entity_short": "entity", "amount": "cost"})


def product_mix(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per (entity, fy, product line): revenue and share of the entity's revenue."""
    df = load_income_statement() if df is None else df
    sales = df[df["category"] == CATEGORY_SALES].copy()
    grouped = (
        sales.groupby(["entity_short", "fy", "line_item"])["amount"].sum().reset_index()
    )
    grouped["total"] = grouped.groupby(["entity_short", "fy"])["amount"].transform("sum")
    grouped["share_pct"] = grouped["amount"] / grouped["total"] * 100
    return grouped.rename(
        columns={"entity_short": "entity", "line_item": "product", "amount": "revenue"}
    )


# --------------------------------------------------------------------------- registry

_FY_METRICS = {
    "revenue": ("Revenue", "AUD"),
    "cogs": ("Cost of Goods Sold", "AUD"),
    "gross_profit": ("Gross Profit", "AUD"),
    "opex": ("Operating Expenses", "AUD"),
    "ebitda": ("EBITDA", "AUD"),
    "ebitda_margin_pct": ("EBITDA Margin", "%"),
    "gross_margin_pct": ("Gross Margin", "%"),
    "revenue_yoy_pct": ("Revenue YoY Growth", "%"),
    "ebitda_yoy_pct": ("EBITDA YoY Growth", "%"),
}


def build_registry(df: pd.DataFrame | None = None) -> MetricRegistry:
    """Flatten every grounded scalar into a metric_id -> MetricValue map."""
    df = load_income_statement() if df is None else df
    values: dict[str, MetricValue] = {}

    def add(metric_id: str, label: str, entity: str, period: str, value: float, unit: str):
        if pd.isna(value):
            return
        values[metric_id] = MetricValue(
            metric_id=metric_id,
            label=label,
            entity=entity,
            period=period,
            value=float(value),
            unit=unit,
        )

    # FY-level, per entity and Group.
    fy = fy_summary(df)
    for row in fy.itertuples():
        period = f"FY{row.fy}"
        for col, (label, unit) in _FY_METRICS.items():
            add(f"{col}.{row.entity}.{period}", f"{label} ({row.entity}, {period})",
                row.entity, period, getattr(row, col), unit)

    # Monthly revenue / opex / ebitda, per entity and Group.
    mo = monthly_series(df)
    for row in mo.itertuples():
        for col, (label, unit) in {
            "revenue": ("Monthly Revenue", "AUD"),
            "opex": ("Monthly Opex", "AUD"),
            "ebitda": ("Monthly EBITDA", "AUD"),
        }.items():
            add(f"{col}_monthly.{row.entity}.{row.period}",
                f"{label} ({row.entity}, {row.period})", row.entity, row.period,
                getattr(row, col), unit)

    # Product revenue, per entity.
    pm = product_mix(df)
    for row in pm.itertuples():
        period = f"FY{row.fy}"
        add(f"product_revenue.{row.entity}.{period}.{_slug(row.product)}",
            f"{row.product} Revenue ({row.entity}, {period})", row.entity, period,
            row.revenue, "AUD")
        add(f"product_share.{row.entity}.{period}.{_slug(row.product)}",
            f"{row.product} Revenue Share ({row.entity}, {period})", row.entity, period,
            row.share_pct, "%")

    # Cost-structure shares, per entity.
    cs = cost_structure(df)
    for row in cs.itertuples():
        period = f"FY{row.fy}"
        add(f"cost_share.{row.entity}.{period}.{_slug(row.cost_name)}",
            f"{row.cost_name} Cost Share ({row.entity}, {period})", row.entity, period,
            row.share_pct, "%")

    return MetricRegistry(values=values)
