# Loom script — simple English, ~4.5 min (5:00 hard cap)

Goal: pitch Devin to a VP of Engineering + senior ICs. Read it naturally; the
`[…]` notes are screen cues, not spoken. Prepare these before recording:

- **Terminal** running the live server (ready to show `curl .../scan` + logs)
- **Browser tab 1:** http://localhost:8000/dashboard (already populated)
- **Browser tab 2:** your fork's Pull requests
- **Browser tab 3:** `ARCHITECTURE.md` (for the diagram)

Pro tip: record the `curl scan` + logs live (instant, looks great), then cut to
the already-populated dashboard — don't wait on camera for sessions to finish.

---

### [0:00–0:35] WHAT — the problem  *[your face or the dashboard]*

> "Hi. This is **Sentinel**. It uses Devin to fix dependency and security issues
> automatically — with no engineer in the loop.
>
> Here's the problem. Big teams get a flood of dependency and security alerts
> every week. Right now, a person has to read each one, upgrade the package, fix
> what breaks, run the tests, and open a pull request. It's slow, and it eats
> senior engineers' time. Dependabot opens the PR — but a human still has to do
> the fix. Sentinel hands that whole job to Devin."

### [0:35–2:10] HOW — demo + architecture  *[terminal → dashboard → fork PRs]*

> "Let me show you. I run one command to scan my copy of Apache Superset."
> *[show `curl .../scan` + the log lines]*
>
> "That scan creates a GitHub issue for each problem. For each issue, my code
> calls the Devin API and starts a session. Here's the dashboard." *[/dashboard]*
> "It shows every issue, its severity, the Devin session, and the pull request.
> Up top: success rate, throughput, and average time to fix.
>
> Now, here's what Devin actually did." *[fork → Pull requests]*
> - "First PR: it upgraded **Flask from 2.3.3 to 3.1.3**. A real code change,
>   with the tests run.
> - Second PR: the interesting one. The task was moving off old **SQLAlchemy 1.4
>   to 2.0** — a risky, far-reaching change. Devin did *not* force it. It opened
>   a PR with a step-by-step **migration plan** instead. It knew when *not* to act.
>
> The design is simple." *[ARCHITECTURE.md diagram]* "Three parts. A **trigger** —
> a scan or a webhook. An **orchestrator** that turns each issue into a Devin
> session, with a spend limit per session so costs stay safe. And an
> **observability** layer — this dashboard, logs, and a metrics page. One small
> service. No heavy infrastructure."

### [2:10–3:20] WHY Devin  *[back to the PRs]*

> "Why Devin? Without it, you have two choices. Dependabot — which opens a PR you
> still have to fix yourself. Or a human — slow and expensive. Devin fills the
> gap. It reads the issue, writes the fix, runs the tests, sees what breaks, and
> fixes it — then opens a PR you can review. And when something is too risky,
> like the SQLAlchemy upgrade, it stops and writes a plan instead of guessing.
> Nothing else does autonomous, *tested* fixes like this today."

### [3:20–4:30] WHEN — next steps  *[your face or the dashboard]*

> "In a real rollout, I'd add four things. One: connect it to live alerts — like
> Dependabot or a security scanner — instead of a manual scan. Two: tune the
> instructions for each repository. Three: when Devin flags something for a
> human, open a Jira or Linear ticket automatically. Four: auto-merge the small,
> safe upgrades when tests pass, and keep humans for the big ones. The code is
> already built for this.
>
> That's Sentinel. It turns a constant drain on senior engineers into a
> dashboard a leader checks once a day. Thanks."
