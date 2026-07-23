"""The numeric guardrail (ADR-0002).

Every number in a Finding's text must match a figure the system computed (the Evidence
Pack's ``allowed_numbers``) within tolerance, or the Finding is flagged. This turns the
accuracy *claim* into an enforced *property*: a hallucinated figure — including an invented
customer-concentration percentage — cannot pass, because it is not in the pack.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from .findings import Finding

# A number, optionally with $, magnitude word, or %. Years and bare small counts are ignored.
_NUM_RE = re.compile(
    r"(?<![\w.])(\$)?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?"
    r"(million|billion|thousand|bn|m|k)?\s?(%)?",
    re.IGNORECASE,
)
_MAG = {"million": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9, "thousand": 1e3, "k": 1e3}


class NumberCheck(BaseModel):
    text: str
    value: float
    is_percent: bool
    matched: bool
    nearest: float | None = None


class GuardrailReport(BaseModel):
    finding_id: str
    passed: bool
    checks: list[NumberCheck]
    unmatched: list[str]


def _parse(match: re.Match) -> tuple[float, bool, bool] | None:
    """Return (value, is_percent, checkable) or None if the token is not a checkable
    financial figure (years, bare small counts)."""
    currency, numstr, mag, pct = match.groups()
    value = float(numstr.replace(",", ""))
    if mag:
        value *= _MAG[mag.lower()]
    is_percent = bool(pct)
    had_mag = bool(mag) or bool(currency)
    if is_percent:
        return value, True, True
    if had_mag or value >= 1000:
        # Ignore bare 4-digit years written without separators.
        if not had_mag and value == int(value) and 1900 <= value <= 2100:
            return None
        return value, False, True
    return None  # small counts like "3 GM changes"


def _matches(value: float, is_percent: bool, allowed: list[float]) -> tuple[bool, float | None]:
    if is_percent:
        cands = [a for a in allowed if abs(a - value) <= 0.2]
    else:
        tol = max(abs(value) * 0.01, 1.0)
        cands = [a for a in allowed if abs(abs(a) - abs(value)) <= tol]
    if not cands:
        return False, None
    nearest = min(cands, key=lambda a: abs(abs(a) - abs(value)))
    return True, nearest


def check_text(text: str, allowed: list[float]) -> list[NumberCheck]:
    checks: list[NumberCheck] = []
    for m in _NUM_RE.finditer(text):
        parsed = _parse(m)
        if parsed is None:
            continue
        value, is_percent, _ = parsed
        matched, nearest = _matches(value, is_percent, allowed)
        checks.append(
            NumberCheck(
                text=m.group(0).strip(), value=value, is_percent=is_percent,
                matched=matched, nearest=nearest,
            )
        )
    return checks


def validate_finding(finding: Finding, allowed: list[float]) -> GuardrailReport:
    text = finding.observation + " " + " ".join(finding.management_questions)
    checks = check_text(text, allowed)
    unmatched = [c.text for c in checks if not c.matched]
    return GuardrailReport(
        finding_id=finding.finding_id, passed=not unmatched, checks=checks, unmatched=unmatched
    )


def validate(findings: list[Finding], allowed: list[float]) -> list[GuardrailReport]:
    return [validate_finding(f, allowed) for f in findings]


def enforce(findings: list[Finding], allowed: list[float]) -> tuple[list[Finding], list[GuardrailReport]]:
    """Return (findings that passed, all reports). Flagged findings are dropped so a
    hallucinated figure never reaches the report."""
    reports = validate(findings, allowed)
    ok = {r.finding_id for r in reports if r.passed}
    return [f for f in findings if f.finding_id in ok], reports
