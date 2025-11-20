import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const cacheControlPlugin = {
  name: 'cache-control-plugin',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      const url = req.url || ''
      const accept = req.headers['accept'] || ''
      if (url.endsWith('/index.html') || String(accept).includes('text/html')) {
        res.setHeader('Cache-Control', 'no-store, must-revalidate')
        res.setHeader('Pragma', 'no-cache')
        res.setHeader('Expires', '0')
      } else if (/\/assets\/.+\.[a-f0-9]{8}\./.test(url)) {
        res.setHeader('Cache-Control', 'public, max-age=31536000, immutable')
      } else {
        res.setHeader('Cache-Control', 'no-store')
      }
      next()
    })
  },
  configurePreviewServer(server) {
    server.middlewares.use((req, res, next) => {
      const url = req.url || ''
      const accept = req.headers['accept'] || ''
      if (url.endsWith('/index.html') || String(accept).includes('text/html')) {
        res.setHeader('Cache-Control', 'no-store, must-revalidate')
        res.setHeader('Pragma', 'no-cache')
        res.setHeader('Expires', '0')
      } else if (/\/assets\/.+\.[a-f0-9]{8}\./.test(url)) {
        res.setHeader('Cache-Control', 'public, max-age=31536000, immutable')
      } else {
        res.setHeader('Cache-Control', 'no-store')
      }
      next()
    })
  }
}

export default defineConfig({
  plugins: [react(), cacheControlPlugin],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})