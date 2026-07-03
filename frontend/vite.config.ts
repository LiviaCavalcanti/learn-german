import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // host: true → listen on 0.0.0.0 so your phone (LAN / Tailscale) can reach the dev server
    host: true,
    port: 5173,
  },
})
