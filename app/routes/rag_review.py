"""
/rag-review routes - the human-review gate for the hybrid-retrieval
staging pipeline (see app/rag/ingest.py, app/storage/models.py's
StagedGuidanceDocument).

Deliberately NOT wired to automatically feed into the live RAG corpus
(app/rag/corpus.py) on approval. Approving a staged document here only
changes its status - promoting an approved entry into the corpus that
/analyze actually retrieves from is a separate, explicit step (see
app/rag/promote.py) done by a person reading the generated diff, same
spirit as this project's existing "new columns need a manual ALTER
TABLE, nothing happens automatically" philosophy. Two separate gates,
not one.

Access control: this project doesn't have general role-based access
control yet (see PROJECT_STATE.md backlog), so these routes are gated
by a simple allowlist (settings.ADMIN_USER_IDS) as a stopgap - anyone
whose user_id isn't in that list gets 403, including any normal logged
in user. Revisit this if/when real RBAC lands.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_id
from app.config import settings
from app.storage.staged_guidance_store import (
    get_staged_document,
    list_staged_documents,
    review_staged_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag-review", tags=["Guidance Review (admin)"])


def _require_admin(current_user_id: str = Depends(get_current_user_id)) -> str:
    if current_user_id not in settings.ADMIN_USER_IDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Not authorized to review staged guidance documents. "
                "This is an admin-only area."
            ),
        )
    return current_user_id


class StagedDocumentOut(BaseModel):
    id: int
    source_id: str
    source_url: str
    license: str
    attribution: str
    topic_hint: str | None
    content: str
    status: str
    review_note: str | None
    reviewed_by: str | None

    model_config = {"from_attributes": True}


class ReviewDecisionRequest(BaseModel):
    approve: bool = Field(..., description="True to approve, False to reject.")
    note: str | None = Field(
        default=None,
        description=(
            "Why this was approved/rejected. For approvals, reviewers should "
            "use this to explicitly reconfirm the source's license still "
            "applies (e.g. project is still non-commercial) - see "
            "app/rag/sources.py's licensing notes for what to check."
        ),
    )


@router.get("", response_model=list[StagedDocumentOut])
def list_pending(
    status_filter: str = Query(
        default="pending_review",
        alias="status",
        description="pending_review | approved | rejected | all",
    ),
    _admin_user_id: str = Depends(_require_admin),
) -> list[StagedDocumentOut]:
    query_status = None if status_filter == "all" else status_filter
    return list_staged_documents(status=query_status)


@router.post("/{document_id}/decision", response_model=StagedDocumentOut)
def submit_decision(
    document_id: int,
    payload: ReviewDecisionRequest,
    admin_user_id: str = Depends(_require_admin),
) -> StagedDocumentOut:
    existing = get_staged_document(document_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No staged guidance document found with that id.",
        )
    if existing.status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"This document was already reviewed (status={existing.status}). "
                "Re-review isn't supported here to keep a clean decision trail."
            ),
        )

    updated = review_staged_document(
        document_id,
        approve=payload.approve,
        reviewer_user_id=admin_user_id,
        note=payload.note,
    )
    logger.info(
        "Staged guidance document %s %s by %s",
        document_id,
        "approved" if payload.approve else "rejected",
        admin_user_id,
    )
    return updated
