import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Un solo .env en la raíz del monorepo
  envDir: '..',
  server: {
    port: 3000,
    host: true
  }
})
