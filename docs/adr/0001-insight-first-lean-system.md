# Insight-first analysis on a deliberately lean system

The brief specifies the stack (Python core, React UI, any LLM provider) as constraints
but grades the output: "numerically accurate… observations/questions [that] will form
the basis of a due diligence report." The dataset reinforces this — two Board Papers
that contradict each other on NZ leadership stability, and a FY2024 paper that names the
exact one-off (Sep restructuring) and non-recurring (May Smart Security spike) items to
normalise.

We therefore optimise for **diligence-insight quality on a clean but modest system**,
rather than for AI-engineering sophistication. The system is real and end-to-end, but we
deliberately avoid heavyweight machinery (vector DB, RAG pipeline, eval harness) that the
two short documents do not warrant and that would read as missing the point. Marginal
effort goes to grounding, catching the cross-document contradiction, and doing the
normalisations properly.

Considered and rejected: an engineering-showcase build (retrieval, embeddings, guardrail
evals as the centrepiece). Rejected because the brief rewards the analyst's output, not
the platform, for a two-document corpus.
