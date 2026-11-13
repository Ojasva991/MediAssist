# Moving Vaeda/MediAssist to hosting that doesn't pause

Checked Nov 2026. Free tiers change without notice - re-verify before relying on a number.

## Target stack (all free, no card unless noted)

| Layer | Now | Move to | Why |
|---|---|---|---|
| Database | Supabase (pauses after ~1 week idle) | **Neon Postgres** | Free plan never expires; scales to zero after 5 min idle and wakes in ~hundreds of ms (no manual "restore"). 0.5 GB / 100 CU-hours per project. |
| Backend API | Render free (sleeps after 15 min) | **Render free + keep-alive ping** (included workflow) | Same code, no rewrite. 750 free hrs/month is enough for one 24/7 service. Upgrade path: Google Cloud Run (needs card, free allowance). |
| Website | Vercel Hobby (non-commercial only) | **Cloudflare Pages** | Free, no sleep, commercial use allowed, unlimited static bandwidth. |
| Android app | - | **Capacitor** wrapper of the same React app | One codebase for web + app. APK is free; Play Store is a one-time $25. iPhone: install the PWA (App Store needs a Mac + $99/yr). |
| AI | Gemini -> Groq | **Provider cascade** (Groq, Cerebras, Mistral, OpenRouter, Cloudflare, your own Ollama, Gemini optional) | No single vendor is a point of failure. |

Honest limits: there is no truly free, always-on, no-card backend in 2026; every free host sleeps or caps hours. The keep-alive ping + a database that wakes itself is the standard workaround. Neon's 100 CU-hours cap is roughly 13 awake hours/day at 0.25 CU - fine at your scale because idle time is free.

## Step 0 - rotate secrets (do first)
Your zip contained a real `.env` (database URL with password, API key, short JWT secret). Treat them as exposed: reset the Supabase DB password (or delete the project after migrating), regenerate the Gemini key, and generate a new 64-char `JWT_SECRET_KEY`. Never share `.env` again. (Changing the JWT secret logs everyone out once - fine.)

## Step 1 - Database -> Neon
1. neon.com -> sign up -> create project (pick the region closest to users, e.g. AWS ap-southeast-1 for India) -> copy the **pooled** connection string.
2. Data: if the Supabase project is only *paused*, restore it from the dashboard, then
   `pg_dump "$OLD_URL" --no-owner --no-acl -Fc -f vaeda.dump`
   `pg_restore --no-owner --no-acl -d "$NEON_URL" vaeda.dump`
   If it can't be restored, just point the app at the empty Neon DB: tables are created on startup. A fresh DB already has the `users.created_at` and `users.role` columns, so the two "pending manual migrations" in PROJECT_STATE.md don't apply. Existing users would need to sign up again.
3. Set `DATABASE_URL` (the app adds `sslmode=require` itself).
4. `python -m app.scripts.grant_admin you@example.com` to make yourself admin.

## Step 2 - AI keys (get 2-3, takes ~10 min)
Groq (console.groq.com), Cerebras (cloud.cerebras.ai), Mistral (console.mistral.ai), OpenRouter (openrouter.ai). Put keys in env vars; order via `AI_PROVIDER_ORDER`. Free limits are daily/per-minute caps that change - the cascade + 60 s cooldown on 429s is what absorbs that. Model IDs on free tiers get retired: if a provider starts failing with 404/400, check its model list and change the `*_MODEL` env var, no code change.
Fully independent option: run Ollama on your own PC/laptop/server (`ollama pull llama3.1:8b`), expose it (Cloudflare Tunnel is free) and set `LOCAL_LLM_BASE_URL`/`LOCAL_LLM_MODEL`.

## Step 3 - Backend on Render
New Blueprint from this repo (`render.yaml`), fill the `sync: false` env vars (DATABASE_URL, ALLOWED_ORIGINS, API keys). In GitHub -> Settings -> Variables add `API_URL=https://<your-service>.onrender.com` so `.github/workflows/keepalive.yml` pings `/health` every 10 min. Check `/health`: `ai_providers_configured` should be > 0.

## Step 4 - Website on Cloudflare Pages
Connect the repo, root dir `frontend`, build `npm run build`, output `dist`, env var `VITE_API_BASE_URL=https://<your-api>`. `public/_redirects` handles SPA routing. Add the final Pages URL to `ALLOWED_ORIGINS` on the backend.

## Step 5 - Android app
```
cd frontend && npm install
npm run build && npx cap add android     # once
npm run cap:sync && npm run cap:open     # opens Android Studio -> Build APK
```
Origins `capacitor://localhost` / `https://localhost` are already in the default CORS list. Known gaps to fix in the app code: the Web Speech voice input doesn't work inside Android WebView (use a Capacitor speech plugin), and reminders use the browser Notification API (switch to `@capacitor/local-notifications`, which also gives real background reminders - the biggest current limitation). Geolocation should use `@capacitor/geolocation`.

## Things I changed in the code
- `app/ai/providers.py`, `gateway.py`: multi-provider cascade, cooldown on rate limits, **image analysis now also goes through the cascade** (before it was Gemini-only, so a Gemini outage killed photo analysis). Gemini is optional and lazily initialised.
- `config.py`: `settings.validate()` existed but was **never called** - with no `JWT_SECRET_KEY` the app would have signed forgeable tokens. Now runs at startup; production also requires a >=32-char secret and no `*` CORS.
- `rate_limit.py`: behind Render's proxy every user shared one IP bucket; now uses the real client IP (right-most `X-Forwarded-For`, trusting `TRUSTED_PROXY_HOPS`).
- `db.py`: pool settings for Neon's idle-suspend; `postgres://` URLs normalised.
- `/health` no longer hard-codes `"ai_service": "online"`.
- Tests: `test_ai_gateway.py` rewritten; `test_groq_client.py` removed (replaced by the generic provider). **I could not run the test suite here (no network to install dependencies) - run `python -m pytest` and tell me what fails.**

## Known issues not fixed yet (in priority order)
1. **Documents stored in Postgres**: up to 5 MB x 20 per user vs Neon's 0.5 GB - a handful of users fills it. Move files to Cloudflare R2 (free 10 GB, card needed to enable) or lower the caps (frontend hard-codes 5 MB in `DocumentsSection.jsx` too).
2. Rate limiter is in-memory (resets on restart; per instance). Fine for one instance.
3. Rule-engine red-flag keywords are English-only while replies are multilingual (already disclosed in UI) - add Hindi/Hinglish keywords; relevant for Indian users.
4. JWT in `localStorage` (XSS risk) and no email verification/password reset.
5. No schema migrations (Alembic); new columns need manual `ALTER TABLE`.
6. Frontend `package.json` Capacitor versions (^7) were not install-tested; run `npm install` and adjust if a newer major is current.
