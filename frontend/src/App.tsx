import { Bridge, FindingsPayload, Metrics, useApi } from "./api";
import {
  CostStructure,
  EntityEbitda,
  EntityRevenue,
  MarginTrend,
  MonthlyTrend,
  ProductMix,
  Seasonality,
} from "./components/Charts";
import { Findings } from "./components/Findings";
import { KpiRow } from "./components/KpiRow";
import { Panel } from "./components/ui";
import { Waterfall } from "./components/Waterfall";
import { C } from "./theme";

export function App() {
  const metrics = useApi<Metrics>("/api/metrics");
  const bridges = useApi<Bridge[]>("/api/bridges");
  const findings = useApi<FindingsPayload>("/api/findings");

  const err = metrics.error || bridges.error || findings.error;
  if (err) {
    return (
      <Shell>
        <p style={{ color: C.down }}>
          Could not reach the API ({err}). Start the backend: <code>uv run uvicorn app.main:app</code>
        </p>
      </Shell>
    );
  }
  if (!metrics.data || !bridges.data || !findings.data) {
    return (
      <Shell>
        <p style={{ color: C.muted }}>Loading…</p>
      </Shell>
    );
  }

  const m = metrics.data;
  return (
    <Shell>
      <div style={{ marginBottom: 16 }}>
        <KpiRow fy={m.fy_summary} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
        <Findings initial={findings.data} />

        {bridges.data.map((b) => (
          <Panel
            key={b.entity}
            title={`${b.entity} — Reported → Normalised EBITDA (FY2024)`}
            subtitle="One-off added back; non-recurring promo removed; sustained reset noted, not adjusted."
          >
            <Waterfall bridge={b} />
          </Panel>
        ))}

        <Panel title="EBITDA margin by entity" subtitle="The headline: AU expands, NZ compresses.">
          <MarginTrend fy={m.fy_summary} />
        </Panel>
        <Panel title="Monthly revenue & opex (Group)" subtitle="Note the May-2024 promo spike.">
          <MonthlyTrend monthly={m.monthly} />
        </Panel>
        <Panel title="FY EBITDA by entity">
          <EntityEbitda fy={m.fy_summary} />
        </Panel>
        <Panel title="FY revenue by entity">
          <EntityRevenue fy={m.fy_summary} />
        </Panel>
        <Panel title="Seasonality (revenue index by month)" subtitle="1.0 = an average month.">
          <Seasonality season={m.seasonality} />
        </Panel>
        <Panel title="Product mix — revenue FY2024">
          <ProductMix product={m.product_mix} />
        </Panel>
        <Panel title="AU cost structure FY2024" subtitle="Share of total cost by line." wide>
          <CostStructure cost={m.cost_structure} />
        </Panel>
      </div>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: "28px 24px 60px" }}>
      <header style={{ marginBottom: 18 }}>
        <h1 style={{ margin: 0, fontSize: 24, color: C.navy }}>
          Apex Electronics — AI-Driven Financial Due Diligence
        </h1>
        <p style={{ margin: "4px 0 0", fontSize: 13.5, color: C.muted }}>
          Numbers computed deterministically in Python; observations narrated by Claude under a
          numeric guardrail.
        </p>
      </header>
      {children}
    </main>
  );
}
