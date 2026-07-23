import { ReactNode } from "react";
import { C } from "../theme";

export function Panel({
  title,
  subtitle,
  children,
  wide,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <section
      style={{
        background: C.panel,
        border: `1px solid ${C.line}`,
        borderRadius: 12,
        padding: "18px 20px",
        gridColumn: wide ? "1 / -1" : "auto",
        minWidth: 0,
      }}
    >
      <h3 style={{ margin: "0 0 2px", fontSize: 15, color: C.ink }}>{title}</h3>
      {subtitle && <p style={{ margin: "0 0 12px", fontSize: 12.5, color: C.muted }}>{subtitle}</p>}
      {children}
    </section>
  );
}
