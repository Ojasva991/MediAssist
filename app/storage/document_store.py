"""
Postgres-backed storage for Health Passport document attachments (blood
test, MRI, X-ray, sonography reports, etc.).

See the docstring on PassportDocumentRecord (app/storage/models.py) for
why files are stored as bytes directly in Postgres rather than in a
separate object-storage service, and why that means real limits apply
here (enforced below) rather than being "unlimited storage."
"""

from typing import Optional

from app.models.document import DocumentCategory, PassportDocumentMeta
from app.storage.db import get_session
from app.storage.models import PassportDocumentRecord

# Conservative caps given files live directly in Postgres (see the
# PassportDocumentRecord docstring) - free-tier Postgres (Supabase/Neon/
# Render) typically caps total database size in the low hundreds of MB.
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB per file
MAX_DOCUMENTS_PER_USER = 20

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


class DocumentValidationError(ValueError):
    """Raised for any client-fixable problem with an upload (too large,
    wrong type, too many documents already). The route layer catches
    this and returns 400 with the message as-is - always safe to show
    directly to the user, never an internal detail."""


def _to_meta(record: PassportDocumentRecord) -> PassportDocumentMeta:
    return PassportDocumentMeta(
        id=record.id,
        filename=record.filename,
        content_type=record.content_type,
        category=record.category,
        file_size=record.file_size,
        uploaded_at=record.uploaded_at,
    )


def save_document(
    user_id: str,
    filename: str,
    content_type: str,
    category: DocumentCategory,
    file_bytes: bytes,
) -> PassportDocumentMeta:
    """
    Validate and store one uploaded document. Raises
    DocumentValidationError (never a generic exception) for anything
    the uploader can actually fix: wrong file type, file too large, or
    already at the per-user document cap.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise DocumentValidationError(
            f"Unsupported file type '{content_type}'. Allowed: PDF, JPEG, PNG, WEBP."
        )
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise DocumentValidationError(
            f"File is too large ({len(file_bytes) / (1024 * 1024):.1f} MB). "
            f"Maximum is {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB per file."
        )
    if not file_bytes:
        raise DocumentValidationError("Uploaded file is empty.")

    session = get_session()
    try:
        existing_count = (
            session.query(PassportDocumentRecord)
            .filter(PassportDocumentRecord.user_id == user_id)
            .count()
        )
        if existing_count >= MAX_DOCUMENTS_PER_USER:
            raise DocumentValidationError(
                f"You've reached the limit of {MAX_DOCUMENTS_PER_USER} documents. "
                "Delete an older one before uploading a new one."
            )

        record = PassportDocumentRecord(
            user_id=user_id,
            filename=filename[:255],
            content_type=content_type,
            category=category.value,
            file_size=len(file_bytes),
            file_data=file_bytes,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return _to_meta(record)
    finally:
        session.close()


def list_documents(user_id: str) -> list[PassportDocumentMeta]:
    """Metadata only (no file bytes) for every document a user has
    uploaded, most recent first."""
    session = get_session()
    try:
        records = (
            session.query(PassportDocumentRecord)
            .filter(PassportDocumentRecord.user_id == user_id)
            .order_by(PassportDocumentRecord.id.desc())
            .all()
        )
        return [_to_meta(r) for r in records]
    finally:
        session.close()


def get_document_owner(document_id: int) -> Optional[str]:
    """Return the user_id that owns a document, or None if it doesn't
    exist. Used to enforce ownership before download/delete."""
    session = get_session()
    try:
        record = session.get(PassportDocumentRecord, document_id)
        return record.user_id if record else None
    finally:
        session.close()


def get_document_file(document_id: int) -> Optional[tuple[bytes, str, str]]:
    """Return (file_bytes, filename, content_type) for download, or
    None if the document doesn't exist. Ownership must already have
    been checked by the caller (see app/routes/documents.py)."""
    session = get_session()
    try:
        record = session.get(PassportDocumentRecord, document_id)
        if record is None:
            return None
        return record.file_data, record.filename, record.content_type
    finally:
        session.close()


def delete_document(document_id: int) -> bool:
    """Delete a document by id. Returns True if it existed and was
    removed. Ownership must already have been checked by the caller."""
    session = get_session()
    try:
        record = session.get(PassportDocumentRecord, document_id)
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True
    finally:
        session.close()
