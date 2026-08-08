# Vaeda

**AI-assisted health triage, a portable Health Passport, and an
emergency toolkit — built to be honest about its own limits, not just
capable.**

> ⚠️ **Vaeda is not a diagnostic tool.** It estimates how urgent a set
> of symptoms is and suggests a next step. It never claims to know
> what disease someone has, every AI response carries a disclaimer,
> and a deterministic rule engine — not the AI — sets the safety floor
> that severity can never fall below.

- **Live app:** https://medi-assist-nu.vercel.app
- **Live API:** https://mediassist-3jpl.onrender.com (interactive docs
  at `/docs`)
- **Repo:** github.com/Ojasva991/MediAssist — the repo is still named
  `MediAssist`; the product itself is Vaeda. Renaming the repo is a
  hosting/GitHub action, not a code change, and hasn't been done.

For a detailed, running log of *how* this project got here — every
design decision, every bug caught, every deliberately-deferred
feature and why — see [`PROJECT_STATE.md`](./PROJECT_STATE.md). This
README is the "what it is today" picture; that file is the "how we
got here and what's next" one.

---

## What's actually in it

**Symptom analysis**
- Text-based triage (`POST /analyze`) — Gemini-powered, grounded by a
  deterministic keyword rule engine that sets a hard severity floor
  the AI can't downgrade below, plus a small hand-written RAG corpus
  for first-aid guidance.
- **Photo-based analysis** (`POST /analyze/image`) — upload a photo of
  a visible symptom (rash, wound, swelling). Runs under a *stricter*
  system prompt than text analysis (no reassuring language for
  anything resembling a skin lesion; medical scans like X-rays are
  explicitly declined, not interpreted).
- **Voice input** — dictate symptoms via the browser's built-in Web
  Speech API, no backend involved.
- **Follow-up chat** (`POST /analyze/follow-up`) — a real conversation
  thread after an analysis. The rule engine re-checks the *entire*
  conversation on every turn, so a red flag mentioned mid-chat still
  raises the severity floor even if the AI itself doesn't flag it.
- **Multilingual** — responds in whatever language the person writes
  in. Honestly caveated in the UI: the deterministic rule-engine floor
  is still English-keyword-only, so this is stated directly, not
  buried.
- **AI Gateway with automatic fallback** — Gemini first, then Groq
  (free tier) if Gemini fails, before falling through to the
  rule-engine-only response. Every attempt is logged for the admin
  dashboard.

**Health Passport**
- Core medical info (blood group, allergies, medications, chronic
  conditions, emergency contact), full CRUD, audit-logged.
- Medical document uploads (blood tests, imaging, prescriptions —
  5MB/file, 20/user, stored in Postgres).
- One-page doctor-facing PDF report export.

**History & insights**
- Every saved analysis, with a severity-over-time chart and a
  most-common-conditions chart (hand-rolled SVG, no charting library).
- Keyword-based symptom-recurrence detection.
- Thumbs up/down feedback on saved analyses.

**Reminders**
- Medication/follow-up reminders, one-time or repeating (daily/weekly).
- **Honestly scoped as in-app only** — no push notifications, no
  email, no SMS yet. Stated directly in the UI, not just a code
  comment.

**Drug interaction checker**
- Checks a list of medications against ~34 hand-curated,
  well-established interactions.
- **Deliberately makes zero AI calls** — pure deterministic name
  matching. A combination not flagged is explicitly *not* claimed
  safe, just not checked against a real database.

**Emergency / SOS**
- One-tap emergency calling + emergency contact, QR code encoding
  critical info for offline use by first responders.
- Nearby-hospital search via OpenStreetMap's Overpass API, with an
  interactive Leaflet map. Falls back across multiple Overpass mirrors
  automatically, and a zero-backend Google Maps search link as a
  last-resort guarantee that this feature can never fully fail.
- **Offline-first PWA** — installable, opens straight to the SOS page.
  Critical info (blood group, allergies, emergency contact) is cached
  and renders with zero network. Nearby-hospital results are
  deliberately *never* cached — showing a stale hospital location as
  current during a real emergency is worse than failing visibly.

**Caregiver / family mode**
- Separate accounts linked by a short invite code (not shared logins).
- Caregivers get read-only Health Passport/History access plus the
  ability to manage reminders on the patient's behalf — no edit access
  to the Passport itself. Revocable by the patient at any time.

