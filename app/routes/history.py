"""
/history routes - HTTP layer for the Symptom Analysis History feature.

Requires authentication, same pattern as app/routes/passport.py: the
user_id in the URL must match the caller's token, so one account can
never read another account's analysis history.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.history import AnalysisHistoryItem, FeedbackRequest
from app.storage.history_store import get_history, get_history_owner, save_feedback

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


@router.post("/{user_id}/{history_id}/feedback")
def submit_feedback(
    user_id: str,
    history_id: int,
    payload: FeedbackRequest,
    current_user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Submit thumbs-up/down feedback on one specific past analysis.

    Two ownership checks, deliberately: the URL's user_id must match the
    caller's token (same pattern as every other route here), AND the
    history_id itself must actually belong to that user - otherwise
    someone could guess another user's history_id and leave feedback on
    an analysis that was never theirs to react to.
    """
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to act on this user's history.",
        )

    owner = get_history_owner(history_id)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found with that id.",
        )
    if owner != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to give feedback on this analysis.",
        )

    save_feedback(current_user_id, history_id, payload.is_helpful)
    return {"status": "recorded", "history_id": history_id, "is_helpful": payload.is_helpful}
