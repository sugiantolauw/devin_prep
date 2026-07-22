"""The accuracy suite: metrics must reproduce the figures verified against the raw data.

These double as regression tests and as executable proof the engine is correct — the whole
selling point of the system (ADR-0002).
"""

import pytest

from apex_diligence.metrics import build_registry, fy_summary

# Verified against the source CSV during design.
EXPECTED = {
    ("AU", 2021): dict(revenue=102_231_868, ebitda=16_096_468, margin=15.7),
    ("AU", 2024): dict(revenue=134_506_640, ebitda=26_480_030, margin=19.7),
    ("NZ", 2021): dict(revenue=33_839_082, ebitda=5_246_622, margin=15.5),
    ("NZ", 2024): dict(revenue=45_078_381, ebitda=4_481_321, margin=9.9),
}


@pytest.fixture(scope="module")
def fy():
    return fy_summary()


@pytest.mark.parametrize(("entity", "year"), list(EXPECTED))
def test_fy_figures(fy, entity, year):
    row = fy[(fy["entity"] == entity) & (fy["fy"] == year)].iloc[0]
    exp = EXPECTED[(entity, year)]
    assert row["revenue"] == pytest.approx(exp["revenue"], rel=1e-6)
    assert row["ebitda"] == pytest.approx(exp["ebitda"], rel=1e-6)
    assert row["ebitda_margin_pct"] == pytest.approx(exp["margin"], abs=0.05)


def test_headline_story(fy):
    """AU margin expands while NZ margin compresses — the core diligence signal."""
    au = fy[fy["entity"] == "AU"].set_index("fy")["ebitda_margin_pct"]
    nz = fy[fy["entity"] == "NZ"].set_index("fy")["ebitda_margin_pct"]
    assert au[2024] > au[2021]  # AU expands
    assert nz[2024] < nz[2021]  # NZ compresses
    assert nz[2024] < 10.0


def test_group_is_sum_of_entities(fy):
    g = fy[(fy["entity"] == "Group") & (fy["fy"] == 2024)].iloc[0]
    au = fy[(fy["entity"] == "AU") & (fy["fy"] == 2024)].iloc[0]
    nz = fy[(fy["entity"] == "NZ") & (fy["fy"] == 2024)].iloc[0]
    assert g["revenue"] == pytest.approx(au["revenue"] + nz["revenue"], rel=1e-9)
    assert g["ebitda"] == pytest.approx(au["ebitda"] + nz["ebitda"], rel=1e-9)


def test_registry_grounds_key_scalars():
    reg = build_registry()
    assert reg.get("revenue.AU.FY2024").value == pytest.approx(134_506_640, rel=1e-6)
    assert reg.get("ebitda_margin_pct.NZ.FY2024").value == pytest.approx(9.9, abs=0.05)
    # A product line and a cost share should be citable too.
    assert reg.get("product_revenue.AU.FY2024.laptops") is not None
    assert any(k.startswith("cost_share.NZ.FY2024") for k in reg.values)
