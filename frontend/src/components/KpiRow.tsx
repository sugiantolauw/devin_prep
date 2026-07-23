import { FYRow } from "../api";
import { money, pct } from "../format";
import { C } from "../theme";

function Kpi({
  label,
  value,
  delta,
  good,
}: {
  label: string;
  value: string;
  delta: string;
  good: boolean;
}) {
  return (
    <div
      style={{
        background: C.panel,
        border: `1px solid ${C.line}`,
        borderRadius: 12,
        padding: "14px 18px",
        flex: "1 1 180px",
      }}
    >
      <div style={{ fontSize: 12.5, color: C.muted }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 700, color: C.ink, marginTop: 2 }}>{value}</div>
      <div style={{ fontSize: 12.5, color: good ? C.up : C.down, marginTop: 2 }}>{delta}</div>
    </div>
  );
}

export function KpiRow({ fy }: { fy: FYRow[] }) {
  const pick = (e: string, y: number) => fy.find((r) => r.entity === e && r.fy === y)!;
  const au21 = pick("AU", 2021);
  const au24 = pick("AU", 2024);
  const nz21 = pick("NZ", 2021);
  const nz24 = pick("NZ", 2024);
  const g24 = pick("Group", 2024);

  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      <Kpi
        label="Group revenue FY2024"
        value={money(g24.revenue)}
        delta={`EBITDA margin ${pct(g24.ebitda_margin_pct)}`}
        good
      />
      <Kpi
        label="AU EBITDA margin"
        value={pct(au24.ebitda_margin_pct)}
        delta={`▲ from ${pct(au21.ebitda_margin_pct)} (FY2021) — expanding`}
        good
      />
      <Kpi
        label="NZ EBITDA margin"
        value={pct(nz24.ebitda_margin_pct)}
        delta={`▼ from ${pct(nz21.ebitda_margin_pct)} (FY2021) — compressing`}
        good={false}
      />
      <Kpi
        label="NZ revenue FY2024"
        value={money(nz24.revenue)}
        delta={`▲ from ${money(nz21.revenue)} — revenue grows, margin falls`}
        good={false}
      />
    </div>
  );
}
