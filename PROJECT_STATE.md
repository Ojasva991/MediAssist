# Vaeda — Project State

> **How to use this file:** This is the single source of truth for where the
> project stands. Update the "Last Updated" line and the relevant sections at
> the end of *every* work session, even a short one. When picking this project
> back up after a gap, read only this file (not the whole codebase) before
> deciding what to work on — it should be enough to re-orient cheaply.

**Last Updated:** 2026-07-28 (hospitals map + reminders + disposable-email
blocking — see Section 6)
**Repo:** https://github.com/Ojasva991/MediAssist (owner: Ojasva991) — repo
name itself is still "MediAssist" on GitHub; only the product/app inside it
is Vaeda. Renaming the repo itself still hasn't been done.
**Live backend:** https://mediassist-3jpl.onrender.com — URL unchanged.
Free tier — cold starts after inactivity.
**Live frontend:** https://medi-assist-nu.vercel.app — URL unchanged.

---

## 1. What's actually done (verified against code, not assumed)

**Foundation + 2026-07-25/26 work:** see prior versions of this file in git
history for full detail. Summary: FastAPI + React on Render/Vercel, JWT auth,
passport-first profile, deterministic rule engine, dependency-free TF-IDF
RAG, confidence indicator, feedback loop, history+trends, audit log, full
Vaeda rebrand (text + frontend redesign), doctor-facing PDF report export,
emergency QR code, and Health Passport document attachments (files stored
directly in Postgres, capped at 5MB/20 per user). **All of the above is
confirmed pushed and live as of this session** — verified directly via
`git log`, `git pull`, and hitting the live backend root endpoint, not just
trusted from a prior write-up.

**Built 2026-07-27:**

- **History insights dashboard (done, pushed, frontend-only):** two new
  charts on the History page below the existing keyword-trend banner -
  severity-over-time (line) and most-common-possible-conditions-this-month
  (bar). Both are hand-rolled SVG, no charting library added (matches this
  project's existing "no new dependency unless it earns it" pattern from
  `trends.py`/`retriever.py`). Pure functions in `frontend/src/lib/insights.js`
  derive both from data the page already fetches - no new backend endpoint.

- **Hybrid-retrieval staging pipeline (done, pushed, not yet used in
  production answers):** the offline+live guidance sources feature from the
  old backlog, built to the four requirements that were specified when it
  was deferred (scheduled ingestion, source allowlist, human review gate,
  real licensing answer). Checked WHO's actual license terms before writing
  any code (CC BY-NC-SA 3.0 IGO - non-commercial only, attribution +
  share-alike required; project's commercial status is still "not decided,"
  so every approval in the review step has to re-confirm this, not just
  once at setup). Three separate stages, each requiring a deliberate human
  action to proceed to the next - ingestion never touches review, review
  never touches the live corpus:
  1. `python -m app.rag.ingest` - fetches only from `app/rag/sources.py`'s
     allowlist (currently just the WHO/ICRC "Basic Emergency Care" guide),
     stages chunks in a new `staged_guidance_documents` table.
  2. `GET/POST /rag-review` - admin-only (gated by a new `ADMIN_USER_IDS`
     env var - there's still no real RBAC in this project, this is a
     stopgap) approve/reject queue.
  3. `python -m app.rag.promote` - prints ready-to-paste `GuidanceEntry`
     code for a human to hand-add to `app/rag/corpus.py`. Never auto-writes
     to the file the AI actually retrieves from.