**Admin**
- Real analytics dashboard — every number is a live query (users,
  analyses, severity breakdown, AI provider usage/fallback frequency,
  caregiver links, document storage, feedback ratio). Nothing
  estimated or fabricated; where something genuinely isn't tracked
  (API cost, image-analysis provider split), the dashboard says so.
- Real role-based access control (`users.role`), with a CLI bootstrap
  script for the first admin and self-service promotion after that.
- Hybrid-retrieval staging pipeline for the RAG corpus — ingest →
  human review → manual promotion, three separate deliberate gates
  before any externally-sourced guidance reaches the live corpus.

---

## Safety & design principles

A few things are consistent across the whole codebase, worth knowing
before extending it:

1. **The rule engine is the safety floor, not the AI.** Severity can
   be raised by the AI's judgment but never lowered below what the
   deterministic keyword engine decided.
2. **No fabricated data, anywhere.** If a metric or claim can't be
   backed by something real, it's either not shown or explicitly
   labeled as not tracked — see the admin dashboard's provider-usage
   scope note, or the drug checker's "not flagged ≠ safe" framing.
3. **No new paid infrastructure without a deliberate decision.**
   Nearby hospitals uses free OpenStreetMap data, not Google Places.
   The AI gateway's second provider (Groq) has a genuinely free tier.
   Real email verification and SMS reminders are researched (see
   `PROJECT_STATE.md`) but deferred pending an actual provider choice.
4. **Defense in depth on anything safety-relevant.** Emergency-number
   mentions are scrubbed from AI output at the code level (not just
   prompted against), image analysis has both a stricter prompt *and*
   a code-enforced extra disclaimer, and the admin gate has one single
   shared function rather than duplicated checks that could drift.

---

## Tech stack

**Backend:** FastAPI, SQLAlchemy + Postgres, JWT auth (python-jose +
bcrypt), slowapi rate limiting, Gemini + Groq for AI, dependency-free
TF-IDF for RAG retrieval, `fpdf2` for PDF export, `pypdf` for RAG
ingestion. Deployed on Render.

**Frontend:** React 19 + Vite, Tailwind CSS v4, React Router v7,
hand-rolled shadcn-style UI primitives on Radix, Leaflet +
`react-leaflet` for maps, `qrcode.react`, `vite-plugin-pwa` (Workbox)
for offline support. Deployed on Vercel.

**No ORM migration tool** (no Alembic) — new tables are created
automatically; new columns on existing tables need a manual
`ALTER TABLE` against production. See "Pending migrations" below.

---

## Quick start

### Backend

```bash
cd <repo root>
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env
# edit .env: at minimum set GEMINI_API_KEY, JWT_SECRET_KEY, DATABASE_URL

uvicorn app.main:app --reload
```

