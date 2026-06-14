import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Backend (Flask) varsayılan: 127.0.0.1:5055 — /api buraya proxy'lenir (CORS gerekmez)
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': { target: 'http://127.0.0.1:5055', changeOrigin: true },
    },
  },
})
