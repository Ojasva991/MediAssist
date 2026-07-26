"""
Health Passport document attachments (blood test, MRI, X-ray,
sonography reports, etc.).

Kept as its own small model file rather than folded into passport.py,
since these models describe a distinct sub-resource (files) with a
different lifecycle (upload/download/delete) from the passport record
itself.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentCategory(str, Enum):
    BLOOD_TEST = "BLOOD_TEST"
    MRI = "MRI"
    XRAY = "XRAY"
    SONOGRAPHY = "SONOGRAPHY"
    PRESCRIPTION = "PRESCRIPTION"
    OTHER = "OTHER"


class PassportDocumentMeta(BaseModel):
    """
    Metadata for one uploaded document - deliberately does NOT include
    the file bytes themselves (see app/storage/document_store.py). Used
    for the list endpoint; the actual file is fetched separately via
    the download endpoint, one file at a time, only when needed.
    """

    id: int
    filename: str
    content_type: str
    category: DocumentCategory
    file_size: int = Field(..., description="Size in bytes.")
    uploaded_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 7,
                "filename": "blood_panel_july.pdf",
                "content_type": "application/pdf",
                "category": "BLOOD_TEST",
                "file_size": 245678,
                "uploaded_at": "2026-07-26T10:15:00Z",
            }
        }
    }
