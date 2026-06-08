import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "0.0.0.0",
    port: 5555,
    proxy: {
      "/api": {
        target: "http://localhost:5556",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:5556",
        ws: true,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 5555,
  },
});