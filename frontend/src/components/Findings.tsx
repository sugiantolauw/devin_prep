import { useState } from "react";
import { Finding, FindingsPayload, regenerateFindings } from "../api";
import { money } from "../format";
import { C, entityColor, MATERIALITY } from "../theme";

function Chip({ text, color, bg }: { text: string; color: string; bg: string }) {
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        color,
        background: bg,
        borderRadius: 6,
        padding: "2px 8px",
      }}
    >
      {text}
    </span>
  );
}

function Card({ f }: { f: Finding }) {
  const mat = MATERIALITY[f.materiality] ?? C.muted;
  return (
    <div style={{ border: `1px solid ${C.line}`, borderRadius: 10, padding: "14px 16px" }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Chip text={f.materiality} color="#fff" bg={mat} />
        <Chip text={f.category} color={C.navy} bg={C.ice} />
        <Chip text={f.entity} color="#fff" bg={entityColor(f.entity)} />
        {f.dollar_impact != null && (
          <span style={{ fontSize: 11.5, color: C.muted, marginLeft: "auto" }}>
            impact ≈ {money(Math.abs(f.dollar_impact))}
          </span>
        )}
      </div>
      <h4 style={{ margin: "10px 0 6px", fontSize: 14.5, color: C.ink }}>{f.title}</h4>
      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: "#2c3040" }}>{f.observation}</p>
      <div style={{ marginTop: 10 }}>
        <div style={{ fontSize: 11.5, fontWeight: 600, color: C.muted }}>
          Questions for management
        </div>
        <ul style={{ margin: "4px 0 0", paddingLeft: 18, fontSize: 12.5, color: "#2c3040" }}>
          {f.management_questions.map((q, i) => (
            <li key={i} style={{ marginBottom: 3 }}>
              {q}
            </li>
          ))}
        </ul>
      </div>
      <div style={{ marginTop: 8, fontSize: 11, color: C.muted }}>
        Grounded in {f.evidence.metric_ids.length} metric
        {f.evidence.metric_ids.length === 1 ? "" : "s"} · {f.evidence.claim_ids.length} board-paper
        claim{f.evidence.claim_ids.length === 1 ? "" : "s"}
        {f.evidence.claim_ids.length > 0 && ` (${f.evidence.claim_ids.join(", ")})`}
      </div>
    </div>
  );
}

export function Findings({ initial }: { initial: FindingsPayload }) {
  const [data, setData] = useState(initial);
  const [busy, setBusy] = useState(false);

  const regen = async () => {
    setBusy(true);
    try {
      setData(await regenerateFindings());
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      style={{
        gridColumn: "1 / -1",
        background: C.panel,
        border: `1px solid ${C.line}`,
        borderRadius: 12,
        padding: "18px 20px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
        <h3 style={{ margin: 0, fontSize: 16, color: C.ink }}>Key diligence findings</h3>
        <span style={{ fontSize: 11.5, color: C.muted }}>
          source: {data.source} · {data.guardrail.checked} figures guardrail-checked ·{" "}
          {data.dropped} dropped
        </span>
        <button
          onClick={regen}
          disabled={busy}
          style={{
            marginLeft: "auto",
            fontSize: 12.5,
            padding: "6px 14px",
            borderRadius: 8,
            border: `1px solid ${C.navy}`,
            background: busy ? C.line : C.navy,
            color: "#fff",
            cursor: busy ? "default" : "pointer",
          }}
        >
          {busy ? "Regenerating…" : "Regenerate analysis"}
        </button>
      </div>
      <p style={{ margin: "0 0 14px", fontSize: 12.5, color: C.muted }}>
        Ranked by materiality. Every figure is computed in Python and verified against the
        Evidence Pack before display — the LLM narrates, it never does the arithmetic.
      </p>
      <div style={{ display: "grid", gap: 12 }}>
        {data.findings.map((f) => (
          <Card key={f.finding_id} f={f} />
        ))}
      </div>
    </section>
  );
}
