"""
Health Passport document attachments - blood test, MRI, X-ray,
sonography reports, prescriptions, etc.

Same ownership-check pattern used everywhere else in this project: the
user_id in the URL must match the caller's own token, AND (for
download/delete) the specific document must actually belong to that
user - not just guessable by having a valid token for SOME account.
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.auth.dependencies import get_current_user_id
from app.models.document import DocumentCategory, PassportDocumentMeta
from app.storage.document_store import (
    DocumentValidationError,
    delete_document,
    get_document_file,
    get_document_owner,
    list_documents,
    save_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/passport", tags=["Health Passport Documents"])


def _ensure_self(user_id: str, current_user_id: str) -> None:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's documents.",
        )


@router.post("/{user_id}/documents", response_model=PassportDocumentMeta, status_code=201)
async def upload_document(
    user_id: str,
    category: DocumentCategory = Form(...),
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id),
) -> PassportDocumentMeta:
    """
    Upload a medical document (PDF or image) and tag it with a category
    (blood test, MRI, X-ray, sonography, prescription, or other).

    Rejects (400) files that are the wrong type, too large, or would
    put the user over their document limit - see
    app/storage/document_store.py for the exact caps and why they
    exist (files are stored directly in Postgres, not a separate
    object-storage service).
    """
    _ensure_self(user_id, current_user_id)
    file_bytes = await file.read()
    try:
        return save_document(
            user_id=user_id,
            filename=file.filename or "document",
            content_type=file.content_type or "application/octet-stream",
            category=category,
            file_bytes=file_bytes,
        )
    except DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/documents", response_model=list[PassportDocumentMeta])
def read_documents(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
) -> list[PassportDocumentMeta]:
    """List metadata for every document a user has uploaded (no file
    bytes - see GET /{user_id}/documents/{document_id} to download
    one). Most recent first."""
    _ensure_self(user_id, current_user_id)
    return list_documents(user_id)


@router.get("/{user_id}/documents/{document_id}")
def download_document(
    user_id: str,
    document_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> Response:
    """Download one document's actual file content."""
    _ensure_self(user_id, current_user_id)

    owner = get_document_owner(document_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="No document found with that id.")
    if owner != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this document.",
        )

    result = get_document_file(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No document found with that id.")
    file_bytes, filename, content_type = result

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{user_id}/documents/{document_id}")
def remove_document(
    user_id: str,
    document_id: int,
    current_user_id: str = Depends(get_current_user_id),
) -> dict:
    """Delete one uploaded document."""
    _ensure_self(user_id, current_user_id)

    owner = get_document_owner(document_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="No document found with that id.")
    if owner != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this document.",
        )

    delete_document(document_id)
    return {"status": "deleted", "document_id": document_id}
