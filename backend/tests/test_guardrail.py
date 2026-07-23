"""Adversarial guardrail tests (ADR-0002). The traps in analytical-traps.md are the
fixtures: a fabricated number is rejected; a correctly-cited number passes; an invented
concentration percentage is rejected."""

from apex_diligence.findings import Evidence, Finding
from apex_diligence.guardrail import check_text, validate_finding

ALLOWED = [134_506_640.0, 45_078_381.0, 9.9, 19.7, 505_390.0, 26_072_884.0]


def _finding(obs: str, questions=None) -> Finding:
    return Finding(
        finding_id="T", category="Profitability/Margin", entity="AU", title="t",
        observation=obs, evidence=Evidence(), management_questions=questions or [],
        materiality="High",
    )


def test_grounded_numbers_pass():
    f = _finding("AU revenue was $134,506,640 and the NZ EBITDA margin was 9.9%.")
    report = validate_finding(f, ALLOWED)
    assert report.passed
    assert len(report.checks) == 2 and all(c.matched for c in report.checks)


def test_fabricated_number_is_rejected():
    f = _finding("NZ revenue fell to $30,000,000 in FY2024.")  # not in the pack
    report = validate_finding(f, ALLOWED)
    assert not report.passed
    assert "$30,000,000" in report.unmatched


def test_invented_concentration_percentage_is_rejected():
    # The concentration figure is not computed from the P&L; asserting it as a number must
    # not pass (trap #4).
    f = _finding("Roughly 33% of NZ revenue runs through a single reseller.")
    report = validate_finding(f, ALLOWED)
    assert not report.passed


def test_years_and_counts_are_ignored():
    # Bare years and small counts are not financial figures — no false rejections (trap #5:
    # "3 GM changes in 2024" must not trip the guardrail).
    checks = check_text("There were 3 GM changes in 2024 and again in 2023.", ALLOWED)
    assert checks == []


def test_rounded_but_correct_number_passes_within_tolerance():
    f = _finding("Normalised EBITDA was about $26.07m.")
    report = validate_finding(f, ALLOWED)
    assert report.passed
