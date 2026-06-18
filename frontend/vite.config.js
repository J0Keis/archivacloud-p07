import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Fijamos el puerto 5173, que es el origen que el backend autoriza en
    // su configuración de CORS (FRONTEND_ORIGIN en el .env del backend).
    port: 5173,
  },
})
