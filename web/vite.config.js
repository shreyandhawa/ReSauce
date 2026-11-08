import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `npm run dev` serves the page with live reload and forwards /api to the Python server
// (python -m app, port 8000 by default; set RESAUCE_API to use another address).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': process.env.RESAUCE_API || 'http://localhost:8000' } },
  build: { outDir: 'dist', emptyOutDir: true },
})
