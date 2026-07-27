"""
Promotes APPROVED staged guidance documents into a form ready to be
hand-added to the live corpus (app/rag/corpus.py).

Deliberately manual and deliberately generates code for a HUMAN to
review and paste in, rather than writing to corpus.py automatically or
having the retriever pull live from the database. Reasons:

1. The live corpus is the exact thing /analyze's grounding depends on
   (see app/rag/retriever.py, app/ai/triage_service.py) - it should
   stay something a person can read in a diff/PR before it ships, the
   same way this project already treats "new columns need a manual
   ALTER TABLE" as a deliberate non-automatic step.
2. It keeps a single approval action (app/routes/rag_review.py) from
   being the ONLY thing standing between "ingested from the internet"
   and "the AI is now citing this in a live medical-adjacent
   response" - promotion is a second, separate, deliberate action.

Usage:
    python -m app.rag.promote
    # prints ready-to-paste GuidanceEntry(...) blocks for every
    # approved-but-not-yet-promoted staged document, then marks them
    # "promoted" so this script doesn't print them again next time.
"""

import logging
import re

from app.storage.db import get_session
from app.storage.models import StagedGuidanceDocument

logger = logging.getLogger(__name__)

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    slug = _SLUG_PATTERN.sub("_", text.lower()).strip("_")
    return slug[:40] or "entry"


def _format_entry(row: StagedGuidanceDocument) -> str:
    entry_id = f"{_slugify(row.source_id)}_{row.id}"
    topic = (row.topic_hint or "Untitled").replace('"', "'")
    content = row.content.replace('"""', "'''")
    return (
        f'    GuidanceEntry(\n'
        f'        id="{entry_id}",\n'
        f'        source="{row.attribution}",\n'
        f'        topic="{topic}",\n'
        f'        keywords="",  # TODO: fill in search keywords before merging\n'
        f'        content="""{content}""",\n'
        f'    ),'
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    session = get_session()
    try:
        approved = (
            session.query(StagedGuidanceDocument)
            .filter(StagedGuidanceDocument.status == "approved")
            .all()
        )
        if not approved:
            print("No approved-and-not-yet-promoted staged documents found.")
            return

        print(f"# {len(approved)} entries ready to review and paste into app/rag/corpus.py")
        print("# Fill in `keywords` for each before merging - see existing CORPUS entries")
        print("# for the style (topic-relevant terms a symptom description might use).\n")
        for row in approved:
            print(_format_entry(row))
            print()
            row.status = "promoted"
        session.commit()
        print(f"# Marked {len(approved)} row(s) as status=promoted (won't be printed again).")
    finally:
        session.close()


if __name__ == "__main__":
    main()
