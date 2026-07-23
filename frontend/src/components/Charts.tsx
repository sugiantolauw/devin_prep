import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CostRow, FYRow, MonthlyRow, ProductRow, SeasonRow } from "../api";
import { money, MONTHS, pct } from "../format";
import { C } from "../theme";

const YEARS = [2021, 2022, 2023, 2024];
const axis = { fontSize: 12, fill: C.muted };
const grid = <CartesianGrid stroke={C.line} vertical={false} />;
const mMoney = (v: number) => money(v);
const mPct = (v: number) => pct(v);

export function MarginTrend({ fy }: { fy: FYRow[] }) {
  const data = YEARS.map((y) => ({
    fy: y,
    AU: fy.find((r) => r.entity === "AU" && r.fy === y)!.ebitda_margin_pct,
    NZ: fy.find((r) => r.entity === "NZ" && r.fy === y)!.ebitda_margin_pct,
  }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ left: 4, right: 8, top: 6 }}>
        {grid}
        <XAxis dataKey="fy" tick={axis} />
        <YAxis tick={axis} unit="%" width={44} />
        <Tooltip formatter={mPct as never} />
        <Legend />
        <Line type="monotone" dataKey="AU" stroke={C.au} strokeWidth={2.5} dot={{ r: 3 }} />
        <Line type="monotone" dataKey="NZ" stroke={C.nz} strokeWidth={2.5} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function EntityBars({ fy, field }: { fy: FYRow[]; field: "ebitda" | "revenue" }) {
  const data = YEARS.map((y) => ({
    fy: y,
    AU: fy.find((r) => r.entity === "AU" && r.fy === y)![field],
    NZ: fy.find((r) => r.entity === "NZ" && r.fy === y)![field],
  }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ left: 4, right: 8, top: 6 }}>
        {grid}
        <XAxis dataKey="fy" tick={axis} />
        <YAxis tick={axis} tickFormatter={mMoney} width={54} />
        <Tooltip formatter={mMoney as never} />
        <Legend />
        <Bar dataKey="AU" fill={C.au} radius={[3, 3, 0, 0]} />
        <Bar dataKey="NZ" fill={C.nz} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export const EntityEbitda = ({ fy }: { fy: FYRow[] }) => <EntityBars fy={fy} field="ebitda" />;
export const EntityRevenue = ({ fy }: { fy: FYRow[] }) => <EntityBars fy={fy} field="revenue" />;

export function MonthlyTrend({ monthly }: { monthly: MonthlyRow[] }) {
  const data = monthly
    .filter((r) => r.entity === "Group")
    .sort((a, b) => a.period.localeCompare(b.period))
    .map((r) => ({ period: r.period, Revenue: r.revenue, Opex: r.opex }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ left: 4, right: 8, top: 6 }}>
        {grid}
        <XAxis dataKey="period" tick={{ ...axis, fontSize: 9 }} interval={5} />
        <YAxis tick={axis} tickFormatter={mMoney} width={54} />
        <Tooltip formatter={mMoney as never} />
        <Legend />
        <Line type="monotone" dataKey="Revenue" stroke={C.au} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Opex" stroke={C.amber} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function Seasonality({ season }: { season: SeasonRow[] }) {
  const data = MONTHS.slice(1).map((m, i) => ({
    month: m,
    AU: season.find((r) => r.entity === "AU" && r.month === i + 1)?.seasonal_index ?? 0,
    NZ: season.find((r) => r.entity === "NZ" && r.month === i + 1)?.seasonal_index ?? 0,
  }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ left: 4, right: 8, top: 6 }}>
        {grid}
        <XAxis dataKey="month" tick={{ ...axis, fontSize: 10 }} />
        <YAxis tick={axis} domain={[0.8, 1.3]} width={40} />
        <Tooltip formatter={((v: number) => v.toFixed(2)) as never} />
        <Legend />
        <Bar dataKey="AU" fill={C.au} radius={[2, 2, 0, 0]} />
        <Bar dataKey="NZ" fill={C.nz} radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CostStructure({ cost }: { cost: CostRow[] }) {
  const data = cost
    .filter((r) => r.entity === "AU" && r.fy === 2024)
    .sort((a, b) => b.share_pct - a.share_pct)
    .map((r) => ({ name: r.cost_name, share: r.share_pct }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(240, data.length * 22)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <XAxis type="number" tick={axis} unit="%" />
        <YAxis type="category" dataKey="name" tick={{ ...axis, fontSize: 10 }} width={132} />
        <Tooltip formatter={mPct as never} />
        <Bar dataKey="share" fill={C.navy} radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ProductMix({ product }: { product: ProductRow[] }) {
  const products = [...new Set(product.map((r) => r.product))];
  const data = products.map((p) => ({
    product: p,
    AU: product.find((r) => r.entity === "AU" && r.fy === 2024 && r.product === p)?.revenue ?? 0,
    NZ: product.find((r) => r.entity === "NZ" && r.fy === 2024 && r.product === p)?.revenue ?? 0,
  }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ left: 4, right: 8, top: 6 }}>
        {grid}
        <XAxis dataKey="product" tick={{ ...axis, fontSize: 9 }} />
        <YAxis tick={axis} tickFormatter={mMoney} width={54} />
        <Tooltip formatter={mMoney as never} />
        <Legend />
        <Bar dataKey="AU" stackId="a" fill={C.au} />
        <Bar dataKey="NZ" stackId="a" fill={C.nz}>
          {data.map((_, i) => (
            <Cell key={i} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
