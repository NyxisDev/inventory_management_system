// Quasar config for the public catalog (SSR mode).
// https://v2.quasar.dev/quasar-cli-vite/quasar-config-file
import { defineConfig } from '@quasar/app-vite'

export default defineConfig(() => ({
  // Pages load their data in preFetch, so it is in the server HTML.
  preFetch: true,

  boot: ['config', 'i18n', 'reveal'],

  css: ['app.scss'],

  extras: [],

  build: {
    target: {
      browser: ['es2022', 'firefox115', 'chrome115', 'safari15'],
      node: 'node22',
    },
    vueRouterMode: 'history',
    // Only the static demo build (npm run build:pages) sets a sub-path.
    publicPath: process.env.PAGES_BASE || '/',
  },

  devServer: {
    port: 9100,
    open: false,
    // In development the browser calls /api and /media on the dev server;
    // they are forwarded to the backend (only used when MOCK_API is off).
    proxy: {
      '/api': { target: process.env.API_URL || 'http://localhost:8000', changeOrigin: true },
      '/media': { target: process.env.API_URL || 'http://localhost:8000', changeOrigin: true },
    },
  },

  framework: {
    config: {
      dark: true,
      brand: {
        primary: '#ff8a00',
        secondary: '#2563eb',
        accent: '#ff8a00',
        dark: '#151d30',
        'dark-page': '#0b1121',
        positive: '#22c55e',
        negative: '#f87171',
        info: '#2563eb',
        warning: '#f59e0b',
      },
    },
    iconSet: 'svg-mdi-v7',
    plugins: ['Meta'],
  },

  animations: [],

  ssr: {
    prodPort: 3000,
    // The app is rendered on the server only; no PWA takeover.
    pwa: false,
    middlewares: ['seo', 'render'],
  },
}))
