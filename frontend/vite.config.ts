import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api to FastAPI so there is no CORS friction (ADR-0009).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
