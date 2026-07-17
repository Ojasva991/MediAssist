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
    APP_NAME: str = os.getenv("APP_NAME", "MediAssist AI")
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
