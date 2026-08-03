"""
GET /admin/analytics - admin-only (see app/auth/admin.py).

Every number here comes from a real query against existing tables -
see app/models/analytics.py's module docstring for the "don't fabricate,
be explicit about gaps" principle this follows. Two real gaps were found
and handled honestly while building this, not glossed over:
1. llm_severity is never persisted to history, so a "rule engine
   overrode the AI" metric isn't computable from existing data - that
   field was removed from the response model rather than faking it.
2. UserRecord had no created_at column at all - added one
   (nullable, existing rows will be NULL) rather than reporting a fake
   signup timeline. Needs a manual ALTER TABLE on production, same as
   this project's other "new column on an existing table" gotchas.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.auth.admin import require_admin
from app.models.analytics import (
    AdminAnalyticsOut,
    AIProviderStats,
    DailyCount,
    ProviderCounts,
    SeverityBreakdown,
)
from app.storage.ai_usage_store import get_average_latency_ms, get_provider_stats
from app.storage.db import get_session
from app.storage.models import (
    AnalysisFeedbackRecord,
    AnalysisHistoryRecord,
    CaregiverLinkRecord,
    PassportDocumentRecord,
    ReminderRecord,
    UserRecord,
)

router = APIRouter(prefix="/admin", tags=["Admin Analytics"])


def _daily_counts(timestamps: list[datetime]) -> list[DailyCount]:
    buckets: dict[str, int] = defaultdict(int)
    for ts in timestamps:
        if ts is None:
            continue  # e.g. pre-existing users with no created_at - see module docstring
        buckets[ts.date().isoformat()] += 1
    return [DailyCount(date=d, count=c) for d, c in sorted(buckets.items())]


@router.get("/analytics", response_model=AdminAnalyticsOut)
def get_analytics(
    window_days: int = Query(default=30, ge=1, le=365),
    _admin_user_id: str = Depends(require_admin),
) -> AdminAnalyticsOut:
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    session = get_session()
    try:
        all_users = session.query(UserRecord.created_at).all()
        total_users = len(all_users)
        signups_by_day = _daily_counts([u[0] for u in all_users])

        history_rows = session.query(AnalysisHistoryRecord).all()
        total_analyses = len(history_rows)
        analyses_by_day = _daily_counts([h.created_at for h in history_rows])

        severity_counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "EMERGENCY": 0}
        sos_count = 0
        for h in history_rows:
            if h.severity in severity_counts:
                severity_counts[h.severity] += 1
            if h.sos_recommended:
                sos_count += 1

        total_reminders = session.query(ReminderRecord).count()
        active_reminders = (
            session.query(ReminderRecord).filter(ReminderRecord.is_active.is_(True)).count()
        )

        caregiver_active = (
            session.query(CaregiverLinkRecord)
            .filter(CaregiverLinkRecord.status == "active")
            .count()
        )
        caregiver_pending = (
            session.query(CaregiverLinkRecord)
            .filter(CaregiverLinkRecord.status == "pending")
            .count()
        )
        caregiver_revoked = (
            session.query(CaregiverLinkRecord)
            .filter(CaregiverLinkRecord.status == "revoked")
            .count()
        )

        total_documents = session.query(PassportDocumentRecord).count()
        total_document_bytes = sum(
            f[0] for f in session.query(PassportDocumentRecord.file_size).all()
        )

        feedback_positive = (
            session.query(AnalysisFeedbackRecord)
            .filter(AnalysisFeedbackRecord.is_helpful.is_(True))
            .count()
        )
        feedback_negative = (
            session.query(AnalysisFeedbackRecord)
            .filter(AnalysisFeedbackRecord.is_helpful.is_(False))
            .count()
        )
    finally:
        session.close()

    provider_stats = get_provider_stats(since)

    return AdminAnalyticsOut(
        generated_at=datetime.now(timezone.utc).isoformat(),
        window_days=window_days,
        total_users=total_users,
        signups_by_day=signups_by_day,
        total_analyses=total_analyses,
        analyses_by_day=analyses_by_day,
        severity_breakdown=SeverityBreakdown(**severity_counts),
        sos_recommended_count=sos_count,
        total_reminders=total_reminders,
        active_reminders=active_reminders,
        caregiver_links_active=caregiver_active,
        caregiver_links_pending=caregiver_pending,
        caregiver_links_revoked=caregiver_revoked,
        total_passport_documents=total_documents,
        total_document_storage_bytes=total_document_bytes,
        feedback_positive=feedback_positive,
        feedback_negative=feedback_negative,
        ai_provider_stats=AIProviderStats(
            gemini=ProviderCounts(**provider_stats["gemini"]),
            groq=ProviderCounts(**provider_stats["groq"]),
            all_failed=provider_stats["all_failed"],
            gemini_avg_latency_ms=get_average_latency_ms("gemini", since),
            groq_avg_latency_ms=get_average_latency_ms("groq", since),
        ),
    )
