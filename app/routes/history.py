"""
/history routes - HTTP layer for the Symptom Analysis History feature.

Requires authentication, same pattern as app/routes/passport.py: the
user_id in the URL must match the caller's token, so one account can
never read another account's analysis history.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.history import AnalysisHistoryItem
from app.storage.history_store import get_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["Analysis History"])


@router.get("/{user_id}", response_model=list[AnalysisHistoryItem])
def read_history(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    current_user_id: str = Depends(get_current_user_id),
) -> list[AnalysisHistoryItem]:
    """
    Retrieve a user's past symptom analyses, most recent first.

    Only analyses made while logged in are ever saved (see
    app/routes/analyze.py) - logged-out /analyze calls leave no history.
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user's history.",
        )
    return get_history(user_id, limit=limit)
