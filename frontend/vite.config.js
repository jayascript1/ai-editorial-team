import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // Ensure environment variables are available
    'process.env': process.env
  },
  build: {
    // Ensure compatibility with older browsers including Safari
    target: 'es2015',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom']
        }
      }
    }
  },
  server: {
    // Add CORS headers for development
    cors: true
  }
})
