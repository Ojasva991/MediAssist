# MediAssist AI — Frontend

A React + Vite frontend for the MediAssist AI healthcare backend, built for a 24-hour hackathon.

## Stack

- **React 19** + **Vite** — app shell & bundling
- **Tailwind CSS v4** — styling, via the CSS-first `@theme` config (see `src/index.css`)
- **shadcn/ui-style primitives** (hand-rolled on Radix UI) — Button, Card, Dialog, Select, etc. in `src/components/ui`
- **React Router v7** — routing
- **Axios** — API client
- **lucide-react** — icons

## Getting started

```bash
npm install
npm run dev       # http://localhost:5173
npm run build      # production build -> dist/
npm run preview    # preview the production build locally
```

By default the app talks to the deployed backend at
`https://mediassist-3jpl.onrender.com`. To point at a local backend during
development, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

## Folder structure

```
src/
  api/              Axios instance + one file per resource (analysis.js, passport.js)
  components/
    ui/             Reusable shadcn-style primitives (Button, Card, Input, Dialog, Select...)
    layout/         AppShell, Sidebar, Topbar
    common/         Logo, PulseLine (brand motif)
    dashboard/      Dashboard-specific components
    symptom/        Symptom analysis form + result components
    passport/       Health Passport form + summary components
  context/          AuthContext (local session)
  hooks/            useApi — generic loading/error/data wrapper for API calls
  pages/            One file per screen, wired to routes in App.jsx
  constants/        routes.js — single source of truth for paths
  lib/utils.js      cn() classname helper
```

## Screens implemented

| Screen | Route | Notes |
|---|---|---|
| Splash | `/` | Brief branded loading screen, redirects based on session |
| Login | `/login` | Local session (name + email) — no backend auth endpoint in spec |
| Dashboard | `/dashboard` | Hub with quick actions to the 3 core features |
| Symptom Analysis | `/analysis` | Form -> `POST /analyze` |
| AI Result | `/analysis/result` | Renders the analysis response; defensively parses a couple of likely field-name variants |
| Health Passport | `/passport` | `GET` / `PUT` / `DELETE` on `/passport/{user_id}` |
| SOS | `/sos` | Emergency-optimized view of passport data + tap-to-call |

## API integration notes — please read

The exact response schema for `POST /analyze` and the request/response shape
for `/passport/{user_id}` weren't available when this was built (the deployed
Swagger UI is JS-rendered and `/openapi.json` wasn't reachable from the build
sandbox). Everything is wired against the field names implied by the spec,
isolated to two files so it's a quick fix if the real backend differs:

- **`src/api/analysis.js`** — documents the assumed `/analyze` request/response shape in a comment above `analyzeSymptoms()`.
- **`src/api/passport.js`** — documents the assumed passport object shape.
- **`src/pages/AnalysisResult.jsx`** — reads a few likely field-name variants (`possible_conditions`/`conditions`/`predictions`, `severity`/`risk_level`, etc.) so a minor mismatch won't crash the result screen while you finalize the actual field names.

**Before the demo:** open `/docs` on the deployed backend, confirm the real
request/response bodies for the three endpoints, and adjust the field names
in the two API files above if needed.

## Design system

- **Colors**: Primary `#2563EB`, Danger `#DC2626`, Background `#F8FAFC` (per spec), plus Success/Warning/Ink/Border tokens — defined as CSS variables in `src/index.css` under `@theme`.
- **Type**: Lexend (headings) + Inter (body/UI).
- **Signature element**: an animated "vitals pulse" ECG-style line (`src/components/common/PulseLine.jsx`) used in the splash, login, dashboard hero, and SOS states to reinforce the "live health" concept without generic AI-app decoration.

## Known gaps / good next steps for the team

- No auth endpoint exists in the spec, so login is local-only (persisted in `localStorage`). Swap `AuthContext.login()` for a real call if the backend adds one.
- Symptom analysis history isn't persisted — each analysis is view-once (passed via router state). Worth adding a history list if the backend supports it.
- SOS defaults to India's unified emergency number (112). Change `EMERGENCY_NUMBER` in `src/pages/SOS.jsx` if targeting a different region for the demo.
