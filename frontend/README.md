# Vaeda — Frontend

React + Vite frontend for Vaeda. For the full project picture
(features, architecture, safety design principles, API reference),
see the [root README](../README.md) — this file only covers
frontend-specific development details.

## Stack

- **React 19** + **Vite** — app shell & bundling
- **Tailwind CSS v4** — styling, via the CSS-first `@theme` config (`src/index.css`)
- **shadcn/ui-style primitives** (hand-rolled on Radix UI) — `src/components/ui`
- **React Router v7** — routing
- **Axios** — API client
- **Leaflet + react-leaflet** — the SOS page's nearby-hospitals map
- **qrcode.react** — the SOS page's emergency QR code
- **vite-plugin-pwa** — installable, offline-first app shell (see the
  root README's "Emergency / SOS" section for what's cached and why)
- **lucide-react** — icons

## Getting started

```bash
npm install
npm run dev       # http://localhost:5173
npm run build      # production build -> dist/
npm run preview    # preview the production build locally
npm run lint        # oxlint
```

By default the app talks to the deployed backend at
`https://mediassist-3jpl.onrender.com`. To point at a local backend
during development, copy `.env.example` to `.env` and set
`VITE_API_BASE_URL`.

## Folder structure

```
src/
  api/              Axios instance + one file per backend resource
  components/
    ui/             Reusable primitives (Button, Card, Input, Dialog, Select...)
    layout/         AppShell, Sidebar, Topbar
    common/         Logo, PulseLine (brand motif)
    dashboard/      Dashboard-specific components
    symptom/        Symptom analysis form, image upload, follow-up chat
    passport/       Health Passport form + document upload
    sos/            Nearby-hospitals map
    history/        Insights charts (severity trend, top conditions)
  context/          AuthContext — JWT session, stores user_id/name/email/role
  hooks/            useApi, useVoiceInput, useOnlineStatus
  pages/            One file per screen, wired to routes in App.jsx
  constants/routes.js   Single source of truth for paths
  lib/utils.js      cn() classname helper
public/icons/       PWA app icons (generated from pulse.svg)
```

## Environment variables

See `.env.example`. `VITE_ADMIN_USER_IDS` controls whether the Admin
Analytics link appears in the sidebar — this is a **UI convenience
only**, not a security boundary; the real access control is the
backend's role check.

## Design system

- **Colors**: Primary (jade) `#0F6B5C`, Danger `#C22F3A`, Background
  (porcelain) `#FBFAF7`, ink `#0A0F1A`, plus Success/Warning/Neutral
  tokens — CSS variables in `src/index.css` under `@theme`.
- **Type**: Fraunces (headings/display) + Inter (body/UI) + JetBrains
  Mono (data).
- **Signature element**: an animated "vitals pulse" ECG-style line
  (`src/components/common/PulseLine.jsx`).

## Screens

All routes are defined in `src/constants/routes.js` and wired in
`src/App.jsx`. Most have a sidebar nav entry (`src/components/layout/Sidebar.jsx`)
except `/admin/analytics`, which is intentionally direct-URL-only.
