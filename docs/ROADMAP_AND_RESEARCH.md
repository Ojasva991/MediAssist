# Schedule / workflow (start Mon 16 Nov 2026, ~14 weeks)

Rule: each phase ends with something runnable AND something you can cite in the paper.

| Weeks | Phase | Build | Paper output |
|---|---|---|---|
| 1 (16-22 Nov) | **Stabilise** | Rotate secrets; Neon DB; backend on Render + keep-alive; Cloudflare Pages; run test suite and fix failures; get 2-3 AI keys | Architecture diagram v1; list of reliability incidents (Overpass saga, Supabase pause, Gemini quota) = motivation section |
| 2-3 | **LLM independence** | Tune provider order; add `local` Ollama provider; log provider/latency/failure (already in `ai_provider_usage`) | Table: availability + latency per provider |
| 4-5 | **Android app** | Capacitor build; native geolocation, local notifications (real reminders), speech plugin; APK to testers | Usability/feature table web vs app |
| 6-7 | **Safety hardening** | Hindi/Hinglish red-flag keywords; move documents off Postgres; password reset; Alembic | Safety design section (rule floor, scrubber, disclaimers) |
| 8-9 | **Evaluation set** | Build 100-200 synthetic vignettes with a gold urgency label (EMERGENCY/HIGH/MODERATE/LOW), reviewed by a doctor; include a public benchmark such as the 45 vignettes from Semigran et al. (BMJ 2015) if licence permits | Dataset + labelling protocol |
| 10-11 | **Experiments** | Batch-run vignettes through configurations (below), save JSON results | Results tables/figures |
| 12 | **User study (optional)** | 15-30 volunteers, SUS usability form, consent form; no real patient data | Usability results |
| 13-14 | **Write + polish** | Related work, threats to validity, limitations, ethics | Draft -> advisor review |

## Research paper outline
**Working title:** *Vaeda: a hybrid rule-engine + multi-LLM triage assistant that stays available on free-tier infrastructure.*

**Research questions**
1. RQ1 (safety): Does a deterministic red-flag floor reduce dangerous under-triage versus an LLM alone?
2. RQ2 (reliability): How much availability does a free-provider cascade add versus any single provider?
3. RQ3 (quality): How do different free/open models (Llama 3.3 70B, Mistral Small, Gemini, a small local 8B) compare on triage accuracy and latency?
4. RQ4 (RAG): Does retrieval of curated guidance improve agreement with gold labels?

**Experiment configs (ablation):** rules-only; LLM-only (per model); LLM + rule floor (current system); LLM + floor + RAG; each with simulated provider outages for RQ2.

**Metrics:** emergency recall (primary - misses are the costly error), under-triage rate, over-triage rate, exact-match and within-one-level accuracy, Cohen's kappa vs gold, p50/p95 latency, availability %, fallback rate. Report confidence intervals.

**Honest framing:** triage-support research, not a diagnostic device; no clinical-effectiveness claims; limitations: synthetic vignettes, English-first, free-tier variability, models change over time (record model IDs and dates for reproducibility). Ethics: only synthetic data, or consented volunteers with institutional approval if you collect user data; don't publish real user logs.

**Reproducibility:** keep `eval/` scripts + vignette file + results JSON in the repo; pin model IDs and run dates in a table.
