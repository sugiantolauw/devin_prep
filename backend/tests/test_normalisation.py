"""The EBITDA bridge must be correct and must NOT normalise out the sustained reset
(trap #2). AU FY2024 is the headline bridge."""

import pytest

from apex_diligence.metrics import fy_summary
from apex_diligence.normalisation import build_bridge, build_normalisation_items


def test_au_bridge_arithmetic():
    b = build_bridge("AU", 2024)
    reported = fy_summary()
    au = reported[(reported["entity"] == "AU") & (reported["fy"] == 2024)]["ebitda"].iloc[0]
    assert b.reported_ebitda == pytest.approx(au, rel=1e-9)
    # Running total after each step is internally consistent.
    assert b.steps[0].running == pytest.approx(b.reported_ebitda)
    assert b.steps[-1].running == pytest.approx(b.normalised_ebitda)
    # One-off add-back raises EBITDA; promo removal lowers it; net normalised < reported here.
    assert b.normalised_ebitda < b.reported_ebitda
    assert b.normalised_ebitda == pytest.approx(26_072_884, rel=1e-4)


def test_sustained_reset_is_noted_not_adjusted():
    b = build_bridge("AU", 2024)
    # The reset must not appear as an applied bridge step...
    labels = " ".join(s.label for s in b.steps)
    assert "reset" not in labels.lower()
    # ...but must be surfaced as a noted item with zero EBITDA impact.
    resets = [n for n in b.noted_items if n.kind == "sustained_reset"]
    assert len(resets) == 1
    assert resets[0].ebitda_impact == 0.0
    assert resets[0].applied is False


def test_applied_items_are_grounded():
    items = [i for i in build_normalisation_items() if i.entity == "AU"]
    kinds = {i.kind for i in items}
    assert "one_off_addback" in kinds
    assert "non_recurring_revenue" in kinds
    # The promo removal carries an explicit stated assumption (gross-margin proxy).
    promo = next(i for i in items if i.kind == "non_recurring_revenue")
    assert promo.assumption is not None
    assert promo.revenue_impact is not None
