# MediAssist AI — Backend (AI Integration)

AI-powered healthcare triage assistant. **This is not a diagnostic
tool.** It estimates symptom urgency and recommends a next step (e.g.
"see a doctor," "seek emergency care") — it never claims to know what
disease a user has, and every response carries a disclaimer saying so.

Built for a hackathon MVP. This repo covers the **AI integration**
piece: symptom analysis via Gemini, and the Health Passport API.
Frontend, database persistence, and the real SOS/location workflow are
out of scope here (see [Scope & Limitations](#scope--limitations)).

## Status

✅ All 7 milestones complete. Backend is ready for frontend integration.

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# then edit .env and add your real GEMINI_API_KEY
# get one free at https://aistudio.google.com/apikey

# 4. Run the server
uvicorn app.main:app --reload
```

Server starts at `http://127.0.0.1:8000`.

- **Interactive API docs (try it live):** `http://127.0.0.1:8000/docs`
- **Health check:** `http://127.0.0.1:8000/health`

## Project Structure

```
app/
├── main.py                    # FastAPI app entrypoint, CORS, global error handler
├── config.py                   # Environment variable loading (fail-fast if misconfigured)
├── models/
│   ├── symptom.py               # SymptomAnalysisRequest/Response, Severity enum
│   └── passport.py              # HealthPassport model, BloodGroup enum
├── ai/
│   ├── prompts.py                # System prompt + prompt builder (isolated from logic)
│   ├── gemini_client.py          # Thin Gemini API wrapper, retry/backoff
│   ├── triage_service.py         # Orchestration: prompt -> Gemini -> parse -> validate
│   └── fallback.py                # Safety-net response used only if Gemini fails
├── routes/
│   ├── analyze.py                 # POST /analyze
│   └── passport.py                # Health Passport CRUD
└── storage/
    └── passport_store.py          # In-memory storage (swap-in point for a real DB later)
```

## API Reference

### `POST /analyze` — AI Symptom Analysis

**Request body:**
```json
{
  "age": 28,
  "gender": "Male",
  "symptoms": "Chest pain and sweating",
  "duration": "30 minutes",
  "existing_conditions": null
}
```
| Field | Type | Required | Notes |
|---|---|---|---|
| `age` | int | yes | 0-120 |
| `gender` | string | yes | free text, non-blank |
| `symptoms` | string | yes | 3-1000 chars, non-blank |
| `duration` | string | yes | free text, e.g. "30 minutes" |
| `existing_conditions` | string \| null | no | e.g. "diabetes" |

**Response (200):**
```json
{
  "possible_conditions": ["Heart-related emergency"],
  "severity": "EMERGENCY",
  "recommended_action": "Seek emergency medical attention immediately.",
  "sos_recommended": true,
  "disclaimer": "This is not a medical diagnosis."
}
```
`severity` is always one of `LOW`, `MODERATE`, `HIGH`, `EMERGENCY`.

**If Gemini is unavailable:** this endpoint does NOT fail. It
automatically returns a conservative fallback response instead (see
[Reliability & Fallback Behavior](#reliability--fallback-behavior)
below) - always `200`, never a `5xx` for this reason.

**Error responses:**
- `422` - invalid input (e.g. negative age, blank symptoms) - rejected before reaching the AI
- `500` - a genuinely unexpected server error (not a Gemini failure - those use the fallback instead)

---

### Health Passport — `PUT` / `GET` / `DELETE /passport/{user_id}`

⚠️ **No authentication.** `user_id` is a caller-supplied path value, not
a verified identity. Fine for a hackathon demo; do not treat as secure
multi-user storage. Data is stored **in-memory** and is lost on server
restart.

**`PUT /passport/{user_id}`** — create or update (upsert)

Request body:
```json
{
  "name": "Priya Sharma",
  "age": 24,
  "blood_group": "O+",
  "allergies": "Penicillin",
  "medications": "None",
  "chronic_diseases": "Asthma",
  "emergency_contact_name": "Raj Sharma",
  "emergency_contact_phone": "+91-9876543210"
}
```
`blood_group` is one of `A+ A- B+ B- AB+ AB- O+ O- UNKNOWN` (defaults
to `UNKNOWN` if omitted). Returns `200` with the saved record.

**`GET /passport/{user_id}`** — retrieve. Returns `404` if not found.

**`DELETE /passport/{user_id}`** — delete. Returns `404` if not found.

## Reliability & Fallback Behavior

`/analyze` is designed to **never crash and never leave the user with
nothing**, even if Gemini is completely down:

1. Transient errors (server overload, brief network issues) are
   automatically retried (up to 2 extra attempts, exponential backoff)
   before giving up.
2. If Gemini still can't be reached, or returns something that isn't
   valid/expected JSON, the app falls back to a conservative,
   keyword-based safety check (`app/ai/fallback.py`) - NOT a diagnosis
   engine. It only decides whether the described symptoms contain
   obvious emergency red flags (e.g. "chest pain," "unconscious") and
   escalates to `EMERGENCY` if so; otherwise it returns a safe
   `MODERATE` default telling the user AI analysis is temporarily
   unavailable.
3. Fallback responses are clearly distinguishable: `possible_conditions`
   is always empty, and the `disclaimer` explicitly states the AI
   service was unavailable.
4. Any other unexpected error anywhere in the app is caught by a global
   handler (`app/main.py`) and returns a clean `500` - never a raw
   stack trace.

## Model Configuration Note

Gemini's available/recommended models have changed multiple times
during development of this project (models get deprecated, free-tier
availability shifts). The current model is set via `GEMINI_MODEL` in
`.env`. **If `/analyze` starts returning `404` or `429` errors
mentioning a model name**, check
[the current model list](https://ai.google.dev/gemini-api/docs/models)
and update `GEMINI_MODEL` accordingly - this is expected occasional
maintenance, not a bug in this codebase.

## Scope & Limitations

This backend implements the AI integration only, per the hackathon's
AI Integration Brief:
- ✅ AI Symptom Analysis (`/analyze`)
- ✅ Health Passport storage (in-memory)
- ✅ SOS *decision* (`sos_recommended` field) - the AI only decides
  whether SOS should be recommended
- ❌ Not implemented here: actual SOS dispatch, location services, or
  contacting real emergency services - that's explicitly a separate
  backend/SOS-team responsibility per the project brief, and this app
  never attempts to simulate contacting real emergency services
- ❌ Not implemented here: authentication, persistent database, frontend

## Testing It Yourself

Use the interactive docs at `/docs` to try both endpoints without
needing curl or Postman - click "Try it out" on any endpoint, fill in
the example, and Execute.
