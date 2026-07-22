# LLM stack: Anthropic Claude (Opus 4.8), structured-output pipeline, no agent/RAG

The brief allows any provider. We use **Anthropic Claude** throughout — one SDK
covers the three things we need: vision (to read the scanned Appendix B), native
**structured outputs** (to enforce the `Finding` schema and give the guardrail a
typed target), and strong reasoning for reconciliation.

- **Model:** `claude-opus-4-8`. This is a diligence-reasoning task (reconciling
  numbers against narrative, catching the cross-document contradiction) where model
  quality is the deliverable, and the workload is tiny (one analysis run over two
  short documents plus an Evidence Pack), so cost and latency are immaterial.
  Considered and rejected: `claude-sonnet-5` (cheaper/faster, also supports vision +
  structured outputs) — a defensible production-minded choice, but for a one-shot
  case study we spend the trivial extra for the sharpest observations.
- **Orchestration:** a plain deterministic pipeline with structured outputs, **not**
  an agent and **not** RAG. Python builds the Evidence Pack; discrete Claude calls
  vision-extract the appendix, extract board-paper claims, and reconcile → emit
  `Finding[]` via structured output with adaptive thinking on; the guardrail then
  validates. Board papers are passed in full context (two ~2-page documents — a
  vector store would be theatre). This keeps the non-determinism isolated to explicit,
  cacheable steps and matches the lean posture of ADR-0001/0003.
