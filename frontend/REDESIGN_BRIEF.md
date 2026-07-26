# Vaeda redesign — implementation brief

You've been given a zip of the Vaeda frontend (React 19 + Vite + Tailwind v4 +
shadcn-style primitives). A previous session already did **pass 1**: it
established a new design system (tokens, fonts, logo) and applied it to the
existing page structure by recoloring classNames. That pass is real and
working — don't redo it. Your job is **pass 2**: rebuild specific pages so
their actual layout, not just their colors, matches the approved mockups
described below, without fabricating data the backend doesn't provide.

Read this whole brief before touching code. Then read every file under
`src/` so you understand what already exists — most of pass 1 is good and
should be preserved as-is.

## Design system already in place — keep this

- `src/index.css` — `@theme` tokens: primary/jade `#0F6B5C`, danger `#C22F3A`,
  bg/porcelain `#FBFAF7`, ink `#0A0F1A`, plus `--color-abyss*` for dark
  surfaces and `--color-mist` for light neutral fills. Fonts: Fraunces
  (display), Inter (body/UI), JetBrains Mono (data/numbers).
- `src/components/common/Logo.jsx` — the mark: a single continuous stroke
  that is both a "V" and an ECG pulse (`polyline points="14,22 38,74 46,52
  53,80 60,52 86,22"`). Reuse this exact path anywhere the mark appears —
  don't redraw it.
- `src/components/layout/Sidebar.jsx` — already rebuilt as a dark
  `--color-abyss` panel with a jade left-border active state. This one is
  done; match its visual language elsewhere rather than changing it.
- `src/pages/Splash.jsx` and `src/pages/NotFound.jsx` — already ink
  backgrounds with the mono "404" / pulse mark. Done.

## The real gap: these pages were only recolored, not restructured

### 1. `src/pages/Login.jsx` and `src/pages/Signup.jsx`

Current: your original split-screen layout (dark hero panel left, form right)
just recolored to ink/jade. That's a legitimate direction and you can keep
it — OR rebuild as a **centered card on a full ink background** (the
approved mockup direction): logo mark + wordmark centered above a
`--color-abyss-soft` card, faint pulse-line running along the bottom of the
viewport as ambient texture, email/password fields styled dark
(`bg-[var(--color-abyss)]` inputs inside the card), jade "sign in" button,
divider, "create an account" link in jade. Preserve all existing validation
logic, error states, and the `useAuth` calls — this is a visual restructure
only, not a logic change. Pick one direction and apply it consistently to
both Login and Signup.

### 2. `src/pages/Dashboard.jsx`

The mockup shown to the user had a topbar with icon buttons, three stat
cards (a numeric "risk score" with a trend arrow, "last check-in", and
"passport status"), a pulse-line strip, and a recent-activity list. **Do not
build all of this literally — check what the backend actually supports
first:**

- `src/api/analysis.js` — `/analyze` returns `possible_conditions`,
  `severity` (LOW/MODERATE/HIGH/EMERGENCY enum, not a number),
  `recommended_action`, `sos_recommended`, `disclaimer`. There is **no
  numeric risk score** anywhere in the API. Do not invent one.
- `src/api/history.js` — only exposes a feedback POST endpoint. There is
  **no GET endpoint to list past analyses**, so a "recent activity" feed
  cannot be populated with real data as things stand.
- `src/api/passport.js` — `getPassport(userId)` is real and already used
  elsewhere in the app. Whether a passport exists/is complete **is** real
  data you can use.

Given that, do this instead:
- Keep the stat-card *visual pattern* (small porcelain cards, mono numbers,
  jade fill for the "good" one) but only populate cards with data that's
  actually available: e.g. "passport" card showing complete/incomplete
  (derived from `getPassport`), and if you want a third/fourth card, use
  something honestly derivable (e.g. severity of the most recent analysis
  *if* the user just ran one and it's in local/route state — don't invent a
  persisted history feature).
- If you want the recent-activity list and a real numeric trend, add a
  clearly-marked TODO comment noting it requires a new backend endpoint
  (e.g. `GET /history/{user_id}`) and stub it behind a feature flag or omit
  it rather than faking it with hardcoded fixture data that looks live.
- Rebuild the hero to include a topbar-style row (icon buttons for
  notifications/search are fine as inert UI if the backend has nothing
  behind them yet — but label them clearly as non-functional in a comment,
  or simply leave them out if you'd rather not ship dead buttons).
- Keep the existing `FeatureCard` quick-actions grid — it's fine, just
  restyle to match spacing/rhythm of the rest of the rebuild.

### 3. `src/pages/Passport.jsx` and `src/components/passport/PassportSummary.jsx`

Close to the mockup already (same info blocks: name/age, blood group badge,
allergies, chronic conditions, medications) but not pixel-matched — tighten
spacing, use the mono font for the blood-group badge and age number, add
hairline dividers between rows matching the Dashboard/SOS card style once
that's finalized.

### 4. `src/pages/SOS.jsx`

Structure already matches the mockup closely (emergency call block, info
list). Polish pass only: align padding/type scale with whatever you land on
for Dashboard/Passport so all authenticated pages feel like one system.

## Constraints — do not violate these

- Don't fabricate data or persisted features (fake "streaks", fake history,
  fake numeric scores) to make a screen look fuller. If a mockup implies
  data the backend doesn't have, either wire up a real backend change (out
  of scope unless you say otherwise) or simplify the UI to what's real.
- Don't change `src/api/*`, `src/context/AuthContext.jsx`, or any
  request/response shapes — this is a frontend visual/structural pass only.
- Preserve all existing behavior: loading states, error states, empty
  states, toasts, validation, the passport-autofill flow in
  `SymptomAnalysis.jsx`.
- Keep using the existing token names (`bg-primary`, `text-ink`,
  `border-border`, `var(--color-abyss)`, etc.) rather than introducing new
  hardcoded hex values, so the system stays cascade-driven from
  `index.css`.
- Run `npm install && npm run build` before handing back and confirm it's
  clean.

## What "done" looks like

Every authenticated page (Dashboard, Symptom Analysis, Analysis Result,
Passport, SOS) shares the same spacing rhythm, card style, and type scale.
Login/Signup share one deliberate direction. Nothing on screen implies data
that doesn't actually exist behind it. `npm run build` passes.
