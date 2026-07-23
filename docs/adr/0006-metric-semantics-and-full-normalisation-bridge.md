# Metric semantics and a full Reported-to-Normalised EBITDA bridge

## Metric semantics (verified against the data)

- **Revenue** = sum of `Sales` line items (positive).
- **Gross Profit** = Sales + Cost of Goods Sold (COGS stored negative).
- **Opex** = sum of the `Opex` branch (negative).
- **Reported EBITDA** = sum of all signed amounts = Gross Profit + Opex.
- **Margins** = the metric divided by Revenue.
- **FY** = calendar year (per the brief).

These reproduce the headline: AU EBITDA margin 15.7%→19.7% (FY21→FY24); NZ 15.5%→9.9%.

## Analytical scope

The five required views (FY EBITDA by entity, FY revenue by entity, monthly revenue/opex
trends, seasonality, cost-structure) plus a capped value-add set, each tied to a finding:
EBITDA-margin trend by entity, product-mix revenue analysis, and the normalisation bridge.
Scope is capped here to avoid creep.

## Normalisation: full bridge, not flag-only

We compute a **Normalised EBITDA** per entity/year and render an explicit **EBITDA Bridge**
(waterfall): Reported EBITDA → add back the one-off Sep-2024 AU restructuring cost → remove
the non-recurring May-2024 Smart Security promo revenue → Normalised EBITDA, with the
sustained Oct-2024 salary run-rate reset noted but not adjusted out.

The exact figures are confirmed in the data (AU Salaries & Wages: ~-1.05M/mo baseline,
-1.60M one-off Sep, -0.83–0.94M sustained from Oct; Smart Home Devices: ~625k→900k May
promo bump reverting toward ~790k). Each adjustment is a defensible position the LLM
justifies against the board narrative, with the number originating in Python and passing
the guardrail.

Considered and rejected: flag-only (surface the items without recomputing a normalised
figure). Rejected because the adjusted-earnings number is the highest-value diligence
artifact and the inputs are already confirmed. Accepted cost: a normalisation engine plus a
waterfall chart, and taking explicit positions on each adjustment.
