# Analytical traps in the Apex dataset

The dataset is engineered with tripwires that separate real diligence from "ran the
numbers." This is the build checklist and the source of the guardrail's test cases —
every trap below must be actively neutralised, and each maps to an architecture choice.

## 1. Revenue vs. margin (the big one)
The narrative calls NZ "deteriorating." The lazy read is "NZ revenue is falling." It is
**not** — NZ revenue rises every year (33.8M → 45.1M). What collapses is **EBITDA
margin** (15.5% → 9.9%). A finding that says "NZ revenue declining" is fabricated and
contradicts the data.
- **Anchor:** NZ revenue FY21–24 = 33.8M / 37.1M / 40.8M / 45.1M; NZ EBITDA margin =
  15.5% / 14.0% / 12.3% / 9.9%.
- **Neutralised by:** Python computes all figures + numeric guardrail (ADR-0002).

## 2. One-off vs. sustained — do not normalise out a real improvement
The Sep-2024 AU salary spike (~-1.60M vs ~-1.05M baseline) is a genuine one-off → add
back. The **Oct-2024-onward lower run-rate (~-0.83–0.94M) is a *sustained* saving**, not a
one-off — normalising it away understates true earnings power. The FY2024 paper is
explicit: "one-off Sep; sustained run-rate reduction from Oct."
- **Anchor:** AU Salaries & Wages 2024: Jan–Aug ~-1.05M to -1.15M; Sep -1.60M; Oct -0.83M;
  Nov -0.88M; Dec -0.94M.
- **Neutralised by:** both-sides reconciliation (ADR-0003); bridge notes the reset, does
  not adjust it out (ADR-0006).

## 3. Narrative vs. numbers — trust neither blindly
The FY2024 paper says the May Smart Security revenue spike "reduced to normal once the
promo ended." The data *partly* agrees — a May–Jun bump reverts toward ~790k — **but Smart
Home Devices then ramps hard in Q4 (to ~1.9M in Dec) for unrelated reasons.** Naively
"normalising out all above-baseline Smart Home revenue" over-adjusts.
- **Anchor:** Smart Home Devices 2024 (Group): Apr 625k, May 901k, Jun 887k, Jul 792k …
  Oct 1.14M, Nov 1.44M, Dec 1.91M.
- **Neutralised by:** anomaly detection + narrative reconciliation must both support the
  adjustment, and only the promo-attributable portion is removed (ADR-0003/0006).

## 4. The unverifiable figure (honesty trap)
Appendix B claims ~one third of NZ revenue runs through one reseller (Security Tech Inc.).
The CSV has **no customer/reseller dimension — only product lines.** This cannot be
verified from the structured data. Do not hallucinate or claim to confirm it — raise it as
a management question and request customer-level data.
- **Neutralised by:** guardrail rejects any fabricated figure; becomes a Data-Quality /
  Verifiability finding.

## 5. Cross-document contradiction (highest-value find)
FY2023 + its scanned Appendix B state NZ leadership is "restored… no further changes
anticipated" and name James O'Connor as permanent GM (effective 1 Jan 2023). FY2024 reports
"3 GM changes in 18 months." Skipping the scanned appendix loses that FY2023 *specifically
promised stability* — which makes the churn far more damning.
- **Neutralised by:** Claude-vision extraction of the scan (ADR-0005); reconciliation flags
  the contradiction as a top-materiality Finding.

## 6. Instruction vs. instinct — the fiscal year
Apex is ASX-listed; instinct says an Australian Jul–Jun fiscal year. The brief overrides:
**treat calendar years as reported FY (Jan–Dec).** Follow the brief.
- **Neutralised by:** locked in ADR-0006.

## 7. Signs, entities, aggregation
Costs are stored negative; EBITDA = signed sum. Absolute values break margins. Report
Group-only and the AU↑ / NZ↓ divergence — the whole story — disappears. Always split by
entity.
- **Neutralised by:** metric semantics fixed in ADR-0006; FY EBITDA/Revenue *by entity* are
  first-class required views.

## 8. Do not force an all-negative report
AU genuinely improves (margin 15.7% → 19.7%). A balanced read notes it **and** probes
durability: the AU cut was "salary-only" — does it risk the same capability/attrition
death-spiral NZ is in? A positive finding with a sharp follow-up reads as senior.
- **Neutralised by:** Finding taxonomy includes Profitability/Growth (positive) categories,
  not just risks (ADR-0007).

## Meta-trap
The case *looks* like "build an app" but is *graded* on diligence judgement under a
numerical-accuracy constraint. Effort spent on infrastructure at the expense of correct,
sharp observations fails the brief. This is why we tilted insight-first (ADR-0001).
