# Testing bar

Numerical accuracy is the deliverable, so tests are the proof the numbers are right and the
most convincing thing an evaluator can run — but this is a case study, not a product, so we
target proof-of-correctness, not full coverage.

## Non-negotiable (backend cores)

- **Metric layer** — unit tests asserting the exact verified figures: EBITDA margin by
  entity/year (AU 15.7%→19.7%, NZ 15.5%→9.9%), revenue by entity, the Sep-2024 one-off
  magnitude, the May promo bump, and the Reported→Normalised bridge totals. These are both
  regression tests and executable documentation of correctness.
- **Guardrail (adversarial)** — the cases in `docs/analytical-traps.md` are the fixtures: a
  fabricated number is rejected; a correctly-cited number passes; the unverifiable
  concentration claim is routed to a Data-Quality finding, not asserted.
- **Anomaly detector** — tests that it flags the Sep dip and May spike from the series
  itself (not hardcoded), proving the discovery is real.

## Scoped choices

- **LLM path** — not tested live (non-deterministic, costs tokens). We test the scaffolding
  around it: schema validation of a mocked Claude response plus the guardrail over it. The
  model's judgement isn't unit-testable; its contract is.
- **Frontend & API** — one or two FastAPI endpoint smoke tests (shape/status). No automated
  frontend tests — effort is better spent on the backend accuracy suite for a focused
  dashboard.
