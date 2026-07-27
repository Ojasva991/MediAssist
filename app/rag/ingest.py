"""
Scheduled ingestion job for the hybrid-retrieval RAG staging pipeline.

Run this manually or via an external scheduler (a cron job, a Render
Cron Job, GitHub Actions on a schedule, etc.) - deliberately NOT
triggered by any user-facing request. /analyze must keep answering
purely from the already-approved corpus (app/rag/corpus.py) and the
staging table (app/storage/models.StagedGuidanceDocument), with zero
live network calls in the request path.

Usage:
    python -m app.rag.ingest                 # ingest every allowlisted source
    python -m app.rag.ingest --source-id who_icrc_basic_emergency_care_2018

What this does NOT do:
- It never writes to the live corpus. Every row lands as
  status="pending_review" - see app/routes/rag_review.py for the human
  approval step, and app/rag/promote.py for the separate, explicit step
  that actually adds an approved row to the corpus.
- It never fetches a URL that isn't in app/rag/sources.py's allowlist.
- It does not re-ingest a source that already has ANY staged rows
  (pending, approved, or rejected) unless --force is passed, so
  re-running this job by accident doesn't flood the review queue with
  duplicates of something already decided on.
"""

import argparse
import logging
import re
from io import BytesIO
from urllib.request import Request, urlopen

from pypdf import PdfReader

from app.rag.sources import SOURCE_ALLOWLIST, AllowlistedSource
from app.storage.staged_guidance_store import create_staged_documents, list_staged_documents

logger = logging.getLogger(__name__)

# Keep chunks short enough to be a single reviewable/citable "entry",
# matching the scale of app/rag/corpus.py's existing hand-written
# entries (a paragraph or two), not whole-page dumps.
_MAX_CHUNK_CHARS = 1200
_MIN_CHUNK_CHARS = 200


def _fetch_pdf_bytes(url: str) -> bytes:
    # Plain stdlib urllib - deliberately not adding `requests`/`httpx` as
    # a new dependency for a single GET request, same "no new dependency
    # unless it earns its place" spirit as the rest of this project.
    request = Request(url, headers={"User-Agent": "Vaeda-ingestion/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _chunk_text(text: str) -> list[str]:
    # Paragraph-based chunking (split on blank lines), then merge/split
    # so each chunk lands roughly within the size bounds above. Simple
    # on purpose - same "no ML model needed for this" reasoning as
    # app/insights/trends.py and app/rag/retriever.py elsewhere in this
    # project.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= _MAX_CHUNK_CHARS:
            buffer = candidate
        else:
            if len(buffer) >= _MIN_CHUNK_CHARS:
                chunks.append(buffer)
            buffer = paragraph[:_MAX_CHUNK_CHARS]
    if len(buffer) >= _MIN_CHUNK_CHARS:
        chunks.append(buffer)
    return chunks


def _topic_hint(chunk: str) -> str:
    first_line = chunk.strip().splitlines()[0] if chunk.strip() else ""
    return first_line[:100]


def ingest_source(source: AllowlistedSource, *, force: bool = False) -> int:
    """Ingests one allowlisted source. Returns the number of chunks staged."""
    if not force:
        existing = [
            row
            for row in list_staged_documents(status=None)
            if row.source_id == source.id
        ]
        if existing:
            logger.info(
                "Skipping %s - already has %d staged row(s). Pass --force to re-ingest.",
                source.id,
                len(existing),
            )
            return 0

    if source.content_type != "pdf":
        raise ValueError(f"Unsupported content_type for {source.id}: {source.content_type}")

    logger.info("Fetching %s", source.url)
    pdf_bytes = _fetch_pdf_bytes(source.url)
    text = _extract_text(pdf_bytes)
    chunks = _chunk_text(text)

    rows = [
        {
            "source_id": source.id,
            "source_url": source.url,
            "license": source.license,
            "attribution": source.attribution,
            "topic_hint": _topic_hint(chunk),
            "content": chunk[:4000],
        }
        for chunk in chunks
    ]
    ids = create_staged_documents(rows)
    logger.info("Staged %d chunk(s) from %s for review", len(ids), source.id)
    return len(ids)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", help="Ingest only this source (default: all)")
    parser.add_argument(
        "--force", action="store_true", help="Re-ingest even if staged rows already exist"
    )
    args = parser.parse_args()

    sources = SOURCE_ALLOWLIST
    if args.source_id:
        sources = [s for s in sources if s.id == args.source_id]
        if not sources:
            raise SystemExit(f"No allowlisted source with id={args.source_id!r}")

    total = 0
    for source in sources:
        total += ingest_source(source, force=args.force)
    logger.info("Done. %d chunk(s) newly staged across %d source(s).", total, len(sources))


if __name__ == "__main__":
    main()
