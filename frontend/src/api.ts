import { useEffect, useState } from "react";

export interface FYRow {
  entity: string;
  fy: number;
  revenue: number;
  cogs: number;
  gross_profit: number;
  opex: number;
  ebitda: number;
  ebitda_margin_pct: number;
  gross_margin_pct: number;
  revenue_yoy_pct: number | null;
  ebitda_yoy_pct: number | null;
}
export interface MonthlyRow {
  entity: string;
  fy: number;
  month: number;
  revenue: number;
  opex: number;
  ebitda: number;
  period: string;
}
export interface SeasonRow {
  entity: string;
  month: number;
  seasonal_index: number;
}
export interface CostRow {
  entity: string;
  fy: number;
  cost_name: string;
  cost: number;
  total: number;
  share_pct: number;
}
export interface ProductRow {
  entity: string;
  fy: number;
  product: string;
  revenue: number;
  total: number;
  share_pct: number;
}
export interface Metrics {
  fy_summary: FYRow[];
  monthly: MonthlyRow[];
  seasonality: SeasonRow[];
  cost_structure: CostRow[];
  product_mix: ProductRow[];
}
export interface BridgeStep {
  label: string;
  delta: number;
  running: number;
  item_id: string | null;
}
export interface NotedItem {
  label: string;
  description: string;
}
export interface Bridge {
  entity: string;
  fy: number;
  reported_ebitda: number;
  steps: BridgeStep[];
  normalised_ebitda: number;
  noted_items: NotedItem[];
}
export interface Finding {
  finding_id: string;
  category: string;
  entity: string;
  title: string;
  observation: string;
  evidence: { metric_ids: string[]; values: number[]; claim_ids: string[] };
  management_questions: string[];
  materiality: string;
  dollar_impact: number | null;
}
export interface FindingsPayload {
  source: string;
  dropped: number;
  findings: Finding[];
  guardrail: { checked: number; flagged: number };
}

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

export function useApi<T>(url: string): { data: T | null; error: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    getJSON<T>(url)
      .then((d) => live && setData(d))
      .catch((e) => live && setError(String(e)));
    return () => {
      live = false;
    };
  }, [url]);
  return { data, error };
}

export async function regenerateFindings(): Promise<FindingsPayload> {
  const r = await fetch("/api/findings/regenerate", { method: "POST" });
  if (!r.ok) throw new Error(`regenerate -> ${r.status}`);
  return r.json();
}
