"""The detector must surface the real events from the series itself (ADR-0003) — proving
the discovery is genuine, not hardcoded."""

from apex_diligence.anomalies import (
    detect_point_anomalies,
    detect_runrate_shifts,
    detect_transient_revenue_spikes,
)
from apex_diligence.ingest import load_income_statement

DF = load_income_statement()


def test_sep_2024_au_salary_one_off_is_flagged():
    spikes = [
        a
        for a in detect_point_anomalies(DF)
        if a.entity == "AU" and a.series == "Salaries & Wages" and a.period == "2024-09"
    ]
    assert spikes, "the Sep-2024 AU restructuring one-off was not detected"
    a = spikes[0]
    assert a.direction == "down"  # extra cost
    assert abs(a.deviation) > 400_000  # a material one-off


def test_may_2024_promo_is_a_transient_total_revenue_spike():
    spikes = {a.entity: a for a in detect_transient_revenue_spikes(DF)}
    assert "AU" in spikes and spikes["AU"].period == "2024-05"
    assert spikes["AU"].deviation > 2_000_000  # whole-basket uplift, not one product
    # Stronger in AU than NZ, matching the narrative.
    assert spikes["AU"].deviation > spikes["NZ"].deviation


def test_runrate_novelty_isolates_the_salary_reset():
    shifts = detect_runrate_shifts(DF)
    # The novelty filter strips recurring seasonal Q4 cost rises, leaving the one genuine
    # structural reset: AU salaries stepping DOWN in cost late in 2024.
    assert len(shifts) == 1
    a = shifts[0]
    assert a.entity == "AU"
    assert a.series == "Salaries & Wages"
    assert a.direction == "up"  # cost decreasing
    assert a.period.startswith("2024")
