// Diligence palette — navy-led, echoing the enterprise slide.
export const C = {
  navy: "#1E2761",
  ink: "#1a1d26",
  panel: "#ffffff",
  bg: "#f5f6f8",
  line: "#e4e7ee",
  muted: "#6b7280",
  au: "#1C7293", // AU — teal
  nz: "#B85042", // NZ — terracotta
  group: "#8792b8",
  up: "#2C7A4B", // favourable
  down: "#C0492F", // unfavourable
  amber: "#E0952A",
  ice: "#CADCFC",
};

export const MATERIALITY: Record<string, string> = {
  High: "#C0492F",
  Medium: "#E0952A",
  Low: "#6b7280",
};

export const entityColor = (e: string) => (e === "AU" ? C.au : e === "NZ" ? C.nz : C.group);
