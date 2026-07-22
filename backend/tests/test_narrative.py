"""Unstructured ingestion (ADR-0005). Offline path uses the cached extraction; the live
path (Claude vision + structured extraction) runs when a key is present."""

from apex_diligence.documents import fy2023_text, fy2024_text, render_pdf_page_png
from apex_diligence.narrative import build_narrative_context, extract_appendix_b


def test_document_text_extraction():
    assert "3 GM changes" in fy2024_text()  # the FY2024 instability claim
    assert "leadership stability" in fy2023_text().lower()  # FY2023 "restored" claim
    assert len(render_pdf_page_png()) > 1000  # the scanned page renders to PNG


def test_appendix_b_recovered():
    text, _ = extract_appendix_b()
    # The scan carries the material facts the contradiction hinges on.
    assert "O'Connor" in text
    assert "one third" in text.lower()
    assert "Security Tech" in text


def test_narrative_context_supports_the_contradiction():
    nc = build_narrative_context()
    assert len(nc.claims) >= 8
    assert {"FY2023", "FY2023-AppendixB", "FY2024"} <= set(nc.excerpts)
    blob = " ".join(c.text.lower() for c in nc.claims)
    # Both sides of the leadership contradiction are captured.
    assert "stability" in blob or "restored" in blob or "no further changes" in blob
    assert "3 gm changes" in blob
    # And the unverifiable concentration claim is present for the honesty finding.
    assert "one third" in blob or "single reseller" in blob
