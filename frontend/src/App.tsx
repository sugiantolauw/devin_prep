import { useEffect, useState } from "react";

// Phase 0 skeleton: confirms the Vite dev server proxies to FastAPI. The real dashboard
// (KPI headline, charts, EBITDA waterfall, ranked findings) lands in Phase 8.
export function App() {
  const [health, setHealth] = useState<string>("checking…");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setHealth(d.status))
      .catch(() => setHealth("unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>Apex — AI-Driven Financial Due Diligence</h1>
      <p>
        Backend health: <strong>{health}</strong>
      </p>
    </main>
  );
}
