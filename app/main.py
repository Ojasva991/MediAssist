"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import analyze, passport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered symptom triage assistant. "
        "This tool does NOT diagnose diseases - it estimates urgency "
        "and recommends next steps only."
    ),
    version="0.1.0",
)

# Allow the frontend (React/Flutter dev server, etc.) to call this API.
# Wide open for hackathon purposes - tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last-resort safety net for the whole app.

    Individual routes (like /analyze) already handle their own known
    failure modes and return clean errors. This handler only fires for
    something truly unexpected anywhere in the app - a bug, a typo, an
    edge case nobody anticipated. Without this, FastAPI's default
    behavior can leak a raw stack trace to the caller, which is bad
    practice for any API and especially a health-related one.

    Every error response from this API therefore has the SAME shape:
    {"detail": "..."} - whether it's a normal 404/422 or this fallback.
    """
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )


@app.get("/health", tags=["System"])
def health_check() -> dict:
    """Simple liveness check so the frontend/backend teams know the API is up."""
    return {"status": "ok", "service": settings.APP_NAME}


app.include_router(analyze.router)
app.include_router(passport.router)