- **Emergency-flow: nearby hospitals on the SOS page (done, pushed, live -
  but see the debugging saga below, worth reading before touching this
  code again):**
  - `GET /emergency/nearby-hospitals?lat=&lon=&radius_km=&limit=` - public,
    no login required (same as the rest of the SOS page), rate-limited by
    IP. Looks up hospitals via OpenStreetMap's Overpass API - deliberately
    not Google Places, to avoid a new paid API key/billing account without
    asking first (same reasoning as the document-storage tradeoff).
  - **This took five follow-up fixes after the first deploy, each one a
    real production bug caught via Render's live logs, not hypothetical:**
    1. `[Errno 101] Network is unreachable` - Render has no outbound IPv6
       route, but `urlopen` doesn't fall back to IPv4 automatically when
       DNS hands it an IPv6 address first. Fixed by forcing IPv4-only DNS
       resolution for this one call (`_force_ipv4_dns()` in
       `hospital_lookup.py`) - no new dependency needed.
    2. `[Errno 111] Connection refused` from `overpass-api.de` specifically
       - that public instance is known to block/rate-limit shared
         datacenter IPs (which Render's free-tier egress IP is). Fixed by
         trying a *list* of mirrors in order
         (`settings.OVERPASS_API_URLS`), not a single URL.
    3. Zero results for a real city (Indore) despite mirrors succeeding -
       turned out to be a genuine query bug: Overpass's `out` statement
       grammar is `out [verbosity] [geometry-modifier];` and the query had
       them backwards (`out center tags;` instead of `out tags center;`).
    4. Still zero results after that fix - `overpass.osm.ch`, one of the
       fallback mirrors, **only contains Switzerland's OSM data** (stated
       on its own site). It was silently succeeding with an empty result
       for any non-Swiss location. **Any future mirror added to
       `OVERPASS_API_URLS` must be verified as globally-scoped first** -
       this exact mistake already happened once.
    5. A DNS resolution failure (`Name or service not known`) on
       `api.openstreetmap.fr` in production - possibly a stale/dead mirror.
       At this point, rather than keep adding mirrors indefinitely, added
       a structurally different fix instead of another patch (see below).
  - **Given that pattern (three different failure modes across three
    different free community Overpass mirrors), the real lesson is: public
    Overpass mirrors are not reliable infrastructure to depend on from a
    shared-IP host, full stop - not a "just add one more mirror" problem.**
    So the SOS page now also has a **zero-backend guaranteed fallback**: a
    plain Google Maps search link (`googleMapsHospitalsUrl` in `SOS.jsx`)
    that works even if every Overpass mirror is down, since it's just a
    URL with no server round-trip at all. Overpass results (when they
    work) are still shown first/inline as the nicer experience; the Maps
    link is the backstop that makes the feature un-fail-able. Also
    broadened to match both `amenity=hospital` and `healthcare=hospital`
    OSM tagging schemes, and added a one-time radius-widening retry
    (5km → 15km) if the first attempt is empty.
  - **Confirmed live and working** (2026-07-28) - the SOS page now shows
    a real, correctly-sorted list of nearby hospitals (verified against a
    live screenshot: Banthia Hospital, Geetanjali Hospital, etc. near
    Indore, with accurate distances/addresses/phone links), and the
    Google Maps fallback link is confirmed working too.

- **Interactive hospitals map on the SOS page (done, pushed):** the
  hospital list now has a List/Map toggle. Map view uses Leaflet + free
  OpenStreetMap tiles (no API key/billing account - same reasoning as
  everywhere else in this project). User location (blue dot) and each
  hospital (red pin) are plotted; tapping a pin shows name/distance/
  address/directions. New frontend dependencies: `leaflet`,
  `react-leaflet`.

- **Reminders (done, pushed) - in-app only, scope deliberately limited:**
  full CRUD (`/reminders`) for medication/follow-up/other reminders, with
  optional daily/weekly repeat. Completing a repeating reminder advances
  it to its next occurrence rather than deleting it. **No push
  notification, email, or SMS behind this** - only a foreground browser
  `Notification` popup (opt-in, polls every 30s) while the tab is open.
  The UI states this limitation directly, not just in code comments -
  see the note card on the Reminders page itself. Don't let this quietly
  grow a "send at remind_at" background job without the actual
  infrastructure (a real push/email/SMS service) existing first.

- **Signup: disposable-email blocking (done, pushed) - explicitly
  best-effort, not full verification:** `app/auth/disposable_domains.py`
  is a static blocklist of ~40 known throwaway-email domains
  (mailinator.com, tempmail.com, etc.), checked at signup alongside a
  tightened (but still simple, not RFC 5322) email-format regex. This
  catches the obvious/common cases only - it will never be exhaustive,
  and it is NOT the same guarantee as real email verification (a
  confirmation link requiring a working email-sending service, which
  this project doesn't have - see the backlog entry below for the
  actual provider research done on that decision).

---

## 2. What's next — in priority order

1. **Ambulance live-tracking - explicitly NOT to be built as a fake/demo
   feature.** The idea was raised (a Zomato/Swiggy-style moving-icon map)
   but there is no real ambulance fleet, driver app, or dispatch system
   behind it. Showing a moving "ambulance" icon on an emergency page
   without a real GPS-reporting vehicle behind it would be actively
   misleading in a genuine emergency - someone could wait for a fake
   ambulance instead of calling for real help. **This only becomes a
   legitimate feature if/when there's an actual ambulance/driver partner
   integration to tie it to** - until then, don't build a simulated
   version of this even as a placeholder.
2. **Actually rename the live URLs**, if still wanted - hosting-dashboard
   action, not code (see git history/prior conversation for the sequencing
   if retried: backend URL → frontend API base URL → backend CORS).
3. **Decide on an email-sending provider**, if full email verification at
   signup is wanted (a confirmation link required before the account
   works - stronger than the disposable-domain blocklist already built,
   see Section 1). Researched 2026-07-28, not yet decided: SendGrid's
   free tier is gone (retired 2025, trial-only now). Best genuinely-free-
   forever, no-credit-card options are **Brevo** (300/day, ~9,000/month,
   most generous) and **Resend** (3,000/month, nicer developer API, less
   volume). This needs an actual account signup + API key on the user's
   side before any code can use it - not something to pick unilaterally.
4. **SMS reminders** - same kind of decision as above but for SMS (a
   provider like Twilio, with a phone number and real per-message cost).
   Explicitly deferred, not started, not decided on.
