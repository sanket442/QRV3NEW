import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listen on all local IPs (needed for LAN access)
    port: 5173, // Standard Vite port
    strictPort: true,
  }
})
