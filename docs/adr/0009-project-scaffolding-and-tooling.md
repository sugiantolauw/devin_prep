# Project scaffolding and tooling

## Layout — monorepo, three parts

```
/backend      FastAPI app + the analysis engine (metrics, anomaly detection,
              Evidence Pack assembly, LLM reconciliation, numeric guardrail)
/frontend     React + Vite + TypeScript dashboard
/data         source CSV + the two Board Papers (committed)
```

The analysis engine is a plain Python package inside `backend/` rather than a separate
top-level package — nothing else consumes it, so a shared package would be premature.
Pydantic models for the Finding and Evidence Pack live there and are what FastAPI serves.

## Python tooling

`uv` for environment and dependency management (`pyproject.toml`), Python 3.12, `ruff` for
lint/format. Chosen over `poetry` / `pip`+`requirements.txt` for speed and current-practice
signal; the trade-off is that a reviewer must have (or install) `uv`, which is a one-line
install.

## Frontend tooling

React + Vite + TypeScript; Recharts for the bar/line/waterfall views (declarative, right
weight for a focused dashboard); plain CSS / a small utility layer rather than a heavy
component framework. The Vite dev server proxies to FastAPI so there is no CORS friction in
development.

## Data in the repo

The source CSV and both Board Papers are committed to `/data` so the case study runs
out-of-the-box on clone — no external fetch. The files are small and are the fixed inputs
to the exercise.
