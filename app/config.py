"""
Application configuration.

Loads settings from environment variables (via a .env file in development).
Keeping this in one place means no other module has to know HOW config
is loaded - they just import `settings`.
"""

import os
from dotenv import load_dotenv

# Load variables from .env into the process environment.
# In production you'd typically set real env vars instead of using a file.
load_dotenv()


def _normalize_database_url(url: str) -> str:
    """Accept what hosts hand out (postgres://...) and make SQLAlchemy +
    psycopg2 happy. Neon requires TLS, so add sslmode=require if missing."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql") and "sslmode=" not in url and "localhost" not in url and "127.0.0.1" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


class Settings:
    """Central place for all configuration values."""

    # ---- AI providers (all optional; configure as many as you like) ----
    # Order the gateway tries them in. Providers with no key are skipped.
    # See app/ai/gateway.py. "local" = your own Ollama/llama.cpp server.
    AI_PROVIDER_ORDER: list[str] = [
        p.strip().lower()
        for p in os.getenv(
            "AI_PROVIDER_ORDER", "groq,cerebras,mistral,openrouter,cloudflare,local,gemini"
        ).split(",")
        if p.strip()
    ]
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))

    # Gemini (now just one optional provider among several)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Cerebras / Mistral / OpenRouter / Cloudflare Workers AI. Model IDs
    # on free tiers change often - override via env, don't edit code.
    CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")
    CEREBRAS_MODEL: str = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    MISTRAL_VISION_MODEL: str = os.getenv("MISTRAL_VISION_MODEL", "mistral-small-latest")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    OPENROUTER_VISION_MODEL: str = os.getenv("OPENROUTER_VISION_MODEL", "")
    CLOUDFLARE_ACCOUNT_ID: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    CLOUDFLARE_API_TOKEN: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    CLOUDFLARE_MODEL: str = os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.1-8b-instruct")
    # Self-hosted OpenAI-compatible server, e.g. Ollama: http://host:11434/v1
    LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_BASE_URL", "")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "")
    LOCAL_LLM_VISION_MODEL: str = os.getenv("LOCAL_LLM_VISION_MODEL", "")
    LOCAL_LLM_API_KEY: str = os.getenv("LOCAL_LLM_API_KEY", "")

    # App
    APP_NAME: str = os.getenv("APP_NAME", "Vaeda AI")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database (Postgres) - replaces the old Google Sheets storage.
    # Example: postgresql://user:password@host:5432/dbname
    DATABASE_URL: str = _normalize_database_url(os.getenv("DATABASE_URL", ""))

    # Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")

    # CORS - comma-separated list of frontend origins allowed to call this API.
    # Defaults cover the deployed Vercel frontend + local dev (Vite's default
    # port). Override via env var to add/change origins without a code change.
    # capacitor://localhost, https://localhost and http://localhost are the
    # origins a Capacitor-wrapped Android/iOS app sends.
    _default_origins = (
        "https://medi-assist-nu.vercel.app,http://localhost:5173,"
        "capacitor://localhost,https://localhost,http://localhost"
    )
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
        if origin.strip()
    ]

    # Rate limiting - format is "<count>/<period>", e.g. "10/minute".
    # See slowapi/limits docs for supported period strings.
    # Applied per client IP address (see app/rate_limit.py).
    RATE_LIMIT_ANALYZE: str = os.getenv("RATE_LIMIT_ANALYZE", "10/minute")

    # Image-based analysis (POST /analyze/image) - a lower limit than
    # text /analyze, since a multimodal Gemini call costs more per
    # request. See app/routes/analyze.py.
    RATE_LIMIT_ANALYZE_IMAGE: str = os.getenv("RATE_LIMIT_ANALYZE_IMAGE", "5/minute")

    # Number of trusted reverse proxies in front of the app (Render/Cloud
    # Run = 1; add 1 if Cloudflare proxies in front too). Used for the
    # client IP in rate limiting - see app/rate_limit.py.
    TRUSTED_PROXY_HOPS: int = int(os.getenv("TRUSTED_PROXY_HOPS", "1"))

    # Groq (free, no card). Vision model is used for /analyze/image.
    GROQ_VISION_MODEL: str = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    # Second AI provider for the gateway's fallback chain (see
    # app/ai/gateway.py) - free, no credit card. Empty by default:
    # the gateway skips Groq entirely (not an error) if this isn't
    # set, so the app keeps working with just Gemini configured.
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Public, deterministic (no AI call) - see app/interactions/matcher.py.
    RATE_LIMIT_DRUG_INTERACTIONS: str = os.getenv("RATE_LIMIT_DRUG_INTERACTIONS", "20/minute")

    # OpenStreetMap's Overpass API - no key/billing account needed.
    # See app/emergency/hospital_lookup.py for why this was chosen over
    # a paid places API.
    #
    # A LIST, not a single URL: overpass-api.de (the original/default
    # public instance) is known to actively rate-limit or block
    # shared/datacenter IP ranges - exactly the situation with Render's
    # shared free-tier egress IPs (confirmed in production: got an
    # outright "Connection refused" from it, not a timeout). Mirror
    # instances differ in how permissive they are, so this tries each
    # in order and only fails if all of them do.
    #
    # IMPORTANT: every URL here must have GLOBAL coverage. Some public
    # Overpass mirrors intentionally host only a regional OSM extract
    # (e.g. overpass.osm.ch explicitly only contains Switzerland's
    # data, confirmed on its own site) - querying one of those for a
    # location outside its region silently succeeds with an empty
    # result, which looks identical to "genuinely nothing nearby."
    # That was an actual production bug here once already - don't
    # add a regional-only mirror back into this list without checking.
    OVERPASS_API_URLS: list[str] = [
        url.strip()
        for url in os.getenv(
            "OVERPASS_API_URLS",
            "https://overpass.private.coffee/api/interpreter,"
            "https://overpass-api.de/api/interpreter,"
            "https://api.openstreetmap.fr/oapi/interpreter",
        ).split(",")
        if url.strip()
    ]
    RATE_LIMIT_NEARBY_HOSPITALS: str = os.getenv("RATE_LIMIT_NEARBY_HOSPITALS", "20/minute")

    # Comma-separated list of user_id values allowed to review/approve
    # staged RAG guidance documents (see app/routes/rag_review.py).
    # This project has no general role-based access control yet (it's
    # still on the backlog in PROJECT_STATE.md) - this env var is a
    # deliberate stopgap, not a real permissions system. A user_id is
    # the deterministic sha256(lowercased/trimmed email)[:24] computed
    # in app/auth/security.py; compute it for whichever email(s) should
    # be allowed to review, and set them here. Empty by default, which
    # means the review endpoints reject everyone until this is set -
    # fail closed, not open.
    ADMIN_USER_IDS: list[str] = [
        uid.strip() for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip()
    ]

    def validate(self) -> None:
        """Fail fast on missing/unsafe config instead of failing mid-request."""
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set. Create a free Neon Postgres database "
                "and set its connection string. See docs/MIGRATION.md."
            )
        if not self.JWT_SECRET_KEY:
            raise RuntimeError(
                "JWT_SECRET_KEY is not set (an empty signing key would make "
                "login tokens forgeable). Generate one: "
                'python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if self.ENVIRONMENT.lower() == "production":
            if len(self.JWT_SECRET_KEY) < 32:
                raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production.")
            if "*" in self.ALLOWED_ORIGINS:
                raise RuntimeError("ALLOWED_ORIGINS must not contain '*' in production.")


settings = Settings()
