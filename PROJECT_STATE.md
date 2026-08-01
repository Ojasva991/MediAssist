# Vaeda — Project State

> **How to use this file:** This is the single source of truth for where the
> project stands. Update the "Last Updated" line and the relevant sections at
> the end of *every* work session, even a short one. When picking this project
> back up after a gap, read only this file (not the whole codebase) before
> deciding what to work on — it should be enough to re-orient cheaply.

**Last Updated:** 2026-07-30 (offline-first PWA for SOS + caregiver/family
mode — see Section 6)
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

- **Voice input for symptoms (done, pushed):** a "Speak" button next to
  the Symptoms field on the Symptom Analysis page, using the browser's
  built-in Web Speech API. No backend, no new dependency, no cost -
  feature-detected and hidden in browsers that don't support it
  (Firefox, mostly).

- **Photo-based visual symptom analysis (done, pushed) - a genuinely
  higher-stakes feature, built with extra guardrails, not a casual
  add-on:** new "Photo" tab on Symptom Analysis, `POST /analyze/image`.
  Uses Gemini's multimodal (vision) capability - same model, no new
  provider. Key safety decisions, worth remembering if this code is
  touched again:
  - A **separate, stricter system prompt** (`IMAGE_SYSTEM_PROMPT` in
    `app/ai/prompts.py`) than text analysis - explicitly forbids
    reassuring language ("looks benign", "probably fine") for anything
    resembling a skin lesion/mole/wound, since false reassurance on a
    photo is a worse failure mode than a text tool getting severity
    wrong.
  - **Medical scans (X-ray/CT/MRI/lab reports) are explicitly out of
    scope** - the AI is instructed to decline interpreting those
    (`image_rejected: true`) and point to the ordering doctor/a
    radiologist, rather than attempt general-vision interpretation of
    actual medical imaging.
  - Every response includes `visual_observation` - what the AI actually
    saw, in plain language, so the person can confirm it looked at the
    right thing.
  - A mandatory extra disclaimer sentence about photo unreliability is
    enforced in code (not just requested in the prompt) - defense in
    depth, same pattern as emergency-number scrubbing elsewhere.
  - Real bug caught during testing: the shared `analysis_history` table
    requires age+gender NOT NULL, but this endpoint allows a photo with
    zero patient info - fixed by skipping the history save gracefully
    in that case (logged, not crashed, not faked with placeholder
    data).

- **AI Gateway with Groq fallback (done, pushed) - text `/analyze` path
  only:** `app/ai/gateway.py` tries Gemini first, then Groq (free, no
  credit card, OpenAI-compatible API) if Gemini fails, before the
  caller falls through to the existing rule-engine-only fallback. Same
  "try several, then a guaranteed fallback" shape as the Overpass
  nearby-hospitals lookup, applied to the AI layer. Groq is skipped
  entirely (not an error) if `GROQ_API_KEY` isn't set - the app must
  keep working with just Gemini configured. **Deliberately does NOT
  cover `/analyze/image`** - Groq's vision-model lineup wasn't verified
  as a safe drop-in for the same conservative image-analysis prompt,
  so image analysis still calls Gemini directly. Researched but NOT
  added as providers: OpenAI (free tier gone since mid-2025, needs
  prepaid billing - a new paid-infra decision) and Ollama (needs a
  dedicated server actually running the model - Render's free tier
  can't host this at all, a different infrastructure category, not
  just a decision). Both could be added later following the exact same
  pattern as Groq in `gateway.py`, if/when those decisions are made.

