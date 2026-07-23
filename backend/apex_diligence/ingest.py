"""Load the flat-file income statement into a normalised, validated DataFrame.

Encodes the fixed conventions (ADR-0006):
- calendar year == reported financial year (the brief overrides an AU Jul-Jun instinct);
- amounts are signed (revenue positive, costs negative), so EBITDA is a plain signed sum;
- the hierarchy is ``Income Statement -> EBITDA -> {Gross Profit, Opex} -> category -> line``.

Every downstream metric reads this frame; nothing else parses the CSV.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import INCOME_STATEMENT_CSV
from .domain import ENTITY_SHORT, EXPECTED_LINE_ITEMS, EXPECTED_ROWS

# Source column -> normalised name.
_COLUMN_MAP = {
    "Entity": "entity",
    "Management 1": "statement",
    "Management 2": "ebitda",
    "Management 3": "branch",
    "Management 4": "category",
    "Management 5": "line_item",
    "Date": "date",
    "Amount": "amount",
}


def load_income_statement(path: Path = INCOME_STATEMENT_CSV) -> pd.DataFrame:
    """Return a tidy frame: entity, entity_short, branch, category, line_item, date, fy,
    month, amount.

    Raises ``ValueError`` if the file does not match the expected shape, so a malformed
    input fails loudly rather than silently skewing the numbers.
    """
    raw = pd.read_csv(path)
    missing = set(_COLUMN_MAP) - set(raw.columns)
    if missing:
        raise ValueError(f"income statement is missing columns: {sorted(missing)}")

    df = raw.rename(columns=_COLUMN_MAP)[list(_COLUMN_MAP.values())].copy()

    # Dates are M/D/YY; calendar year is the reported FY.
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%y")
    df["fy"] = df["date"].dt.year.astype(int)
    df["month"] = df["date"].dt.month.astype(int)
    df["amount"] = df["amount"].astype(float)
    df["entity_short"] = df["entity"].map(ENTITY_SHORT)

    if df["entity_short"].isna().any():
        unknown = sorted(df.loc[df["entity_short"].isna(), "entity"].unique())
        raise ValueError(f"unexpected entity value(s): {unknown}")

    _validate(df)
    return df.reset_index(drop=True)


def _validate(df: pd.DataFrame) -> None:
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(df)}")
    if df["line_item"].nunique() != EXPECTED_LINE_ITEMS:
        raise ValueError(
            f"expected {EXPECTED_LINE_ITEMS} line items, got {df['line_item'].nunique()}"
        )
    if (df["statement"] != "Income Statement").any() or (df["ebitda"] != "EBITDA").any():
        raise ValueError("unexpected value in the Income Statement / EBITDA hierarchy levels")
