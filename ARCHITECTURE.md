# Architecture

## System shape

```
            ┌─────────────────────────────────────────────────────────────┐
            │                         TRIGGER LAYER                         │
            │                                                               │
   cron ───▶│  scanner.py            POST /webhooks/github                  │
            │  (Dependabot alerts /  (real GitHub Issues event, HMAC-       │
            │   security scan →       verified)                             │
            │   files issues)                                               │
            └───────────────┬───────────────────────┬───────────────────────┘
                            │  issue (labelled devin-fix)
                            ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                      ORCHESTRATOR (core)                      │
            │  orchestrator.py                                              │
            │   • qualifies issue by trigger label                          │
            │   • idempotency check (store)                                 │
            │   • builds remediation prompt + structured-output schema      │
            │   • POST /v1/sessions  ───────────────────┐                   │
            │   • persists Task, comments on issue       │                  │
            └───────────────┬────────────────────────────┼──────────────────┘
                            │                            ▼
                            │                   ┌──────────────────┐
                            │                   │   DEVIN API      │
                            │                   │ (autonomous fix, │
                            │                   │  opens the PR)   │
                            │                   └─────────┬────────┘
                            ▼                             │ GET /v1/session/{id}
            ┌───────────────────────────────┐            │
            │   STORE (SQLite, store.py)     │◀───────────┘
            │   tasks: issue↔session↔PR,     │      poller.py (background tracker)
            │   status, timings              │      maps status_enum → TaskStatus,
            └───────────────┬───────────────┘      captures PR, comments back
                            │
                            ▼
            ┌─────────────────────────────────────────────────────────────┐
            │                    OBSERVABILITY LAYER                         │
            │  metrics.py → GET /metrics (success rate, MTTR, throughput)    │
            │  templates/dashboard.html → GET /dashboard (live)             │
            │  logging_conf.py → structured JSON logs                        │
            └─────────────────────────────────────────────────────────────┘
```

## Task lifecycle

```
PENDING ──create session──▶ RUNNING ──┬── PR produced ───────▶ COMPLETED (terminal)
                                       ├── outcome=needs_human ▶ NEEDS_INPUT (awaits human)
                                       └── error/out-of-credits▶ FAILED (terminal)
```

Sentinel maintains its own coarse `TaskStatus` rather than leaking Devin's
granular `status_enum` to the dashboard. `poller.py` owns the mapping:

| Devin `status_enum`                              | Sentinel `TaskStatus`        |
|--------------------------------------------------|------------------------------|
| `working`, `waiting_for_user`, ...               | `RUNNING`                    |
| `finished` / `blocked` **with** a PR             | `COMPLETED`                  |
| `finished` / `blocked`, `outcome=needs_human`    | `NEEDS_INPUT`                |
| `out_of_credits`, `error`, usage-limit reasons   | `FAILED`                     |

## Key decisions

1. **Devin as a primitive.** The orchestrator hands Devin a *task*, not a
   prompt-and-pray — a structured brief with guardrails plus a
   `structured_output_schema` so the result is machine-readable
   (`outcome`, `pull_request_url`, `summary`, `files_changed`, `verification`).

2. **Idempotency at two layers.** The Devin call sets `idempotent: true`, and the
   store enforces one task per `(repo, issue)`. GitHub *will* deliver a webhook
   twice; neither layer lets that double-spend a credit.

3. **Cost guardrail.** Every session is created with `max_acu_limit` so an
   automated loop has a hard spend ceiling per issue.

4. **Pluggable clients.** `devin_client.py` and `github_client.py` each expose a
   live client and an in-process mock behind one Protocol. Mode is a config flag;
   the orchestrator/poller are identical in mock and live. This is what makes the
   system testable and demoable without credits.

5. **Synchronous-feeling, async-safe.** A single FastAPI process with one
   background poll loop. No queue, no workers, no Redis — deliberately sized to
   the problem and easy to read line-by-line.

## Failure handling

- **Session creation fails** → task marked `FAILED`, error stored, issue
  commented. Pipeline continues with the next finding.
- **Session finishes without a PR** → `FAILED` with a clear reason to investigate.
- **Devin escalates (`needs_human`)** → `NEEDS_INPUT`; the issue thread gets
  Devin's reasoning so a human can decide. The tracker keeps the session visible
  rather than silently dropping it.
- **Poll loop throws** → caught and logged; the loop never dies.

## Extending it (real customer engagement)

- Swap the demo scanner for the live Dependabot alerts API
  (`GET /repos/{owner}/{repo}/dependabot/alerts`) or your SAST/SCA tool.
- Per-repo prompt + guardrail tuning, loaded from repo config.
- Escalation: on `needs_human`, open a Linear/Jira ticket instead of a comment.
- Auto-merge low-risk patch bumps when CI is green; require human review for
  major versions.
- Replace SQLite with Postgres and run the poller as a separate worker when
  fan-out grows.