- **Drug interaction checker (done, pushed) - deliberately small scope,
  purely deterministic, no AI call at all:** `POST
  /drug-interactions/check` (public, no login required). Researched
  first, per usual practice here: NLM's official Drug-Drug Interaction
  API was discontinued in January 2024 (confirmed, not a rumor) and
  DrugBank's free checker is being retired March 25, 2026 - there is
  currently no live, free, official pairwise interaction API to call.
  The realistic broad-coverage option is DDInter 2.0 (302,516 records,
  but CC BY-NC-SA 4.0 - same non-commercial licensing question already
  open for the WHO RAG sources) - that's a much bigger data-engineering
  project (download, parse, host, build name resolution), explicitly
  NOT done this round. What got built instead: `app/interactions/corpus.py`,
  a hand-written list of ~34 well-established, textbook-level
  interactions (anticoagulants, SSRIs/MAOIs, cardiac drugs, diuretics,
  NSAIDs, a few antibiotics/antifungals, one herbal supplement) checked
  via exact case-insensitive name/alias matching - no fuzzy matching, no
  AI-assisted name resolution, and **no AI call anywhere in this
  feature** - same "an LLM sounding confident while being wrong is a
  real harm here" reasoning as the rule engine's severity floor. A
  drug pair not in this list is NOT reported as safe - the response
  and disclaimer are explicit that "not flagged" means "not checked
  against a real database," not "confirmed fine." If DDInter ingestion
  is wanted later, `app/interactions/matcher.py`'s lookup shape
  (canonical name + aliases, frozenset-keyed pair index) would extend
  naturally to a much bigger dataset without a redesign.

- **Multilingual responses + follow-up chat (done, pushed):**
  - **Safety prerequisite fixed first, not after:** the emergency-number
    scrubber (`_sanitize_emergency_number` in `app/ai/triage_service.py`)
    was English-verb-anchored (`call|dial|contact` + a number) - a wrong
    number stated in another language would have slipped straight
    through. Broadened to match the bare number regardless of
    surrounding language, with a regression test proving it (Spanish
    phrasing case).
  - Both system prompts (text + image) now instruct the AI to respond
    in whatever language the person used.
  - **Honest, UI-visible caveat, not just a code comment:** the
    deterministic rule-engine safety floor is still English-keyword-
    only (`chest pain`, `difficulty breathing`, etc.). Responding in
    another language does NOT extend that floor - this is stated
    directly on the Symptom Analysis page and in the follow-up chat
    itself, not buried.
  - **Follow-up chat** (`POST /analyze/follow-up`, stateless - no chat
    history persisted server-side, frontend holds the conversation in
    React state and resends it each time): the rule engine re-runs over
    the ENTIRE conversation (original symptoms + every message
    exchanged, not just the latest one) on every turn, so a red flag
    raised mid-conversation still forces the severity floor up
    independent of the AI's own judgment - tested explicitly, including
    the case where the red flag is in an earlier turn, not the newest
    message. `escalation_detected` is forced true whenever the rule
    engine's floor exceeds what the AI itself reported, same defense-
    in-depth pattern as `sos_recommended` elsewhere in this codebase.
    Goes through the same Gemini→Groq gateway as text analysis; has its
    own safe, rule-engine-only fallback wording if both providers fail.