5. Remaining backlog, unsequenced: drug interaction checker (needs careful
   sourcing/disclaiming), offline-first PWA for SOS (would also be what
   makes real push notifications for reminders possible, see Section 1),
   voice input, caregiver/family mode, wearable data import,
   emergency-flow additions beyond hospitals (e.g. showing the user's own
   emergency contact's live ETA - same "needs something real behind it"
   caveat as ambulance tracking above), AI assistant (follow-ups,
   multilingual), Redis/Docker/JWT hardening/real role-based access
   control (would also let the `/rag-review` admin gate stop being an
   env-var stopgap), admin analytics dashboard.

## 3. Key gotchas (don't relearn these the hard way)

- Don't add `passlib` - bcrypt conflict, already fixed once.
- `google-auth` must stay `>=2.48.1,<3.0.0` - required by `google-genai`.
- Render free tier cold-starts after inactivity - expected, not a bug.
- Run pytest as `python -m pytest`, not a bare `pytest` command.
- Tests never touch the real Postgres database or real Gemini API, or the
  real Overpass API - `tests/conftest.py` uses a throwaway SQLite file;
  external calls are monkeypatched at the function level (see
  `test_documents.py`'s Gemini pattern, `test_hospital_lookup.py`'s
  Overpass pattern).
- New TABLES need no manual migration (`create_all()` handles it). New
  COLUMNS on an EXISTING table DO need a manual `ALTER TABLE` - still no
  Alembic/migration tool in this project.
- **Render has no outbound IPv6 route.** Any future code making an
  external HTTP call from the backend should be aware `urlopen`/`requests`
  can fail with `Errno 101 Network is unreachable` if DNS returns an IPv6
  address first - see `_force_ipv4_dns()` in `app/emergency/hospital_lookup.py`
  for the workaround pattern if this comes up again elsewhere.
- **Free public Overpass mirrors are not reliable infrastructure** - see
  Section 1's emergency-flow entry for the full saga. Don't add a new
  mirror to `OVERPASS_API_URLS` without confirming it's globally-scoped
  (not a regional extract like `overpass.osm.ch`) and currently resolving.
- **New Python dependencies:** `fpdf2`, `python-multipart`, `pypdf` (added
  2026-07-27 for RAG PDF ingestion). **New frontend dependency:**
  `qrcode.react`. All need installing after pulling.
- The frontend's `localStorage` session key is `vaeda_session` (renamed
  from `mediassist_session` on 2026-07-26 - one-time logout, not a bug).
- The live Render/Vercel URLs still say "mediassist" - hosting-dashboard
  action needed if this is still wanted, code changes alone won't do it.
- **This file has been wrong about code state multiple times before.**
  Verify directly against the repo/live site for anything specific rather
  than trusting a "done"/"pending" claim in here at face value.

## 4. Session log

*(Entries before 2026-07-27 — 2026-07-23 through 2026-07-26 — are
preserved in git history; summarized under Section 1 above.)*

- 2026-07-27: Confirmed the entire 2026-07-26 handoff (rebrand text,
  document attachments) had NOT actually been pushed despite being marked
  done - applied both from zips, verified via `git log`/live-site fetch,
  pushed. Built and pushed the History insights dashboard (frontend-only,
  no new dependency). Checked WHO's actual licensing terms (not assumed)
  before building the hybrid-retrieval staging pipeline for the previously
  -deferred RAG feature - three-stage ingest/review/promote pipeline, all
  gates manual and deliberate. Built emergency-flow nearby-hospitals on the
  SOS page; this required five separate production-bug fixes after
  deployment (IPv6 egress, mirror rate-limiting, Overpass query grammar,
  a region-locked mirror, a dead mirror) before landing on a Google Maps
  link as a guaranteed zero-backend fallback rather than continuing to
  chase individual mirror failures. User proposed a Zomato/Swiggy-style
  live ambulance-tracking map; flagged that this would require real
  ambulance/driver GPS data to be honest (not something to fake on an
  emergency page) and logged both that idea and the more modest
  "interactive hospitals map" idea to the backlog above instead of
  building either this session.
- 2026-07-28: Confirmed the nearby-hospitals feature live via a real
  screenshot (Banthia Hospital, Geetanjali Hospital, etc. near Indore).
  Built the interactive hospitals map (Leaflet + free OSM tiles, List/Map
  toggle on the SOS page). Built the Reminders feature - full CRUD,
  medication/follow-up/other categories, daily/weekly repeat - scoped
  deliberately to in-app-only (no push/email/SMS), with that limitation
  stated directly in the UI, not hidden. Researched real email-sending
  providers (SendGrid's free tier is gone; Brevo and Resend are the best
  free-forever no-card options) as a first step toward stronger signup
  email verification, but deferred the actual provider choice since it
  needs an account signup on the user's side. Built the lighter-weight
  version now: a disposable/throwaway-email domain blocklist at signup,
  explicitly documented as best-effort rather than real verification.
  Logged SMS reminders as a separate deferred paid-infra decision.
