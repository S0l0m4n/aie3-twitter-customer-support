import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const DEV_API_TARGET = process.env.VITE_DEV_API_TARGET || 'http://localhost:8000';
const API_PATHS = ['/query', '/retrieve', '/generate', '/predict', '/health', '/docs', '/openapi.json', '/redoc'];

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: Object.fromEntries(
      API_PATHS.map((p) => [p, { target: DEV_API_TARGET, changeOrigin: true }]),
    ),
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});