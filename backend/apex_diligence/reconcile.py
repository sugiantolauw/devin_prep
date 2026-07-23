"""Reconciliation: numeric anomalies x narrative -> ranked Findings (ADR-0003/0007).

Two paths, both filtered through the numeric guardrail (ADR-0002):
- **live** — Claude receives the Evidence Pack and emits Findings via structured output,
  instructed to cite only figures present in the pack and to propose a normalisation only
  when a numeric anomaly *and* a narrative claim agree;
- **offline** — a deterministic reference reconciliation that builds the headline findings
  directly from the pack, so the case study runs without a key.

Either way, every figure in a Finding's text must survive the guardrail before it ships.
"""

from __future__ import annotations

from pydantic import BaseModel

from .evidence import EvidencePack, build_evidence_pack
from .findings import Evidence, Finding, rank
from .guardrail import GuardrailReport, enforce
from .llm import MODEL, get_client
from .narrative import build_narrative_context

MONEY = lambda v: f"${abs(v):,.0f}"  # noqa: E731
PCT = lambda v: f"{v:.1f}%"  # noqa: E731


class ReconciliationResult(BaseModel):
    findings: list[Finding]
    reports: list[GuardrailReport]
    source: str  # "live" | "offline"
    dropped: int  # findings removed by the guardrail


def _fy(pack: EvidencePack, entity: str, year: int):
    return next(r for r in pack.fy_summary if r.entity == entity and r.fy == year)


def _bridge(pack: EvidencePack, entity: str):
    return next(b for b in pack.bridges if b.entity == entity)


