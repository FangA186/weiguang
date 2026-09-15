import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
// Dev: the Vue SPA stays on :5173 and delegates HTTP API traffic to the
// cloud-provider adapter service on local :8080.
export default defineConfig({
    plugins: [vue()],
    server: {
        port: 5173,
        strictPort: true,
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8080",
                changeOrigin: true,
            },
        },
    },
    build: {
        outDir: "dist",
        emptyOutDir: true,
    },
});
