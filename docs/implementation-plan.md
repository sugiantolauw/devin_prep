# Implementation Plan

Build order for the Apex AI-Driven Financial Due Diligence system. Each phase ends at a
**verification gate** — a test or check that must pass before moving on — and is committed
separately. Phases map to the ADRs; the accuracy-critical work (Phases 2–6) comes before
any UI, because the numbers are the deliverable.

Critical path: **metric engine → anomaly/normalisation → Evidence Pack → LLM reconciliation
+ guardrail**. The UI and API are the last, cheapest steps.

---

## Phase 0 — Scaffold
Monorepo per ADR-0009: `backend/` (FastAPI + `apex_diligence` package), `frontend/`
(Vite + React + TS), `data/` (CSV + both Board Papers committed), root `pyproject.toml`
(`uv`, Python 3.12, `ruff`, `pytest`). README skeleton.
**Gate:** `uv run` boots FastAPI with a `/health` route; Vite dev server proxies to it.

## Phase 1 — Data ingestion & domain model
Load the CSV with pandas into typed structures. Encode the fixed conventions: calendar
year = FY (ADR-0006, trap #6), signed amounts (costs negative), the
`Income Statement → EBITDA → {Gross Profit, Opex} → category → line item` hierarchy.
**Gate:** loader test — 1,728 rows, 2 entities, 4 years (2021–2024), 18 line items,
hierarchy intact.

## Phase 2 — Metric engine (the core) — ADR-0006, test 10a
Deterministic computation of every figure the system will ever show, each carrying a
stable `metric_id`:
- Required: FY EBITDA by entity, FY revenue by entity, monthly revenue/opex trends,
  seasonality (monthly seasonal index vs. annual mean), cost-structure mix.
- Value-add: EBITDA-margin trend by entity, product-mix revenue.
**Gate:** unit tests against verified figures — AU margin 15.7%→19.7%, NZ 15.5%→9.9%,
revenue by entity (AU 102M→135M, NZ 34M→45M). Splitting by entity is mandatory (trap #7).

## Phase 3 — Anomaly detection + normalisation engine — ADR-0003/0006, tests 10a/10c
A genuine detector (rolling seasonal baseline + structural-break / outlier tests) that
flags candidates from the series itself, not hardcoded. Compute the deterministic dollar
impact of each normalisation. Build the Reported→Normalised **EBITDA bridge**: add back the
Sep-2024 one-off, remove the non-recurring May promo portion, **note but do not adjust out**
the sustained Oct run-rate reset (trap #2).
**Gate:** detector flags the Sep dip and May spike unprompted (10c); bridge totals match
computed figures (10a); test that the Oct reset is *not* normalised out.

## Phase 4 — Evidence Pack — ADR-0002
Assemble the structured facts pack the LLM narrates from: all metrics, detected anomalies,
normalisation candidates with impacts, and relevant Board-Paper excerpts. Pydantic schema.
The LLM may reference only `metric_id`s present here.
**Gate:** schema/build test; pack contains the expected metric_ids and anomaly records.

## Phase 5 — Unstructured ingestion — ADR-0005
Parse both Board Papers (docx + pdf text). **Claude-vision extract** the scanned Appendix B
(trap #5) and feed it into the same claim-extraction step. Extract structured narrative
claims (permanent-GM appointment, "no further changes," customer concentration, restructure,
promo) via a Claude call.
**Gate:** appendix extraction returns the O'Connor permanent-GM claim and the ~⅓
concentration figure (mocked fixture + one live smoke call).

## Phase 6 — LLM reconciliation + numeric guardrail (the trust core) — ADR-0002/0003/0007
Reconcile numeric anomalies ↔ narrative claims; surface contradictions (FY2023 "stability
restored" vs. FY2024 "3 GM changes"); emit `Finding[]` via structured output (adaptive
thinking). The **numeric guardrail** extracts every number in each Finding and verifies it
against the Evidence Pack within tolerance — unmatched → rejected; unverifiable claims (the
concentration figure) → routed to a Data-Quality/Verifiability finding, never asserted
(trap #4). Rank Findings by materiality (ADR-0007), anchored to dollar impact where one
exists.
**Gate:** adversarial guardrail tests using `analytical-traps.md` as fixtures (10b);
schema validation over a mocked Claude response (10d).

## Phase 7 — FastAPI backend — ADR-0004
Endpoints: `/metrics` (computed live), `/findings` (LLM output cached to disk), a
regenerate action to re-run the LLM step, `/evidence` (lineage — figure → source), `/health`.
**Gate:** endpoint smoke tests — correct shape/status (10e).

## Phase 8 — React dashboard — ADR-0004/0007
Views: a headline KPI row (the AU↑ / NZ↓ margin story), FY EBITDA & revenue by entity,
monthly revenue/opex trends, seasonality, cost-structure mix, product mix, the **EBITDA
bridge waterfall**, and the ranked **Key Diligence Findings** panel — each Finding showing
its category, cited figures, the reconciled Board-Paper evidence, the management questions,
and its materiality — plus the regenerate control. Recharts.
**Gate:** app runs end-to-end from the CSV to rendered findings; manual visual pass.

## Phase 9 — Tests, README, polish
Full `pytest` run green. README: setup/run, architecture, the accuracy thesis (Python
computes / guardrail / vision / reconciliation), a link to the ADRs and traps doc as the
decision record, and an honest limitations section. The §3.4 slide is already delivered
(`deliverables/Apex_Enterprise_Scaling.pptx`).
**Gate:** clean clone → `uv sync` + `pytest` green → `uv run` + `npm run dev` shows the full
dashboard.

---

## What to demo
The three findings that prove the system, in priority order: (1) the NZ margin collapse with
exact figures, (2) the FY2023↔FY2024 leadership contradiction (only visible because the scan
was read), (3) the Reported→Normalised EBITDA bridge with the correctly-signed one-off. Each
is a place a thin LLM wrapper would get the number wrong, hallucinate, or miss entirely.
