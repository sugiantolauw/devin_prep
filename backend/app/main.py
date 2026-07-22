"""FastAPI application entry point.

Deterministic metrics are computed live; LLM-generated findings are cached to disk with an
explicit regenerate action (ADR-0004). Endpoints are added in Phase 7; this module starts as
a health-checkable skeleton.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Apex Diligence API",
    description="AI-driven financial due diligence for Apex Electronics",
    version="0.1.0",
)

# In dev the Vite server proxies /api, so CORS is not strictly needed; permissive here keeps
# a direct browser call working too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
