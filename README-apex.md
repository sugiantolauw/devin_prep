# Apex Electronics — AI-Driven Financial Due Diligence

> **Note:** this repository also contains an unrelated pre-existing project ("Sentinel",
> described in the root `README.md`). This case study is self-contained in `backend/`,
> `frontend/`, `data/`, `docs/`, and `deliverables/`. See the note at the end.

An AI application that performs financial due diligence on Apex Electronics: it analyses the
structured income statement, incorporates the unstructured Board Papers (including a scanned
appendix), and produces ranked, grounded **observations and management questions** — the
basis of a diligence report — with supporting charts and tables.

## The thesis

The brief specifies the stack but grades the **output**: *"numerically accurate…
observations/questions [that] will form the basis of a due diligence report."* The dataset is
engineered with traps that punish a thin LLM wrapper — revenue that grows while margin
collapses, a one-off that must be told apart from a sustained saving, a promo that reads as
one product but is whole-basket, a concentration figure that isn't in the data, and two Board
Papers that contradict each other on NZ leadership.

So the system is built on one principle: **Python computes every number; Claude narrates
under a numeric guardrail.** The model supplies judgement (reconciling data against the Board
narrative, catching the contradiction); it never does arithmetic, and it cannot ship a figure
the engine didn't compute. Each architecture decision neutralises a specific trap — see
[`docs/analytical-traps.md`](docs/analytical-traps.md).

## Architecture

```
CSV ─▶ ingest ─▶ metric engine ─────────────┐
                 anomaly detection ──────────┤
                 normalisation + EBITDA bridge│─▶ Evidence Pack ─▶ Claude reconciliation
Board Papers ─▶ text + vision extraction ────┘        (facts)        (judgement, structured out)
(scanned appendix → Claude vision)                                          │
                                                                    numeric guardrail
                                                                            │
                                                              ranked Findings ─▶ FastAPI ─▶ React
```

- **Deterministic metrics** (`apex_diligence/metrics.py`) — every figure carries a stable
  `metric_id`; the LLM may only cite ids that exist.
- **Anomaly detection** (`anomalies.py`) — three detectors (point spikes, transient
  total-revenue spikes, novel within-year run-rate shifts) surface the real events from the
  series, not hardcoded months.
- **Normalisation + bridge** (`normalisation.py`) — Reported → Normalised EBITDA, adding back
  the one-off, removing the non-recurring promo at gross margin, and **noting but not
  adjusting out** the sustained salary reset.
- **Evidence Pack** (`evidence.py`) — the structured facts Claude narrates from; its
  `allowed_numbers()` is the guardrail's ground truth.
- **Unstructured ingestion** (`documents.py`, `narrative.py`) — Board-Paper text plus
  **Claude-vision transcription of the scanned Appendix B**, then structured claim extraction.
- **Reconciliation + guardrail** (`reconcile.py`, `guardrail.py`) — Findings via Claude
  structured output; every number verified against the Evidence Pack; a normalisation is
  surfaced only when a numeric anomaly *and* a narrative claim agree.

The reasoning behind each choice is recorded as ADRs in [`docs/adr/`](docs/adr/), the domain
glossary in [`CONTEXT.md`](CONTEXT.md), and the build plan in
[`docs/implementation-plan.md`](docs/implementation-plan.md) — all produced during a
`grill-with-docs` session before any code was written.

## Running it

**Backend** (Python 3.12, [uv](https://docs.astral.sh/uv/)):

```bash
cd backend
uv sync
uv run uvicorn app.main:app --port 8000
```

**Frontend** (Node 18+):

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /api to :8000)
```

**LLM configuration.** Set `ANTHROPIC_API_KEY` to run the live pipeline — Claude vision
transcribes the scanned appendix, extracts narrative claims, and reconciles the findings
(model `claude-opus-4-8`). **Without a key the app still runs end-to-end**: the vision and
reconciliation steps fall back to a cached extraction and a deterministic reference
reconciliation, so every number and finding is real and grounded. The findings source
(`live` / `offline`) is shown in the UI, and **Regenerate analysis** re-runs the LLM step.

## Analytics

Required views — FY EBITDA by entity, FY revenue by entity, monthly revenue/opex trends,
seasonality, cost-structure breakdown — plus the value-add layer: EBITDA-margin trend by
entity, product mix, and the **Reported → Normalised EBITDA bridge**.

## What it finds (the demo spine)

1. **NZ EBITDA-margin collapse** — revenue grows (33.8m → 45.1m) while margin falls
   15.5% → 9.9%. The deterioration is profitability, not the top line.
2. **Leadership contradiction** — FY2023 (incl. the scanned appendix) declares NZ leadership
   "restored… no further changes"; FY2024 reports 3 GM changes in 18 months. Only visible
   because the scan was read.
3. **AU normalisation bridge** — reported EBITDA 26.48m → add back the Sep one-off (+0.51m)
   → remove the non-recurring May promo (−0.91m) → normalised 26.07m; the Oct salary reset
   (~3.6m annualised) is noted, not adjusted.

Each is a spot where a thin wrapper would get the number wrong, hallucinate, or miss the scan.

## Testing

```bash
cd backend && uv run pytest        # 32 tests
```

Accuracy is the deliverable, so the tests prove it: the metric layer reproduces the verified
figures; the detectors flag the real events from the series; the **guardrail is tested
adversarially** (a fabricated number is rejected, an invented concentration % is rejected,
years/counts are ignored, a mocked hallucinated LLM finding is dropped); the AU bridge
arithmetic is checked and the reset is confirmed *not* normalised out.

## Enterprise scaling (§3.4)

The one-slide overview of moving from this local prototype to an enterprise-grade product is
in [`deliverables/Apex_Enterprise_Scaling.pptx`](deliverables/Apex_Enterprise_Scaling.pptx) —
framed as the axes we deliberately kept lean locally and would industrialise (warehouse
ingestion, real RAG/document-AI, multi-tenancy, async scaling, LLM-ops + eval harness,
security/MNPI governance).

## Repository layout (this case study)

```
backend/      FastAPI app + apex_diligence engine (metrics, anomalies, normalisation,
              evidence, narrative, reconcile, guardrail) + tests
frontend/     React + Vite + TS dashboard (KPI row, charts, EBITDA waterfalls, findings)
data/         income statement CSV + the two Board Papers
docs/         ADRs, CONTEXT.md glossary, analytical-traps.md, implementation-plan.md
deliverables/ Apex_Enterprise_Scaling.pptx (§3.4)
```

## Limitations

- **Offline reconciliation** is a deterministic reference so the case runs without a key; the
  live path uses Claude for genuine reconciliation. The cached appendix transcription and
  claim set are clearly labelled fixtures.
- **The NZ EBITDA bridge** applies numeric candidates; only the AU bridge's items are
  confirmed against explicit Board-Paper claims. NZ candidates are shown as illustrative and
  are gated by narrative confirmation (the both-sides rule) before becoming asserted findings —
  which is why the asserted findings include only the AU normalisation.
- **Customer concentration** cannot be verified from the P&L (no customer dimension) — the
  system flags this rather than fabricating a figure, and requests customer-level data.
- **Pre-existing content.** The repo root `README.md`, `sentinel/`, `templates/`, `tests/`,
  `data/sample_findings.json`, `Makefile`, and Docker files belong to an unrelated prior
  project and are not part of this case study.
```
