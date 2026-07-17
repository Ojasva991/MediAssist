# MediAssist — Handoff Update (Backend work completed since original HANDOFF.md)

This document summarizes everything done on the **backend** since the original
HANDOFF.md was written. Read this fully before making any frontend changes —
several backend behaviors changed in ways the frontend must now account for.

## Repo
https://github.com/Ojasva991/MediAssist (owner: Ojasva991)

## What changed on the backend (all done, deployed, and tested live)

### 1. Persistent storage (was: in-memory dict, wiped on every restart)
- Passport data now lives in a **Google Sheet**, accessed via `gspread` +
  a Google Cloud service account.
- New files: `app/storage/sheets_client.py` (shared connection),
  `app/storage/passport_store.py` (rewritten to use it).
- New env vars required on Render: `GOOGLE_SHEET_ID`, `GOOGLE_SHEETS_CREDENTIALS`.
- The spreadsheet has two tabs: **Passports** and **Users** (see below).
  Both are auto-created by the code on first use if missing.

### 2. Real authentication (was: no auth at all — anyone could read/edit any user_id)
- New endpoints: `POST /auth/signup`, `POST /auth/login` (see `app/routes/auth.py`).
  Both return `{ access_token, token_type, user_id, name, email }`.
- Passwords are hashed with `bcrypt` (NOT passlib — passlib is incompatible
  with modern bcrypt versions, this cost real debugging time, don't reintroduce it).
- JWTs are signed with `HS256`, 7-day expiry (`app/auth/security.py`).
- New env var required: `JWT_SECRET_KEY` (long random string).
- `user_id` is now **deterministically derived from email**
  (`app/storage/user_store.py::_derive_user_id` — sha256 of lowercased,
  trimmed email, first 24 hex chars). Same email always produces the same
  user_id, so passport data keys correctly to the account that owns it.
- **All `/passport/*` routes now require a valid Bearer token**, AND the
  `user_id` in the URL path must match the `user_id` embedded in the caller's
  token, or the API returns `403 Forbidden`. See `app/auth/dependencies.py`
  (`get_current_user_id`) and `_ensure_self()` in `app/routes/passport.py`.

### 3. CORS restricted (was: `allow_origins=["*"]`, wide open)
- Now driven by `settings.ALLOWED_ORIGINS`, a list parsed from the
  `ALLOWED_ORIGINS` env var (comma-separated), defaulting to:
  `https://medi-assist-nu.vercel.app,http://localhost:5173`
- If the frontend's deployed URL ever changes, this env var (or the default
  in `app/config.py`) needs updating too, or requests will be blocked by
  the browser.

## What this means for the FRONTEND (not yet done — this is your job now)

The frontend currently has a **temporary, minimal patch** (not the final
premium UI) that makes the above work end-to-end:

- `frontend/src/api/auth.js` — wraps `/auth/signup` and `/auth/login`
- `frontend/src/api/client.js` — attaches `Authorization: Bearer <token>`
  to every request via an axios interceptor, reading from
  `localStorage["mediassist_session"]`
- `frontend/src/context/AuthContext.jsx` — **temporary/stopgap logic**:
  tries login first, and if the account doesn't exist yet, automatically
  signs one up, so a single form (name + email + password) covers both
  flows without a separate signup screen
- `frontend/src/pages/Login.jsx` — added a password field to the existing
  form, otherwise mostly unchanged

**This is explicitly flagged as temporary.** The agreed plan (confirmed
directly by the project owner) is:

> Do a proper frontend rebuild later, as part of a premium UI pass — real
> separate Login/Signup screens, better validation and error states, and a
> visual redesign. The current AuthContext.jsx login-then-signup fallback
> should be replaced with that at that time, not kept long-term.

## Remaining backend roadmap (not started yet, from original priority list)

4. Fix emergency number handling at the AI prompt level (currently only
   patched on frontend)
5. Rate limiting on `/analyze` (no protection yet against abuse/cost overrun)
6. Symptom analysis history (now feasible since Sheets storage + auth exist —
   would need a new "AnalysisHistory" tab similar to Users/Passports)
7. Multi-language support (not started)

## Key gotchas worth knowing before touching this code

- **Don't add `passlib`** — real dependency conflict with current bcrypt,
  already hit and fixed once (see `app/auth/security.py` comments).
- **`google-auth` version matters** — `google-genai` requires
  `google-auth>=2.48.1`; pinning it lower breaks `pip install` on Render
  with `ResolutionImpossible`. Current `requirements.txt` has the correct
  range (`>=2.48.1,<3.0.0`).
- Google Sheets writes are simple fetch-all-rows-and-scan operations —
  fine for hackathon-scale traffic, but **not built to scale**. Postgres
  is still the recommended real-production upgrade (this was true before
  and remains true now — Sheets was chosen deliberately for
  quick setup + visibility, not long-term scale).
- The live backend is at `https://mediassist-3jpl.onrender.com` (free tier —
  cold starts after inactivity, first request after idle can be slow).
