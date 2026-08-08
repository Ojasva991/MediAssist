"""
Storage helpers for AIProviderUsageRecord (see app/storage/models.py).
"""

import logging
from datetime import datetime

from app.storage.db import get_session
from app.storage.models import AIProviderUsageRecord

logger = logging.getLogger(__name__)


def log_attempt(provider: str, success: bool, latency_ms: int | None) -> None:
    """
    Records one AI-gateway attempt. Called from app/ai/gateway.py on
    every Gemini/Groq call and once more when both fail ("all_failed").

    Deliberately swallows its own exceptions rather than propagating -
    this is pure observability for the admin dashboard, and a logging
    failure must never be able to turn a successful (or already-failed)
    AI call into a 500 for the actual person waiting on a symptom
    analysis. Worst case if this breaks: the analytics dashboard is
    missing a data point, not that someone's triage request failed.
    """
    try:
        session = get_session()
        try:
            session.add(
                AIProviderUsageRecord(provider=provider, success=success, latency_ms=latency_ms)
            )
            session.commit()
        finally:
            session.close()
    except Exception as e:
        logger.warning("Failed to log AI provider usage (non-fatal): %s", e)


def get_provider_stats(since: datetime) -> dict:
    """
    Returns {"gemini": {"success": n, "failure": n}, "groq": {...},
    "all_failed": n} for attempts since the given timestamp.
    "all_failed" counts requests where every provider failed and the
    caller fell through to the rule-engine-only response.
    """
    session = get_session()
    try:
        rows = (
            session.query(AIProviderUsageRecord)
            .filter(AIProviderUsageRecord.created_at >= since)
            .all()
        )
    finally:
        session.close()

    stats = {
        "gemini": {"success": 0, "failure": 0},
        "groq": {"success": 0, "failure": 0},
        "all_failed": 0,
    }
    for row in rows:
        if row.provider == "all_failed":
            stats["all_failed"] += 1
        elif row.provider in stats:
            key = "success" if row.success else "failure"
            stats[row.provider][key] += 1
    return stats


def get_average_latency_ms(provider: str, since: datetime) -> float | None:
    session = get_session()
    try:
        rows = (
            session.query(AIProviderUsageRecord.latency_ms)
            .filter(
                AIProviderUsageRecord.provider == provider,
                AIProviderUsageRecord.success.is_(True),
                AIProviderUsageRecord.created_at >= since,
                AIProviderUsageRecord.latency_ms.isnot(None),
            )
            .all()
        )
    finally:
        session.close()

    values = [r[0] for r in rows if r[0] is not None]
    return round(sum(values) / len(values), 1) if values else None
