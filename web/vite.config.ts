import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Allow raw-importing the real source files from the repo root so the
// "Codex" page exhibits our actual code (not a GitHub embed). Vite inlines
// these at build time, so the production bundle is fully self-contained.
export default defineConfig({
  base: "/",
  plugins: [react()],
  server: {
    host: true,
    fs: { allow: [".."] },
  },
});
