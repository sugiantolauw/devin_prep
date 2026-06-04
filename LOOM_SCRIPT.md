# Loom script — 5:00 hard cap

Goal: pitch Devin to a VP of Engineering + senior ICs. Show a working system,
defend the architecture, make the "why Devin" case. Practice once, record 2–3
takes. Have two windows ready: **terminal** (running `make serve`) and
**browser** on `/dashboard`, plus a tab on your **Superset fork's issues/PRs**.

---

### 0:00–0:40 · WHAT — the problem (talk over the dashboard, empty)

> "Every org running more than a handful of services drowns in dependency and
> security alerts. Today each one either rots in a backlog or eats a senior
> engineer's afternoon — read the advisory, bump the version, fix what breaks,
> run the tests, open a PR. Dependabot opens the PR but leaves the *fixing* to
> you. I built **Sentinel**: it makes that an unattended workflow, with Devin
> doing the actual engineering."

### 0:40–2:30 · HOW — live demo + architecture

1. **Trigger it.** In the terminal: `curl -X POST localhost:8000/scan`
   > "A dependency scan just filed four issues in our Superset fork and, for
   > each one, opened a Devin session via the API. Filing the issue *is* the
   > event."
2. **Show the orchestrator logs** scrolling — "session created, id mock-0001…".
   Point out the structured JSON logs.
3. **Cut to `/dashboard`.** Tasks in flight → flipping to *completed* with PR
   links. Call out the cards: **PRs opened, success rate, MTTR**.
   > "This is the answer to 'how does a leader know it's working' — live."
4. **Cut to your Superset fork** → the issues, and a Devin-opened **PR** with a
   real diff + passing checks. *(In the live recording use a real PR; the demo's
   mock PRs prove the wiring.)*
5. **Walk the architecture** (open `ARCHITECTURE.md` diagram, ~30s):
   > "Three layers — trigger, orchestrator, observability — with Devin as the
   > remediation primitive in the middle. Key calls: a *structured-output
   > contract* so I never scrape prose for the PR URL; *idempotency* at the
   > Devin call and the store so a double-delivered webhook can't double-spend;
   > and a `max_acu_limit` cost ceiling per issue. SQLite and one async poll
   > loop — no queue, no Redis — deliberately sized to the problem."

### 2:30–3:45 · WHY DEVIN — the uniquely-suited case

> "Strip Devin out and you have two options. Dependabot/Renovate: opens a PR you
> still have to *fix and review*. Or a human: expensive and slow. Devin sits in
> the gap neither fills — it reproduces the issue, writes the fix, runs the
> repo's tests, reads the failures, fixes the breakage, and hands back a
> reviewable PR. And when it's genuinely ambiguous — a major-version bump with
> blast radius — it doesn't guess; it escalates with its reasoning." *(Point to
> the `needs_human` row on the dashboard.)*
> "No other primitive does autonomous, test-validated remediation today."

### 3:45–5:00 · WHEN — next steps in a real engagement

> "To roll this out for a customer: (1) swap the demo scanner for their live
> Dependabot alerts or SCA tool; (2) per-repo prompt and guardrail tuning;
> (3) escalation that opens a Linear ticket on `needs_human`; (4) auto-merge
> low-risk patch bumps when CI is green, human review for majors; (5) Postgres +
> a dedicated worker as fan-out grows. The architecture already has the seams for
> all of it — clients are pluggable, the prompt is one tunable surface, and every
> session is tracked and costed."

---

**Timing tips:** the WHAT and the dashboard reveal are your hooks — don't rush
them. If you're over, cut the architecture walk to the three call-outs
(structured output, idempotency, cost ceiling). End on the business line:
> "This turns a recurring tax on senior engineers into a dashboard a leader
> checks once a day."
