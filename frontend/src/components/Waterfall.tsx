import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Bridge } from "../api";
import { money } from "../format";
import { C } from "../theme";

function shortLabel(label: string): string {
  const l = label.toLowerCase();
  if (l.includes("reported")) return "Reported";
  if (l.includes("restructuring") || l.includes("one-off")) return "One-off add-back";
  if (l.includes("promo")) return "Promo removal";
  return label.split(" ").slice(0, 2).join(" ");
}

export function Waterfall({ bridge }: { bridge: Bridge }) {
  type Row = { name: string; base: number; value: number; kind: "total" | "up" | "down" };
  const rows: Row[] = [];

  rows.push({ name: "Reported", base: 0, value: bridge.reported_ebitda, kind: "total" });
  let prev = bridge.reported_ebitda;
  for (const step of bridge.steps.slice(1)) {
    const cur = step.running;
    rows.push({
      name: shortLabel(step.label),
      base: Math.min(prev, cur),
      value: Math.abs(step.delta),
      kind: step.delta >= 0 ? "up" : "down",
    });
    prev = cur;
  }
  rows.push({ name: "Normalised", base: 0, value: bridge.normalised_ebitda, kind: "total" });

  const color = (k: Row["kind"]) => (k === "total" ? C.navy : k === "up" ? C.up : C.down);
  const min = Math.min(...rows.map((r) => r.base));
  const max = Math.max(...rows.map((r) => r.base + r.value));

  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={rows} margin={{ left: 4, right: 8, top: 18 }}>
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: C.muted }} interval={0} />
          <YAxis
            tick={{ fontSize: 11, fill: C.muted }}
            domain={[Math.floor(min * 0.98), Math.ceil(max * 1.02)]}
            tickFormatter={money}
            width={56}
          />
          <Tooltip formatter={((v: number) => money(v)) as never} />
          <Bar dataKey="base" stackId="s" fill="transparent" />
          <Bar dataKey="value" stackId="s" radius={[3, 3, 0, 0]}>
            {rows.map((r, i) => (
              <Cell key={i} fill={color(r.kind)} />
            ))}
            <LabelList
              dataKey="value"
              position="top"
              formatter={((v: number) => money(v)) as never}
              style={{ fontSize: 10, fill: C.ink }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {bridge.noted_items.map((n, i) => (
        <p key={i} style={{ fontSize: 11.5, color: C.muted, margin: "6px 0 0" }}>
          <strong style={{ color: C.amber }}>Noted, not adjusted:</strong> {n.description}
        </p>
      ))}
    </div>
  );
}
