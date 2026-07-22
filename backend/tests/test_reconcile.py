"""Reconciliation (ADR-0003/0007): the offline reference findings, and the guardrail applied
over a mocked LLM response (ADR-0010 — the LLM's contract is testable even though its
judgement is not)."""

import apex_diligence.reconcile as R
from apex_diligence.evidence import build_evidence_pack
from apex_diligence.findings import Evidence, Finding
from apex_diligence.narrative import build_narrative_context


def test_offline_reconciliation_headline_findings():
    result = R.reconcile()
    assert result.source == "offline"
    assert result.dropped == 0  # every grounded figure passes the guardrail
    ids = {f.finding_id for f in result.findings}
    assert {"F-NZ-MARGIN", "F-LEADERSHIP", "F-AU-NORMALISATION", "F-CONCENTRATION"} <= ids
    # Ranked: the first finding is High materiality.
    assert result.findings[0].materiality == "High"


def test_contradiction_and_concentration_assert_no_numbers():
    result = R.reconcile()
    for fid in ("F-LEADERSHIP", "F-CONCENTRATION"):
        report = next(r for r in result.reports if r.finding_id == fid)
        assert report.checks == []  # judgement findings, correctly free of fabricated figures


def test_guardrail_drops_a_hallucinated_llm_finding(monkeypatch):
    pack = build_evidence_pack(narrative=build_narrative_context())

    good = Finding(
        finding_id="LLM-GOOD", category="Profitability/Margin", entity="NZ",
        title="grounded", observation="NZ FY2024 EBITDA margin was 9.9%.",
        evidence=Evidence(), management_questions=[], materiality="High",
    )
    hallucinated = Finding(
        finding_id="LLM-BAD", category="Concentration/Dependency", entity="NZ",
        title="invented", observation="Security Tech Inc. is 41.3% of NZ revenue.",
        evidence=Evidence(), management_questions=[], materiality="High",
    )
    monkeypatch.setattr(R, "_reconcile_live", lambda _pack: [good, hallucinated])

    result = R.reconcile(pack, prefer_live=True)
    assert result.source == "live"
    kept = {f.finding_id for f in result.findings}
    assert "LLM-GOOD" in kept
    assert "LLM-BAD" not in kept  # the fabricated 41.3% is not in the pack -> dropped
    assert result.dropped == 1
