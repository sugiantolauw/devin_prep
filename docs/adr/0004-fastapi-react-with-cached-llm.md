# FastAPI + React, with deterministic metrics live and LLM output cached

The system must be a real, demonstrable app (ADR-0001 keeps it lean but genuine). The open
question was *when the LLM runs* relative to a page view.

Decision:

- A **FastAPI** backend computes the deterministic metrics layer **live** from the source
  CSV and serves it to a **React** single-page dashboard. Numbers are always fresh and
  instant.
- The **LLM-generated** observations, questions, and reconciliation are **generated once
  and cached to disk**, served via an endpoint, with an explicit **"Regenerate analysis"**
  action to re-run on demand.
- Charts and tables render from the metrics layer, never from LLM text.

This gives a genuine client/server product with a clean API boundary while avoiding
per-view LLM latency, token cost, and non-determinism — the non-determinism is isolated to
an explicit, user-triggered step. Considered and rejected: (a) an offline batch script
writing a static JSON the React app just displays — less work but reads as less of a
system; (c) calling the LLM live on every request — slow, costly, and unstable between
refreshes for no benefit here.
