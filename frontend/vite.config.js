import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['pulse.svg'],
      manifest: {
        name: 'Vaeda',
        short_name: 'Vaeda',
        description: 'Instant AI symptom analysis and a portable health passport.',
        theme_color: '#0F6B5C',
        background_color: '#0A0F1A',
        display: 'standalone',
        start_url: '/sos',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          {
            src: '/icons/icon-maskable-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        // Precaches the built app shell (JS/CSS/HTML) so the whole SPA -
        // including the SOS page - loads with zero network once visited.
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
        runtimeCaching: [
          {
            // The Health Passport GET is what makes the SOS page's
            // critical-info card (name, blood group, allergies,
            // emergency contact) work offline - NetworkFirst means it
            // always tries fresh data first, and only falls back to the
            // last-cached response when there's genuinely no network.
            // This is a DELIBERATE, narrow exception - see the next
            // rule for why almost nothing else gets this treatment.
            urlPattern: ({ url, request }) =>
              request.method === 'GET' && /\/passport\/[^/]+$/.test(url.pathname),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'vaeda-passport-cache',
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 4, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            // Nearby-hospitals results are explicitly NEVER cached.
            // Serving a stale hospital location as if it were current
            // during an actual emergency is a worse failure mode than
            // just failing visibly - the frontend shows a clear
            // "you're offline" state instead (see SOS.jsx). Same
            // reasoning as this project's existing "don't fabricate
            // certainty" stance elsewhere.
            urlPattern: ({ url }) => url.pathname.includes('/emergency/nearby-hospitals'),
            handler: 'NetworkOnly',
          },
          {
            // Everything else API-shaped (auth, analyze, history,
            // reminders, drug interactions, etc.) also stays
            // NetworkOnly - none of it is safe or meaningful to serve
            // from a stale cache, and most of it mutates data anyway.
            urlPattern: ({ url }) =>
              [
                '/auth/',
                '/analyze',
                '/history/',
                '/reminders',
                '/drug-interactions/',
                '/rag-review',
                '/documents',
              ].some((p) => url.pathname.includes(p)),
            handler: 'NetworkOnly',
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
})
