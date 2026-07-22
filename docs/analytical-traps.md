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

## 3. Narrative vs. numbers — trust neither blindly (and locate the promo correctly)
The FY2024 paper ties the May revenue step-up to the "Smart Security" launch, which reads
as a Smart-Home story. **It isn't.** Cross-referencing the data: the May-2024 promo is a
**whole-basket, single-month spike** — AU total revenue 13.19M vs an ~11M run-rate, with
*every* product line up (Laptops +30%, Mobile +22%, Smart Home +46%, TVs +16%,
Accessories +13%) and a full reversion in June (11.05M). Meanwhile **Smart Home Devices
ramps hard in Q4 (to ~1.43M AU in Dec) as genuine secular growth, unrelated to the promo.**
Two failure modes: (a) attributing the promo to Smart Home only, understating it; (b)
"normalising out all above-baseline Smart Home revenue," which strips real Q4 growth.
- **Anchor:** AU total revenue 2024 by month (M): Jan 10.65, Apr 10.76, **May 13.19**,
  Jun 11.05, Dec 11.61. Promo uplift ≈ 2.28M (AU), ~0.78M (NZ), computed vs adjacent months.
- **Neutralised by:** the transient-spike detector runs on *total* entity revenue (not one
  product); only the single-month uplift is removed, at gross margin; the Q4 ramp is
  untouched (ADR-0003/0006).

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
