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

    # Google Sheets (Health Passport persistent storage)
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_SHEETS_CREDENTIALS: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")

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
        if not self.GOOGLE_SHEET_ID or not self.GOOGLE_SHEETS_CREDENTIALS:
            raise RuntimeError(
                "GOOGLE_SHEET_ID and GOOGLE_SHEETS_CREDENTIALS must both be set "
                "for Health Passport storage. See README for setup steps."
            )
        if not self.JWT_SECRET_KEY:
            raise RuntimeError(
                "JWT_SECRET_KEY is not set. Generate one and set it as an "
                "environment variable - see README for instructions."
            )


settings = Settings()
