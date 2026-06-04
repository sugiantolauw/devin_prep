"""FastAPI application: the event ingress, control plane, and observability
surface for the pipeline.

Endpoints
---------
POST /webhooks/github  real GitHub `issues` webhook (verifies signature)
POST /scan             run the scanner: file issues + dispatch remediation
POST /simulate         file a single synthetic issue and dispatch (demo helper)
GET  /status           JSON list of all tasks
GET  /metrics          JSON analytics (success rate, MTTR, throughput, ...)
GET  /dashboard        live HTML dashboard
GET  /healthz          liveness
"""
from __future__ import annotations

import hashlib
import hmac
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import get_settings
from .devin_client import build_devin_client
from .github_client import build_github_client
from .logging_conf import configure_logging, get_logger
from .metrics import compute_metrics, task_rows
from .models import Finding
from .orchestrator import Orchestrator
from .poller import Tracker
from .scanner import run_scan
from .store import Store

log = get_logger("sentinel.main")
_templates = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parent.parent / "templates")),
    autoescape=select_autoescape(["html"]),
)


def build_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    store = Store(settings.db_path)
    devin = build_devin_client(settings)
    github = build_github_client(settings)
    orchestrator = Orchestrator(
        store, devin, github,
        repo=settings.target_repo,
        trigger_label=settings.trigger_label,
        max_acu_limit=settings.devin_max_acu_limit,
    )
    tracker = Tracker(store, devin, github,
                      interval_seconds=settings.poll_interval_seconds)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        tracker.start()
        log.info("sentinel up", extra={
            "ctx_mode": settings.mode, "ctx_repo": settings.target_repo})
        yield
        await tracker.stop()
        await devin.aclose()
        await github.aclose()

    app = FastAPI(title="Sentinel", version="0.1.0", lifespan=lifespan)
    # Expose collaborators for tests / introspection.
    app.state.settings = settings
    app.state.store = store
    app.state.orchestrator = orchestrator
    app.state.tracker = tracker
    app.state.github = github

    @app.get("/healthz")
    async def healthz():
        return {"ok": True, "mode": settings.mode}

    @app.post("/webhooks/github")
    async def github_webhook(
        request: Request,
        x_hub_signature_256: Optional[str] = Header(default=None),
        x_github_event: Optional[str] = Header(default=None),
    ):
        raw = await request.body()
        if settings.github_webhook_secret:
            _verify_signature(raw, x_hub_signature_256, settings.github_webhook_secret)
        payload = await request.json()
        if x_github_event != "issues":
            return {"ignored": True, "reason": f"event {x_github_event}"}
        action = payload.get("action")
        if action not in ("opened", "labeled", "reopened"):
            return {"ignored": True, "reason": f"action {action}"}
        task = await orchestrator.handle_issue_event(payload["issue"])
        return {"dispatched": task is not None,
                "session_id": task.session_id if task else None}

    @app.post("/scan")
    async def scan():
        """Run the scanner, then dispatch a Devin session per filed issue."""
        issues = await run_scan(github, trigger_label=settings.trigger_label)
        dispatched = []
        for issue in issues:
            task = await orchestrator.handle_issue_event(issue)
            if task:
                dispatched.append({"issue": issue["number"],
                                   "session_id": task.session_id})
        return {"filed": len(issues), "dispatched": dispatched}

    @app.post("/simulate")
    async def simulate(request: Request):
        """File one synthetic issue and dispatch it. Body may override fields."""
        body = await request.json() if await request.body() else {}
        finding = Finding(
            id=body.get("id", "SIM-1"),
            title=body.get("title", "Simulated: upgrade vulnerable dependency"),
            severity=body.get("severity", "high"),
            category=body.get("category", "vulnerability"),
            body=body.get("body", "Synthetic finding generated for a demo run."),
            package=body.get("package", "example-pkg"),
            cve=body.get("cve"),
        )
        labels = [settings.trigger_label, f"severity:{finding.severity}",
                  f"category:{finding.category}"]
        issue = await github.create_issue(finding, labels)
        issue["labels"] = [{"name": l} for l in labels]
        task = await orchestrator.handle_issue_event(issue)
        return {"issue": issue["number"],
                "session_id": task.session_id if task else None}

    @app.post("/poll")
    async def poll():
        """Force one tracker poll cycle (handy for demos / tests)."""
        n = await tracker.poll_once()
        return {"reached_terminal": n}

    @app.get("/status")
    async def status():
        return {"tasks": task_rows(store)}

    @app.get("/metrics")
    async def metrics():
        return JSONResponse(compute_metrics(store))

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        html = _templates.get_template("dashboard.html").render(
            m=compute_metrics(store),
            tasks=task_rows(store),
            repo=settings.target_repo,
            mode=settings.mode,
        )
        return HTMLResponse(html)

    return app


def _verify_signature(raw: bytes, signature: Optional[str], secret: str) -> None:
    if not signature:
        raise HTTPException(status_code=401, detail="missing signature")
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="bad signature")


app = build_app()
