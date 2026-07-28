"""
SQLAlchemy table definitions for Postgres-backed storage.

Mirrors the exact columns the old Google Sheets tabs used, so no data
shape changes for the rest of the app - just where it's stored.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, LargeBinary, func

from app.storage.db import Base


class UserRecord(Base):
    __tablename__ = "users"

    user_id = Column(String(24), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)


class PassportRecord(Base):
    __tablename__ = "passports"

    user_id = Column(String(24), primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    # Nullable at the DB level (unlike the Pydantic model, where it's
    # required for all NEW/updated passports) so this stays backward
    # compatible with passport rows that already exist in production from
    # before this column was added. Base.metadata.create_all() only creates
    # MISSING tables - it does not ALTER existing ones - so this column
    # will not appear in an already-existing `passports` table until you
    # run, once, against the real database:
    #   ALTER TABLE passports ADD COLUMN gender VARCHAR(30);
    gender = Column(String(30), nullable=True)
    blood_group = Column(String(10), nullable=False, default="UNKNOWN")
    allergies = Column(String(500), nullable=True)
    medications = Column(String(500), nullable=True)
    chronic_diseases = Column(String(500), nullable=True)
    emergency_contact_name = Column(String(100), nullable=False)
    emergency_contact_phone = Column(String(20), nullable=False)


class AnalysisHistoryRecord(Base):
    """
    One saved symptom analysis. Only created when the caller was
    logged in at the time of the /analyze request (see
    app.auth.dependencies.get_optional_user_id and app/routes/analyze.py) -
    logged-out analyses are never saved anywhere.
    """

    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(24), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # What the user reported
    age = Column(Integer, nullable=False)
    gender = Column(String(30), nullable=False)
    symptoms = Column(String(1000), nullable=False)
    duration = Column(String(100), nullable=False)
    existing_conditions = Column(String(500), nullable=True)

    # What the AI returned
    possible_conditions = Column(JSON, nullable=False)  # list[str]
    severity = Column(String(20), nullable=False)
    recommended_action = Column(String(1000), nullable=False)
    sos_recommended = Column(Boolean, nullable=False)
    disclaimer = Column(String(1000), nullable=False)


class PassportDocumentRecord(Base):
    """
    One uploaded medical document (blood test, MRI, X-ray, sonography,
    prescription, etc.) attached to a user's Health Passport.

    File bytes are stored directly in Postgres (LargeBinary/BYTEA) -
    deliberately, not in a separate object-storage service (S3,
    Cloudinary, etc.). That keeps this feature's ops footprint at zero
    new services/credentials, consistent with how this project has
    avoided new paid infrastructure everywhere else (no Redis, no
    Docker, no cloud storage). The real tradeoff: Postgres free tiers
    (Supabase/Neon/Render) typically cap total database size in the low
    hundreds of MB to ~1GB, so this does NOT scale to large numbers of
    large files. app/storage/document_store.py enforces a per-file size
    cap and a per-user document count cap for exactly this reason. If
    usage ever outgrows that, the fix is swapping this column for a
    reference to a real object-storage bucket - a storage-layer change,
    not a schema change visible to the API.

    Brand-new table, so - same as `analysis_feedback` and
    `passport_audit_log` before it - no manual migration needed.
    """

    __tablename__ = "passport_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(24), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    category = Column(String(30), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class StagedGuidanceDocument(Base):
    """
    One chunk of externally-ingested guidance content, waiting for (or
    already through) human review before it can be added to the live
    RAG corpus (app/rag/corpus.py).

    This is the gate described in PROJECT_STATE.md's hybrid-retrieval
    requirements: ingestion (app/rag/ingest.py) only ever writes rows
    here with status="pending_review" - it never touches the live
    corpus directly. A human reviewer (app/routes/rag_review.py) is the
    only thing that can move a row to "approved", and even then, the
    live corpus is a separate, explicit step (see rag_review.py) rather
    than something that happens automatically on approval - so a bad
    approval can still be caught before it's actually serving answers.

    `source_id` matches an entry in app/rag/sources.py's allowlist -
    every row here should be traceable back to exactly which source and
    license it came from, since that's what a reviewer is being asked
    to sign off on.
    """

    __tablename__ = "staged_guidance_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(100), nullable=False, index=True)
    source_url = Column(String(500), nullable=False)
    license = Column(String(100), nullable=False)
    attribution = Column(String(1000), nullable=False)

    # The actual candidate guidance text, chunked by the ingestion job.
    # A short topic/keyword hint the ingestion job derived, mirroring
    # the shape of app/rag/corpus.py's GuidanceEntry so an approved row
    # can be turned into one with minimal translation.
    topic_hint = Column(String(200), nullable=True)
    content = Column(String(4000), nullable=False)

    status = Column(String(20), nullable=False, default="pending_review", index=True)
    # Free-text note from whoever reviewed it - why approved/rejected.
    review_note = Column(String(1000), nullable=True)
    reviewed_by = Column(String(24), nullable=True)  # user_id of the reviewer
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PassportAuditLogRecord(Base):
    """
    One audit entry for a Health Passport create/update/delete.

    Brand-new table, same as `analysis_feedback` above - no manual
    migration needed, `create_all()` creates it automatically.

    `snapshot` holds the full passport field values at the time of the
    change (the state AFTER a create/update, or the state right BEFORE
    a delete) - a dict, stored as JSON. `changed_fields` is only
    meaningful for "updated" entries: the list of field names whose
    value actually differed from what was there before. Kept as a
    separate column rather than making the caller diff two snapshots
    themselves.
    """

    __tablename__ = "passport_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(24), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # "created" | "updated" | "deleted"
    changed_fields = Column(JSON, nullable=True)  # list[str], only for "updated"
    snapshot = Column(JSON, nullable=True)  # dict of passport fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AnalysisFeedbackRecord(Base):
    """
    Thumbs-up/down feedback on one saved analysis (see
    AnalysisHistoryRecord above). One feedback row per history entry -
    `history_id` is unique, so submitting feedback again on the same
    analysis updates the existing row rather than creating a second one.

    This is a brand-new table, not a column added to an existing one -
    unlike the `gender` column added to `passports` earlier, this needs
    NO manual `ALTER TABLE` against production. Base.metadata.create_all()
    creates any table that doesn't exist yet, and this one never existed
    before, so it's created automatically on the next deploy.
    """

    __tablename__ = "analysis_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    history_id = Column(Integer, nullable=False, unique=True, index=True)
    user_id = Column(String(24), nullable=False, index=True)
    is_helpful = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ReminderRecord(Base):
    """
    A medication/follow-up reminder (see app/models/reminder.py for the
    scope note on what "reminder" actually means here - in-app only, no
    push/email/SMS).

    `remind_at` is always the NEXT time this reminder is due. For a
    repeating reminder (repeat_every_days is 1 or 7), completing it
    (see app/storage/reminder_store.py's complete_reminder) advances
    `remind_at` forward by that many days rather than deactivating the
    row - so the same row represents "the next occurrence," not a fixed
    one-time event, once it's a repeating reminder.

    Brand-new table - no manual migration needed, same as
    AnalysisFeedbackRecord above.
    """

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(24), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    notes = Column(String(1000), nullable=True)
    category = Column(String(20), nullable=False, default="other")
    remind_at = Column(DateTime(timezone=True), nullable=False, index=True)
    repeat_every_days = Column(Integer, nullable=True)  # None = one-time
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
