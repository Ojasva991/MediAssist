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
from app.routes import analyze, auth, passport

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Swagger / OpenAPI Tags
# ---------------------------------------------------------------------

tags_metadata = [
    {
        "name": "System",
        "description": "System status and health monitoring endpoints.",
    },
    {
        "name": "Authentication",
        "description": "Sign up, log in, and obtain access tokens.",
    },
    {
        "name": "Symptom Analysis",
        "description": (
            "Analyze user symptoms using AI to estimate medical urgency "
            "and recommend the next appropriate action."
        ),
    },
    {
        "name": "Health Passport",
        "description": (
            "Create, update, retrieve and delete a user's emergency "
            "medical information. Requires authentication."
        ),
    },
]

# ---------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------

app = FastAPI(
    title="MediAssist AI",
    description="""
# 🩺 MediAssist AI

AI-powered healthcare triage assistant.

MediAssist AI helps users:

- Analyze symptoms using AI
- Estimate urgency
- Store a digital Health Passport
- Support emergency response

---

## Features

✅ AI Symptom Analysis

✅ Health Passport

✅ Emergency SOS Support

---

⚠️ **Medical Disclaimer**

This application **does NOT diagnose diseases** and **is NOT a substitute
for professional medical advice**.

Always consult a qualified healthcare professional during medical emergencies.
""",
    version="1.0.0",
    summary="AI-powered healthcare triage and emergency assistance platform",
    contact={
        "name": "MediAssist AI Team",
        "email": "team@mediassist.ai",
    },
    license_info={
        "name": "MIT License",
    },
    openapi_tags=tags_metadata,
)

# ---------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Global fallback error handler.
    Ensures unexpected errors always return a consistent JSON response.
    """

    logger.exception(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected server error occurred. Please try again."
        },
    )


# ---------------------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------------------


@app.get(
    "/",
    tags=["System"],
    summary="API Information",
    description="Returns basic information about the MediAssist AI API.",
)
def root():
    return {
        "project": "MediAssist AI",
        "version": "1.0.0",
        "status": "Running",
        "documentation": "/docs",
        "health_check": "/health",
    }


# ---------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Checks whether the API service is healthy and operational.",
)
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "ai_service": "online",
    }


# ---------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(passport.router)