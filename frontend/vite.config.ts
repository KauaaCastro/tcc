import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Configuração do Vite com proxy local para Core API Java (8080) e AI Engine Python (5000)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api/chat': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/ai': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
});