def reconcile_offline(pack: EvidencePack) -> list[Finding]:
    nz21, nz24 = _fy(pack, "NZ", 2021), _fy(pack, "NZ", 2024)
    au21, au24 = _fy(pack, "AU", 2021), _fy(pack, "AU", 2024)
    au_bridge = _bridge(pack, "AU")
    reset = next((n for n in au_bridge.noted_items if n.kind == "sustained_reset"), None)
    promo_au = next(
        (i for i in pack.normalisation_items
         if i.kind == "non_recurring_revenue" and i.entity == "AU"), None
    )

    nz_margin_gap = (nz21.ebitda_margin_pct - nz24.ebitda_margin_pct) / 100 * nz24.revenue

    findings = [
        Finding(
            finding_id="F-NZ-MARGIN",
            category="Profitability/Margin",
            entity="NZ",
            title="NZ EBITDA margin collapse despite revenue growth",
            observation=(
                f"NZ revenue rose every year, from {MONEY(nz21.revenue)} in FY2021 to "
                f"{MONEY(nz24.revenue)} in FY2024, yet EBITDA margin fell from "
                f"{PCT(nz21.ebitda_margin_pct)} to {PCT(nz24.ebitda_margin_pct)} and EBITDA "
                f"itself declined from {MONEY(nz21.ebitda)} to {MONEY(nz24.ebitda)}. The "
                "deterioration is in profitability, not the top line — the board narrative "
                "attributes it to execution slippage linked to leadership churn."
            ),
            evidence=Evidence(
                metric_ids=[
                    "revenue.NZ.FY2021", "revenue.NZ.FY2024",
                    "ebitda_margin_pct.NZ.FY2021", "ebitda_margin_pct.NZ.FY2024",
                    "ebitda.NZ.FY2021", "ebitda.NZ.FY2024",
                ],
                values=[nz21.revenue, nz24.revenue, nz21.ebitda_margin_pct,
                        nz24.ebitda_margin_pct, nz21.ebitda, nz24.ebitda],
                claim_ids=["c9", "c6"],
            ),
            management_questions=[
                "What specifically drove the ~5.6pp NZ EBITDA-margin compression — mix, "
                "pricing, or cost inflation — given revenue kept growing?",
                "How much of the margin decline management attributes to leadership churn "
                "versus structural cost, and what is reversible?",
            ],
            materiality="High",
            dollar_impact=nz_margin_gap,
        ),
        Finding(
            finding_id="F-LEADERSHIP",
            category="Narrative-vs-Data Contradiction",
            entity="NZ",
            title="FY2023 declared NZ leadership 'restored'; FY2024 reports 3 GM changes in 18 months",
            observation=(
                "The FY2023 Board Paper (including scanned Appendix B) states the permanent NZ "
                "GM appointment closed the leadership transition and that no further NZ "
                "executive changes were anticipated. The FY2024 paper then reports three GM "
                "changes in eighteen months and two critical vacancies filled by interim "
                "resources. The two papers directly contradict each other on NZ leadership "
                "stability — the very period the FY2023 paper called settled."
            ),
            evidence=Evidence(claim_ids=["c1", "c3", "c6"]),
            management_questions=[
                "Please reconcile the FY2023 statement that NZ leadership was stabilised with "
                "the FY2024 disclosure of three GM changes in eighteen months.",
                "What is the current permanent-versus-interim status of the NZ executive team, "
                "and when were each of the GM changes effective?",
            ],
            materiality="High",
            dollar_impact=None,
        ),
        Finding(
            finding_id="F-AU-NORMALISATION",
            category="Normalisation",
            entity="AU",
            title="AU FY2024 EBITDA normalisation bridge",
            observation=(
                f"AU reported EBITDA of {MONEY(au_bridge.reported_ebitda)} in FY2024 includes a "
                f"one-off September restructuring cost of {MONEY(au_bridge.steps[1].delta)} "
                "(added back) and a non-recurring May promotional revenue uplift, removed at "
                f"gross margin for an EBITDA effect of {MONEY(au_bridge.steps[2].delta)}, giving "
                f"normalised EBITDA of {MONEY(au_bridge.normalised_ebitda)}. A separate "
                "sustained salary run-rate reset from October"
                + (f" (~{MONEY(reset.context['annualised_saving'])} annualised)" if reset else "")
                + " is noted but not normalised out, as it is a genuine run-rate improvement."
            ),
            evidence=Evidence(
                metric_ids=["ebitda.AU.FY2024"],
                values=[au_bridge.reported_ebitda, au_bridge.steps[1].delta,
                        au_bridge.steps[2].delta, au_bridge.normalised_ebitda]
                + ([reset.context["annualised_saving"]] if reset else []),
                claim_ids=["c7", "c8"],
            ),
            management_questions=[
                "Can management confirm the September AU cost is a genuine one-off "
                "restructuring charge and provide the supporting detail?",
                "What incremental margin did the May promotional volume actually earn — the "
                "add-back assumes gross margin, which may overstate it for discounted volume?",
            ],
            materiality="High",
            dollar_impact=au_bridge.reported_ebitda - au_bridge.normalised_ebitda,
        ),
        Finding(
            finding_id="F-AU-MARGIN",
            category="Profitability/Margin",
            entity="AU",
            title="AU margin expansion — is the salary-only restructure durable?",
            observation=(
                f"AU EBITDA margin expanded from {PCT(au21.ebitda_margin_pct)} in FY2021 to "
                f"{PCT(au24.ebitda_margin_pct)} in FY2024 on revenue of {MONEY(au24.revenue)}, "
                "helped by operating leverage and the Q4 salary-only restructuring. The "
                "restructure was salary-only, which raises a durability question given NZ's "
                "leadership-churn problems."
            ),
            evidence=Evidence(
                metric_ids=["ebitda_margin_pct.AU.FY2021", "ebitda_margin_pct.AU.FY2024",
                            "revenue.AU.FY2024"],
                values=[au21.ebitda_margin_pct, au24.ebitda_margin_pct, au24.revenue],
                claim_ids=["c7"],
            ),
            management_questions=[
                "Is the salary-only AU restructuring sustainable, or does it risk the "
                "capability loss and attrition now visible in NZ?",
                "How much of the AU margin gain is structural operating leverage versus the "
                "one-off Q4 salary action?",
            ],
            materiality="Medium",
            dollar_impact=(au24.ebitda_margin_pct - au21.ebitda_margin_pct) / 100 * au24.revenue,
        ),
        Finding(
            finding_id="F-PROMO",
            category="Growth/Trend",
            entity="Group",
            title="May-2024 promo is a non-recurring, whole-basket revenue spike",
            observation=(
                "The May-2024 Smart Security promotion produced a single-month, whole-basket "
                "revenue spike that reverted the next month — an AU total-revenue uplift of "
                f"{MONEY(promo_au.revenue_impact) if promo_au else 'material amount'} above the "
                "adjacent-month baseline, across all product lines rather than one. It should "
                "be treated as non-recurring; separately, the Smart Home Devices Q4 ramp is "
                "genuine secular growth and is not part of the promo."
            ),
            evidence=Evidence(
                metric_ids=["revenue_monthly.AU.2024-05"],
                values=[abs(promo_au.revenue_impact)] if promo_au else [],
                claim_ids=["c8"],
            ),
            management_questions=[
                "Is the Smart Security promotion repeatable, and did it pull forward demand "
                "from June (which fell back to the prior run-rate)?",
                "What is the underlying, promo-adjusted growth rate by product line?",
            ],
            materiality="Medium",
            dollar_impact=abs(promo_au.revenue_impact) if promo_au else None,
        ),
        Finding(
            finding_id="F-CONCENTRATION",
            category="Data Quality/Verifiability",
            entity="NZ",
            title="Customer concentration claimed but unverifiable from the P&L",
            observation=(
                "The FY2023 Board Paper states that around one third of NZ FY2022 channel "
                "revenue ran through a single reseller (Security Tech Inc.), and flags "
                "diversification as a priority. This concentration cannot be verified from the "
                "supplied income statement, which breaks revenue down by product line only, "
                "with no customer or channel dimension. It is a material dependency asserted "
                "in narrative but absent from the structured data."
            ),
            evidence=Evidence(claim_ids=["c2", "c4"]),
            management_questions=[
                "Please provide customer- or channel-level revenue so the Security Tech Inc. "
                "concentration can be quantified and tracked.",
                "Given diversification was a FY2023 priority, what is the current single-"
                "customer revenue share, and has it fallen since FY2022?",
            ],
            materiality="Medium",
            dollar_impact=None,
        ),
    ]
    return findings


