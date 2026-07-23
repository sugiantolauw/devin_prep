# A single Finding object, ranked by materiality

Observations and management questions are not separate loose lists; they are two facets of
one object. We model a **Finding** as the single first-class output, carrying:

- `category` — fixed set: Profitability/Margin, Growth/Trend, Normalisation,
  Narrative-vs-Data Contradiction, Concentration/Dependency, Data Quality/Verifiability,
  Seasonality/Cost-structure
- `entity` / scope (AU, NZ, Group)
- `observation` — grounded statement citing `metric_id`s and values (guardrail-checked)
- `evidence` — numeric references plus the Board-Paper quote(s) reconciled
- `management_question`(s) — the specific asks that follow
- `materiality` — High / Medium / Low

Findings are **ranked by materiality**, and the UI leads with a "Key diligence findings"
list before per-view detail. Materiality is anchored to computed dollar impact wherever one
exists (e.g. the Sep-2024 one-off's EBITDA swing) and is otherwise a reasoned qualitative
call. This mirrors a real diligence report, where findings are always triaged, and it
surfaces the judgement the role is testing.

The Finding schema is also the LLM's structured-output contract and the guardrail's target.
Considered and rejected: flat findings grouped by category only (no ranking) — simpler but
reads as an untriaged data dump. The accepted cost is that materiality is an LLM judgement;
we mitigate by anchoring to dollar impact and keeping the numeric guardrail over every
figure.
