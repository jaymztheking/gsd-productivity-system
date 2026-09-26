import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev proxy attaches the API token the same way ui/nginx.conf.template
// does in production, so local development exercises the same code path and
// the browser never holds the secret in either environment.
const apiToken = process.env.API_TOKEN ?? "";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: "http://api:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
        headers: apiToken ? { "X-API-Token": apiToken } : undefined,
      },
    },
  },
});
