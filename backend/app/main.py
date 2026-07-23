"""FastAPI application (ADR-0004).

Deterministic metrics are computed live; LLM-generated findings are cached to disk with an
explicit regenerate action. In dev the Vite server proxies /api here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import service

app = FastAPI(
    title="Apex Diligence API",
    description="AI-driven financial due diligence for Apex Electronics",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/metrics")
def metrics() -> dict:
    """All deterministic analytical views, computed live from the CSV."""
    return service.get_metrics()


@app.get("/api/bridges")
def bridges() -> list[dict]:
    """Reported -> Normalised EBITDA bridges (AU, NZ)."""
    return service.get_bridges()


@app.get("/api/evidence")
def evidence() -> dict:
    """Material anomalies + normalisation items (the numeric side of the Evidence Pack)."""
    return service.get_evidence()


@app.get("/api/findings")
def findings() -> dict:
    """Ranked, guardrail-checked diligence findings (cached)."""
    return service.get_findings_payload()


@app.post("/api/findings/regenerate")
def regenerate_findings() -> dict:
    """Re-run reconciliation (the LLM step) and refresh the cache."""
    return service.get_findings_payload(regenerate=True)