- **Offline-first PWA for SOS (done, pushed):** the app is now
  installable (manifest + generated icons from the existing pulse.svg
  brand mark) and the SOS page specifically works with zero network
  once visited. New frontend devDependency: `vite-plugin-pwa` (Workbox
  under the hood) - a deliberate exception to this project's usual
  "hand-roll it, avoid a new dependency" bias (see Overpass's plain-
  urllib client for the normal default). Reasoning: correctly
  precaching Vite's content-hashed build output and handling service-
  worker update/versioning by hand is a well-known source of "PWA
  silently serves broken stale UI" bugs - exactly the wrong risk to
  take on for a page whose entire purpose is working reliably during
  an emergency. `vite-plugin-pwa` is the standard, actively-maintained
  solution in the Vite ecosystem itself, not a random third-party
  library.
  - **What's cached, and why - this was the actual safety-relevant
    design decision, not the plugin choice:** the built app shell
    (JS/CSS/HTML) is precached, so the whole SPA loads with no network.
    The Health Passport GET specifically uses a NetworkFirst strategy
    (try fresh data, fall back to last-cached response only when truly
    offline) - that's what lets the SOS page's critical-info card
    (name, blood group, allergies, emergency contact) render offline.
  - **What's deliberately NEVER cached:** nearby-hospitals results and
    every other API call (auth, analyze, history, reminders, drug
    interactions, etc.) are NetworkOnly. Serving a stale hospital
    location as if it were current during a real emergency is a worse
    failure mode than just failing visibly - same "don't fabricate
    certainty" reasoning as everywhere else safety-relevant in this
    codebase. When offline, the SOS page shows a clear "you're offline,
    hospital search needs a connection" message (checked proactively
    before even attempting geolocation) rather than a confusing generic
    error, plus a small banner reminding the person that emergency
    calls and their saved info still work without a connection.
  - `start_url` is set to `/sos` specifically - launching the installed
    app from a home-screen icon goes straight to the most
    time-critical page, not the dashboard.
  - New: `frontend/src/hooks/useOnlineStatus.js` (native
    online/offline browser events - noted honestly in its own
    docstring that `navigator.onLine` means "network interface is up,"
    not "internet is actually reachable," since it isn't a guarantee).

- **Caregiver/family mode (done, pushed):** scoped via clarifying
  questions before building - separate accounts linked by an invite
  code (not a shared login), caregiver gets read-only Passport/History
  access plus the ability to manage reminders on the patient's behalf,
  no edit access to the patient's Health Passport itself.
  - Flow: `POST /caregivers/invite` (patient generates an 8-char,
    human-typable code - excludes visually-ambiguous characters like
    0/O, 1/I/L - expires after 7 days unused), shared out of band since
    there's no email-sending service yet (same limitation as the
    disposable-email/verification backlog item). `POST
    /caregivers/accept` (caregiver, logged into their OWN account,
    redeems it). Patient can revoke at any time
    (`POST /caregivers/{link_id}/revoke`) - only the patient who owns
    the link can revoke it, enforced in the store function itself, not
    just by convention at the route layer.
  - **The entire authorization boundary is one function**:
    `caregiver_store.has_active_access(caregiver_user_id,
    patient_user_id)`, called at the top of every patient-scoped route.
    Deliberately kept to doing exactly one narrow check rather than
    something cleverer - if this one function is ever wrong, everything
    downstream is wrong, so it stays simple and auditable.
  - Real bug caught by tests, not shipped: SQLite (used in tests/dev)
    silently strips timezone info when round-tripping a
    `DateTime(timezone=True)` column, even though it was stored as
    timezone-aware - Postgres (production) doesn't have this problem.
    Comparing a stored `expires_at` against `datetime.now(timezone.utc)`
    raised `TypeError` until a normalization helper was added. Worth
    remembering if any other code ever compares a DB-fetched datetime
    against a freshly-generated aware one.
  - Scope limits, explicit: no separate per-action audit log for
    caregiver activity yet (same "keep a trail" instinct as
    `PassportAuditLogRecord`, just not built out this round) - if this
    matters later, it's a straightforward addition, not a redesign.

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
5. Remaining backlog, unsequenced: real push notifications for
   reminders (the offline-first PWA above added the service-worker
   infrastructure that makes this more feasible than before, but actual
   push notifications still need a Push API subscription flow + VAPID
   keys + a backend endpoint to trigger them - not done this round,
   just less far away now), wearable data import, emergency-flow
   additions beyond hospitals (e.g. showing the user's own emergency
   contact's live ETA - same "needs something real behind it" caveat as
   ambulance tracking above), Redis/Docker/JWT hardening/real
   role-based access control (would also let the `/rag-review` admin
   gate stop being an env-var stopgap), admin
   analytics dashboard.

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
- 2026-07-28 (continued): Built voice input for symptoms (Web Speech
  API, client-side only). Built photo-based visual symptom analysis
  (`POST /analyze/image`) with deliberately stricter safety guardrails
  than text analysis - a separate conservative system prompt, explicit
  refusal to interpret medical scans, a visual_observation field so the
  person can verify what the AI actually saw, and a code-enforced extra
  disclaimer about photo unreliability. Caught and fixed a real bug
  where the shared history table's NOT NULL age/gender columns didn't
  account for this endpoint's "photo with zero context" case. User then
  referenced an idea from an architecture doc they'd written separately
  (multi-provider AI gateway with cascading fallback - Gemini → Groq →
  OpenAI → Ollama → rule engine). Researched current reality on all
  four: Groq is genuinely free/no-card and was added as a real second
  provider; OpenAI (free tier gone, needs billing) and Ollama (needs a
  dedicated server, Render free tier can't run it) were deferred with
  the same "new paid infra/hosting decision" reasoning used throughout
  this file, not built as fakes or stubs. Gateway scoped to the text
  `/analyze` path only, not image analysis - see Section 1 for why.
  Picked up the drug interaction checker next from the backlog.
  Researched real data-source availability first (NLM's official API
  discontinued Jan 2024; DrugBank's free checker retiring March 2026;
  DDInter 2.0 is the real broad-coverage option but is a 300K+ record
  downloadable dataset under CC BY-NC-SA, not a live API - too big for
  this round). User chose the smaller scope: a ~34-entry hand-curated
  list of well-established interactions, checked deterministically
  (exact name/alias matching, zero AI calls) - same reasoning as the
  rule engine's severity floor about not trusting an LLM to freely
  generate claims in a domain where being wrong is a real harm.
  Picked up "AI assistant (follow-ups, multilingual)" last. Scoped it
  via clarifying questions first: follow-ups meant a real chat thread
  (not just re-running analysis), multilingual meant auto-detect from
  what the person types. Found and fixed a real safety gap before
  building anything else: the emergency-number scrubber was English-
  verb-anchored and would have let a wrong number through in another
  language - broadened it first, with a regression test. Then added
  the language instruction to both system prompts, built the follow-up
  chat endpoint (stateless, rule engine re-checks the WHOLE conversation
  every turn so a red flag doesn't need to be in the latest message to
  be caught), and added an honest, UI-visible caveat (not just a code
  comment) that the rule-engine safety net itself is still English-only
  even though the AI's replies aren't.
- 2026-07-30: Built the offline-first PWA for the SOS page. Added
  `vite-plugin-pwa` as a devDependency - a deliberate one-off exception
  to this project's usual "avoid new dependencies" bias, reasoned
  through explicitly rather than defaulted into (hand-rolling correct
  Vite build-hash precaching risks exactly the kind of stale-broken-UI
  bug that would be worst on this specific page). Generated real app
  icons from the existing pulse.svg brand mark rather than placeholder
  art. The actual safety-relevant design work was deciding what NOT to
  cache: nearby-hospitals results and all other API calls are
  NetworkOnly, specifically so the app never shows stale hospital
  locations as if they were current during a real emergency - only the
  Health Passport GET gets NetworkFirst treatment, since that's what
  the SOS critical-info card needs to render offline. Added proactive
  offline detection (checked before attempting geolocation, not just
  reacting to a failed request) with honest UI messaging about what
  still works without a connection and what doesn't.
- 2026-07-30 (continued): Built caregiver/family mode. Scoped it
  deliberately via clarifying questions first, given the privacy/
  security stakes of one person accessing another's health data:
  separate accounts linked by an invite code (not shared logins),
  read-only Passport/History access plus reminder management, no
  Passport edit access. Kept the authorization check to one single,
  narrow, auditable function
  (`caregiver_store.has_active_access()`) that every patient-scoped
  route calls first, on purpose - simple enough to trust. Caught a
  real SQLite-vs-Postgres timezone bug via tests (naive/aware datetime
  comparison) before it could reach anywhere near production.