class _FindingList(BaseModel):
    findings: list[Finding]


def _reconcile_live(pack: EvidencePack) -> list[Finding]:
    client = get_client()
    system = (
        "You are a financial due-diligence analyst. You are given an Evidence Pack of "
        "pre-computed figures and extracted board-paper claims. Rules: (1) cite ONLY numbers "
        "present in the Evidence Pack, in exact form; never compute or estimate a number. "
        "(2) Propose a normalisation only when BOTH a numeric anomaly and a narrative claim "
        "support it. (3) Surface contradictions between the data and the narrative, or between "
        "the two board papers. (4) If a narrative claim cannot be verified from the structured "
        "data (e.g. customer concentration), raise it as a Data Quality/Verifiability finding "
        "and do NOT assert a number for it. Rank findings by materiality (High/Medium/Low)."
    )
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": pack.model_dump_json()}],
        output_format=_FindingList,
    )
    return resp.parsed_output.findings


def reconcile(pack: EvidencePack | None = None, prefer_live: bool | None = None) -> ReconciliationResult:
    if pack is None:
        pack = build_evidence_pack(narrative=build_narrative_context())
    use_live = get_client() is not None if prefer_live is None else prefer_live

    if use_live:
        findings = _reconcile_live(pack)
        source = "live"
    else:
        findings = reconcile_offline(pack)
        source = "offline"

    kept, reports = enforce(findings, pack.allowed_numbers())
    return ReconciliationResult(
        findings=rank(kept), reports=reports, source=source,
        dropped=len(findings) - len(kept),
    )
