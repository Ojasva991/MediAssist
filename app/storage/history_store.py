"""
Postgres-backed storage for Symptom Analysis History and per-analysis
feedback.

Same pattern as passport_store.py: a small set of plain functions that
hide the SQLAlchemy session details from route code.
"""

import logging
from typing import Optional

from app.models.history import AnalysisHistoryItem
from app.models.symptom import SymptomAnalysisRequest, SymptomAnalysisResponse
from app.storage.db import get_session
from app.storage.models import AnalysisFeedbackRecord, AnalysisHistoryRecord

logger = logging.getLogger(__name__)

# Cap how many history rows a single user can accumulate to be returned/
# scanned - prevents a single very active user (or an automated abuse
# pattern slipping past the /analyze rate limit) from making their own
# history query slow. Doesn't limit how many are stored, just returned.
_MAX_HISTORY_RESULTS = 50


def save_analysis(
    user_id: str,
    request: SymptomAnalysisRequest,
    response: SymptomAnalysisResponse,
) -> int:
    """
    Save one analysis to a user's history and return its new history_id.

    The caller (see app/routes/analyze.py) attaches this id to the
    /analyze response so the frontend can later submit feedback against
    this specific analysis via POST /history/{user_id}/{history_id}/feedback.
    Meant to be called in a try/except by the caller - a failure to save
    history should never prevent the user from getting their actual
    analysis result back.
    """
    session = get_session()
    try:
        record = AnalysisHistoryRecord(
            user_id=user_id,
            age=request.age,
            gender=request.gender,
            symptoms=request.symptoms,
            duration=request.duration,
            existing_conditions=request.existing_conditions,
            possible_conditions=response.possible_conditions,
            severity=response.severity.value,
            recommended_action=response.recommended_action,
            sos_recommended=response.sos_recommended,
            disclaimer=response.disclaimer,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.id
    finally:
        session.close()


def get_history(user_id: str, limit: Optional[int] = None) -> list[AnalysisHistoryItem]:
    """
    Return a user's past analyses, most recent first, each annotated
    with any feedback already given (None if none was given yet).

    `limit` defaults to _MAX_HISTORY_RESULTS if not given, and is always
    capped at that value even if a caller asks for more.
    """
    effective_limit = min(limit or _MAX_HISTORY_RESULTS, _MAX_HISTORY_RESULTS)

    session = get_session()
    try:
        records = (
            session.query(AnalysisHistoryRecord)
            .filter(AnalysisHistoryRecord.user_id == user_id)
            .order_by(AnalysisHistoryRecord.created_at.desc())
            .limit(effective_limit)
            .all()
        )

        record_ids = [r.id for r in records]
        feedback_map: dict[int, bool] = {}
        if record_ids:
            feedback_rows = (
                session.query(AnalysisFeedbackRecord)
                .filter(AnalysisFeedbackRecord.history_id.in_(record_ids))
                .all()
            )
            feedback_map = {f.history_id: f.is_helpful for f in feedback_rows}

        return [
            AnalysisHistoryItem(
                id=r.id,
                created_at=r.created_at,
                age=r.age,
                gender=r.gender,
                symptoms=r.symptoms,
                duration=r.duration,
                existing_conditions=r.existing_conditions,
                possible_conditions=r.possible_conditions,
                severity=r.severity,
                recommended_action=r.recommended_action,
                sos_recommended=r.sos_recommended,
                disclaimer=r.disclaimer,
                feedback=feedback_map.get(r.id),
            )
            for r in records
        ]
    finally:
        session.close()


def get_history_owner(history_id: int) -> Optional[str]:
    """
    Return the user_id that owns a given history entry, or None if no
    such entry exists. Used to enforce ownership before accepting
    feedback on someone else's analysis (see app/routes/history.py).
    """
    session = get_session()
    try:
        record = (
            session.query(AnalysisHistoryRecord)
            .filter(AnalysisHistoryRecord.id == history_id)
            .first()
        )
        return record.user_id if record else None
    finally:
        session.close()


def save_feedback(user_id: str, history_id: int, is_helpful: bool) -> None:
    """
    Record thumbs-up/down feedback on a saved analysis. Upserts - a
    second submission for the same history_id updates the existing
    row (letting someone change their mind) rather than creating a
    duplicate, since `history_id` is a unique column.

    Ownership must already have been checked by the caller (see
    app/routes/history.py) before this is called.
    """
    session = get_session()
    try:
        existing = (
            session.query(AnalysisFeedbackRecord)
            .filter(AnalysisFeedbackRecord.history_id == history_id)
            .first()
        )
        if existing:
            existing.is_helpful = is_helpful
            existing.user_id = user_id
        else:
            session.add(
                AnalysisFeedbackRecord(
                    history_id=history_id, user_id=user_id, is_helpful=is_helpful
                )
            )
        session.commit()
    finally:
        session.close()
