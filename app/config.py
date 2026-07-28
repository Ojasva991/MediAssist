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


class Settings:
    """Central place for all configuration values."""

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # App
    APP_NAME: str = os.getenv("APP_NAME", "Vaeda AI")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database (Postgres) - replaces the old Google Sheets storage.
    # Example: postgresql://user:password@host:5432/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")

    # CORS - comma-separated list of frontend origins allowed to call this API.
    # Defaults cover the deployed Vercel frontend + local dev (Vite's default
    # port). Override via env var to add/change origins without a code change.
    _default_origins = "https://medi-assist-nu.vercel.app,http://localhost:5173"
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
        """
        Fail fast and loud if required config is missing, instead of
        crashing later mid-request with a confusing error.
        """
        if not self.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env "
                "and add your Gemini API key."
            )
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set. Create a free Postgres database "
                "(Supabase/Neon/Render all work) and set its connection "
                "string as DATABASE_URL. See README for setup steps."
            )
        if not self.JWT_SECRET_KEY:
            raise RuntimeError(
                "JWT_SECRET_KEY is not set. Generate one and set it as an "
                "environment variable - see README for instructions."
            )


settings = Settings()
