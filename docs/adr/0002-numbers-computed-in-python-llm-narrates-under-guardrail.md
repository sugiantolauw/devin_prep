# Numbers computed in Python; the LLM narrates under a numeric guardrail

The brief's hard bar is numerical accuracy sufficient for a due diligence report. An LLM
doing its own arithmetic on the raw data will eventually produce a wrong figure, and one
wrong number is disqualifying. So fabrication must be structurally difficult, not merely
unlikely.

Decision, in four stages:

1. **Python computes every figure** the system displays — FY EBITDA/revenue by entity,
   margins, YoY, monthly trends, seasonality, cost-structure mix, and normalisation
   adjustments. This is the deterministic metrics layer.
2. The figures are assembled into a structured **Evidence Pack** handed to the LLM. The
   LLM may only reference numbers present in the pack; it never calculates.
3. The LLM returns **structured output** (JSON) where each Observation / Management
   Question carries the `metric_id`(s) and value(s) it cites. Charts and tables render
   from the Python layer, so visuals are correct by construction.
4. A **numeric guardrail** validates the LLM output: every number in the text must match
   a value in the Evidence Pack within tolerance, or the item is rejected/flagged.

Considered and rejected: citations-only (trust the LLM's structured references without
post-verification). Rejected because the guardrail is cheap (~30 lines) and converts an
accuracy *claim* into an enforced *property* — the most persuasive thing to show an
evaluator grading on numerical trustworthiness. The accepted cost is that the LLM must
emit numbers in canonical form so correct observations are not falsely flagged.
