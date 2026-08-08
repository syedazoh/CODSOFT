import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // bind 0.0.0.0 so the dev server is reachable from outside a container
    port: 5173,
    proxy: {
      // Backend routes are already mounted under /api/*, so no path rewrite here —
      // stripping the prefix would 404 against the real FastAPI routes.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})