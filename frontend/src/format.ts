export function money(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  const a = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (a >= 1e9) return `${sign}$${(a / 1e9).toFixed(2)}bn`;
  if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(2)}m`;
  if (a >= 1e3) return `${sign}$${(a / 1e3).toFixed(0)}k`;
  return `${sign}$${a.toFixed(0)}`;
}

export function pct(v: number | null | undefined, dp = 1): string {
  if (v === null || v === undefined) return "—";
  return `${v.toFixed(dp)}%`;
}

export const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
