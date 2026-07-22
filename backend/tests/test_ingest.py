import pandas as pd

from apex_diligence.domain import BRANCH_GROSS_PROFIT, BRANCH_OPEX, FISCAL_YEARS
from apex_diligence.ingest import load_income_statement


def test_shape_is_rectangular():
    df = load_income_statement()
    assert len(df) == 1728
    assert set(df["entity_short"]) == {"AU", "NZ"}
    assert set(df["fy"]) == set(FISCAL_YEARS)
    assert set(df["month"]) == set(range(1, 13))
    assert df["line_item"].nunique() == 18
    # 2 entities x 4 years x 12 months x 18 line items, no gaps.
    per_cell = df.groupby(["entity_short", "fy", "month"]).size()
    assert (per_cell == 18).all()


def test_conventions():
    df = load_income_statement()
    # Costs are stored negative, sales positive.
    assert df.loc[df["category"] == "Sales", "amount"].min() > 0
    assert df.loc[df["category"] == "Cost of Goods Sold", "amount"].max() < 0
    # Every row rolls up under one of the two EBITDA branches.
    assert set(df["branch"]) == {BRANCH_GROSS_PROFIT, BRANCH_OPEX}
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