Server starts at `http://127.0.0.1:8000` — interactive docs at `/docs`,
health check at `/health`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # optional, only needed to point at a local backend
npm run dev             # http://localhost:5173
```

### Tests

```bash
python -m pytest tests/ -v
```

244 tests as of this writing — external calls (Gemini, Groq, Overpass)
are always monkeypatched, never hit the real network; the DB is a
throwaway SQLite file, never real Postgres.

---

## Environment variables

Backend (`.env`, see `.env.example` for the full annotated list):

| Variable | Required | Notes |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Free at https://aistudio.google.com/apikey |
| `JWT_SECRET_KEY` | Yes | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Yes | Postgres connection string |
| `ALLOWED_ORIGINS` | Yes | Comma-separated frontend origins for CORS |
| `GROQ_API_KEY` | No | Free at https://console.groq.com — enables the AI gateway's fallback provider; skipped entirely if unset |
| `ADMIN_USER_IDS` | No | Transitional legacy admin mechanism — see "Admin access" below |

Frontend (`frontend/.env`, see `frontend/.env.example`):

| Variable | Required | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | No | Defaults to the deployed backend; set to point at localhost during development |
| `VITE_ADMIN_USER_IDS` | No | UI convenience only — controls whether the Admin Analytics link is shown, not real access |

---

## Admin access

Real role-based access control lives in `users.role` (`"user"` |
`"admin"`). Since there's no unauthenticated way to safely create the
first admin (that would be a real vulnerability), bootstrapping is a
deliberate manual step:

```bash
python -m app.scripts.grant_admin your-email@example.com
```

After that, further promotions can happen self-service through
`POST /admin/users/{user_id}/role` by any existing admin. The old
`ADMIN_USER_IDS` env var still works as a transitional fallback so
nobody loses access mid-migration, but it's meant to be removed once
every env-var admin has a real role — see `PROJECT_STATE.md`.

The Admin Analytics page (`/admin/analytics`) is deliberately **not**
linked in the sidebar nav — visit it directly once you have access.

---

## Pending production migrations

⚠️ Two columns were added to the `users` table that `create_all()`
won't retroactively add to an existing production database. Run these
once, in order, against production:

```sql
ALTER TABLE users ADD COLUMN created_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
```

Then re-grant admin to whoever needs it via the CLI script above. Full
detail in `PROJECT_STATE.md`'s "Key gotchas" section.

---

## API reference (grouped)

Full request/response schemas are always current at `/docs` — this is
a map of what exists, not a substitute for it.

| Area | Base path |
|---|---|
| Auth | `POST /auth/signup`, `POST /auth/login` |
| Symptom analysis | `POST /analyze`, `POST /analyze/image`, `POST /analyze/follow-up` |
| Health Passport | `GET/PUT/DELETE /passport/{user_id}`, `/passport/{user_id}/documents`, `/passport/{user_id}/report`, `/passport/{user_id}/audit-log` |
| History | `GET /history/{user_id}`, `/history/{user_id}/trends`, feedback endpoint |
| Reminders | `GET/POST /reminders`, `PATCH/DELETE /reminders/{id}`, `/complete` |
| Drug interactions | `POST /drug-interactions/check` |
| Emergency | `GET /emergency/nearby-hospitals` |
| Caregivers | `/caregivers/invite`, `/accept`, `/my-caregivers`, `/my-patients`, `/{patient_user_id}/passport`, `/history`, `/reminders` |
| Admin | `/admin/analytics`, `/admin/users`, `/rag-review` (RAG staging review queue) |

Most routes are public or work anonymously where it makes sense (SOS
nearby-hospitals, drug interactions) — the ones handling personal data
require a JWT bearer token from signup/login.

---

## Project structure

```
app/
├── main.py                  FastAPI entrypoint, CORS, global error handler
├── config.py                 Settings (env-var backed, typed)
├── ai/                        AI gateway (Gemini->Groq), prompts, triage orchestration
├── auth/                      JWT/password logic, shared admin-gate dependency
├── emergency/                  Overpass hospital lookup, multi-mirror fallback
├── insights/                   Symptom-recurrence trend detection
├── interactions/                Curated drug-interaction data + matcher
├── models/                       Pydantic request/response schemas
├── rag/                          Corpus, retriever, allowlist, staging ingestion
├── routes/                        One file per resource area
├── rules/                         Deterministic severity rule engine
├── scripts/                        CLI tools (grant_admin, RAG ingest/promote)
└── storage/                        SQLAlchemy models + one *_store.py per resource

frontend/
├── src/
│   ├── api/                Axios client, one file per resource
│   ├── components/           ui/ primitives, layout/, plus one folder per feature
│   ├── context/                AuthContext (JWT session)
│   ├── hooks/                   useApi, useVoiceInput, useOnlineStatus
│   ├── pages/                    One file per screen, wired in App.jsx
│   └── constants/routes.js        Single source of truth for paths
└── public/icons/                    PWA app icons

tests/            244 tests, mirrors the app/ structure
PROJECT_STATE.md   Full development history and current in-progress state
```

---

## Known limitations (see `PROJECT_STATE.md` for the full, current list)

- Reminders are in-app only — no push/email/SMS yet.
- Drug interaction checker covers ~34 well-known combinations, not a
  comprehensive database.
- Rule-engine safety floor is English-only even though AI responses
  are multilingual.
- No caregiver-action audit log yet (Passport itself has one).
- Ambulance live-tracking was explicitly *not* built as a fake/demo
  feature — there's no real ambulance fleet or dispatch system behind
  it, and simulating one on an emergency page would be actively
  misleading.
