# Code detects anomalies; the LLM reconciles them with the narrative

Normalisations and narrative findings must be genuinely *derived*, not hand-fed. Two
failure modes to avoid: (a) letting the LLM invent normalisation amounts (violates
ADR-0002), and (b) hardcoding the two known items (May-2024 revenue spike, Sep-2024
restructuring), which only looks like discovery.

Decision — a hybrid where **code detects and the LLM attributes**:

1. **Python detects anomalies** in each series (outliers, structural breaks / sustained
   run-rate shifts, spikes vs. a seasonal baseline) and computes the deterministic dollar
   impact of each candidate normalisation.
2. **The LLM extracts claims** from the Board Papers.
3. **The LLM reconciles**: it matches each detected numeric anomaly to a narrative
   explanation, and surfaces contradictions (e.g. FY2023 "NZ leadership stability
   restored" vs. FY2024 "3 GM changes in 18 months"). The number always originates in
   Python and must pass the guardrail.
4. **Both-sides rule**: a Normalisation is surfaced only when supported by *both* a
   detected numeric signal *and* a narrative statement. This double-grounding is itself
   part of the diligence story.

We adopt the full version with a genuine detector (not a simplified month-on-month rule),
because the generality is the demonstration of competence and the same detector must find
anomalies we did not anticipate. Considered and rejected: LLM-led detection (ungrounded
numbers) and hardcoded items (brittle, not real discovery).
