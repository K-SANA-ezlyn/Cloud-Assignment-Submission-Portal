import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev server proxies /api -> FastAPI, so the SPA and the API
// appear same-origin in development (no CORS friction while coding).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
