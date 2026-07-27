"""
Storage helpers for StagedGuidanceDocument (see app/storage/models.py).

Same pattern as the other *_store.py modules in this project: routes
never touch SQLAlchemy sessions/models directly, they call a function
here.
"""

from datetime import datetime, timezone

from app.storage.db import get_session
from app.storage.models import StagedGuidanceDocument


def create_staged_documents(rows: list[dict]) -> list[int]:
    """
    Bulk-insert staged rows from the ingestion job. Each dict must have
    the same keys as StagedGuidanceDocument's ingestible columns
    (source_id, source_url, license, attribution, topic_hint, content).
    Always inserted as status="pending_review" - the ingestion job has
    no way to bypass review, by design.
    """
    session = get_session()
    try:
        records = [StagedGuidanceDocument(status="pending_review", **row) for row in rows]
        session.add_all(records)
        session.commit()
        return [r.id for r in records]
    finally:
        session.close()


def list_staged_documents(status: str | None = "pending_review") -> list[StagedGuidanceDocument]:
    session = get_session()
    try:
        query = session.query(StagedGuidanceDocument)
        if status is not None:
            query = query.filter(StagedGuidanceDocument.status == status)
        return query.order_by(StagedGuidanceDocument.ingested_at.desc()).all()
    finally:
        session.close()


def get_staged_document(document_id: int) -> StagedGuidanceDocument | None:
    session = get_session()
    try:
        return (
            session.query(StagedGuidanceDocument)
            .filter(StagedGuidanceDocument.id == document_id)
            .first()
        )
    finally:
        session.close()


def review_staged_document(
    document_id: int, *, approve: bool, reviewer_user_id: str, note: str | None
) -> StagedGuidanceDocument | None:
    """
    Marks a staged document approved or rejected. Does NOT touch the
    live RAG corpus (app/rag/corpus.py) - that's a deliberate second,
    separate step (see app/routes/rag_review.py's docstring) so an
    approval alone never silently changes what the AI actually cites.
    """
    session = get_session()
    try:
        record = (
            session.query(StagedGuidanceDocument)
            .filter(StagedGuidanceDocument.id == document_id)
            .first()
        )
        if record is None:
            return None
        record.status = "approved" if approve else "rejected"
        record.reviewed_by = reviewer_user_id
        record.review_note = note
        record.reviewed_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()
