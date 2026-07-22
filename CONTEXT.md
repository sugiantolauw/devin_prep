# Apex Diligence System

An AI-driven financial due diligence tool. It analyses Apex Electronics' structured
income-statement data alongside unstructured Board Papers, and produces grounded
observations, insights, and management questions for a diligence team.

## Language

**Entity**:
A reporting unit of the company whose financials are tracked separately. There are
exactly two: Apex Electronics AU and Apex Electronics NZ.
_Avoid_: subsidiary, business unit, company

**Financial Year (FY)**:
A reporting year. Per the brief, calendar years are treated as reported financial
years — FY2023 means Jan–Dec 2023.
_Avoid_: fiscal year, reporting period

**Line Item**:
The lowest level of the income-statement hierarchy (e.g. Components, Salaries & Wages,
Laptops). Each row of the source data is one line item for one entity for one month.
_Avoid_: account, category, GL code

**EBITDA Hierarchy**:
The fixed roll-up in the source data: `Income Statement → EBITDA → {Gross Profit, Opex}
→ category → line item`. Sales and Cost of Goods Sold roll into Gross Profit; the
remaining categories are Opex.
_Avoid_: chart of accounts, tree

**Evidence Pack**:
The structured set of pre-computed figures (aggregates, margins, trends, normalisation
candidates) handed to the LLM. The LLM narrates from this pack; it never computes
numbers itself.
_Avoid_: context, prompt data, facts blob

**Guardrail** (numeric guardrail):
A deterministic post-check that extracts every number in an LLM-generated Observation or
Management Question and verifies it exists in the Evidence Pack within rounding tolerance.
Any unmatched number causes the item to be rejected or flagged. Numbers are emitted by the
LLM in canonical form to keep the check reliable.
_Avoid_: validator, checker, filter

**Customer Concentration**:
The share of an entity's revenue dependent on a single customer/reseller. The FY2023
Board Paper states ~one third of NZ FY2022 channel revenue ran through one reseller
(Security Tech Inc.). This is a narrative claim that the structured data cannot verify —
the P&L breaks revenue down by product line, not by customer.
_Avoid_: customer risk, key account exposure

**Observation**:
A grounded statement about financial performance, a trend, an anomaly, or a structural
shift, each tied to specific figures from the Evidence Pack.
_Avoid_: finding, note, comment

**Management Question**:
A specific, evidence-grounded question a diligence analyst would put to company
management, arising from an Observation.
_Avoid_: query, ask, follow-up

**Anomaly**:
A point or stretch in a series that departs materially from its seasonal/run-rate
baseline — an outlier, a structural break (a sustained level shift), or a spike. Detected
deterministically in Python; it is a *candidate* signal, not yet an explained finding.
_Avoid_: outlier (that is only one kind), blip, deviation

**Reconciliation**:
The LLM step that matches a detected numeric Anomaly to a Board-Paper explanation, and
flags where the data and the narrative — or two Board Papers — disagree. A Normalisation
is only surfaced when a numeric Anomaly and a narrative statement both support it.
_Avoid_: matching, linking, correlation

**Normalisation**:
An adjustment to reported financials to remove one-off or non-recurring effects so the
underlying run-rate is visible. Known candidates: the one-off Sep-2024 AU restructuring
cost, and the temporary May-2024 Smart Security revenue spike.
_Avoid_: adjustment, add-back (add-back is one *type* of normalisation), restatement
