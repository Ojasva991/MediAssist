"""
Postgres-backed storage for Symptom Analysis History.

Same pattern as passport_store.py: a small set of plain functions that
hide the SQLAlchemy session details from route code.
"""

import logging
from typing import Optional

from app.models.history import AnalysisHistoryItem
from app.models.symptom import SymptomAnalysisRequest, SymptomAnalysisResponse
from app.storage.db import get_session
from app.storage.models import AnalysisHistoryRecord

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
) -> None:
    """
    Save one analysis to a user's history.

    Deliberately returns nothing and is meant to be called in a
    try/except by the caller (see app/routes/analyze.py) - a failure
    to save history should never prevent the user from getting their
    actual analysis result back.
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
    finally:
        session.close()


def get_history(user_id: str, limit: Optional[int] = None) -> list[AnalysisHistoryItem]:
    """
    Return a user's past analyses, most recent first.

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
            )
            for r in records
        ]
    finally:
        session.close()
