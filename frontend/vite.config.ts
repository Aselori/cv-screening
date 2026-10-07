import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// En desarrollo, las rutas de la API se envían al servidor FastAPI (puerto 8000).
const api = { target: "http://127.0.0.1:8000", changeOrigin: true };

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/vacancies": api, "/model": api } },
});
