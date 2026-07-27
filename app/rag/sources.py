"""
Allowlist of external guidance sources this project is permitted to
ingest into the RAG corpus's staging area.

This is deliberately NOT an open list - the ingestion job
(app/rag/ingest.py) will only ever fetch a URL that appears here. No
request-time fetching of arbitrary URLs happens anywhere in this
project; that's the whole point of keeping this list separate and
explicit rather than letting a symptom-analysis request trigger a live
fetch.

IMPORTANT - licensing was actually checked, not assumed:
WHO publications (like the entry below) are released under
CC BY-NC-SA 3.0 IGO - copying/adapting is permitted for NON-COMMERCIAL
use only, with attribution, share-alike licensing of any adaptation,
and a required disclaimer that WHO did not create the adaptation and
is not responsible for its accuracy. If this project ever becomes
commercial (ads, paid tiers, etc.), this license no longer covers it,
and WHO's own commercial-use permission process would need to be used
instead - that is a business/legal decision, not a code change, which
is exactly why every staged entry from a source below still requires
human review (see app/routes/rag_review.py) before it can reach the
live corpus. The reviewer re-confirms non-commercial status at
approval time; nothing here treats it as settled once and forgotten.

Plain WHO *website* pages (as opposed to the CC-licensed PDF
publications) are under stricter terms - research/private study only,
not commercial use, and reproduction of "substantial portions" needs
prior written authorization - so this allowlist deliberately only
includes the CC-licensed PDF publication, not the general WHO website.

No IFRC/Red Cross entry is included yet: unlike WHO, general IFRC
first-aid guidance content doesn't have the same clear reuse license
- the joint WHO/ICRC "Basic emergency care" guide below is the one
exception where a Red Cross body co-published under WHO's CC license.
Do not add a general IFRC/Red Cross URL here without first finding
(and documenting, the same way as below) an actual license that covers
it - "seems reasonable" is not sufficient.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AllowlistedSource:
    id: str
    url: str
    title: str
    license: str
    # Exact text (or a close paraphrase) required by the license to
    # accompany any use of this source's content.
    attribution: str
    # Human-readable note on WHY this specific source/license combo was
    # judged acceptable to ingest, for the next person who has to trust
    # (or re-check) this list rather than a code comment buried lower down.
    license_note: str
    # Format hint for the ingestion job (app/rag/ingest.py) - which
    # extractor to use.
    content_type: str  # "pdf"


SOURCE_ALLOWLIST: list[AllowlistedSource] = [
    AllowlistedSource(
        id="who_icrc_basic_emergency_care_2018",
        url="https://iris.who.int/server/api/core/bitstreams/63432b9f-8808-44c5-9692-cea717c0cbda/content",
        title="Basic Emergency Care: Approach to the Acutely Ill and Injured",
        license="CC BY-NC-SA 3.0 IGO",
        attribution=(
            "World Health Organization and the International Committee of the "
            "Red Cross, 2018. Basic Emergency Care: Approach to the Acutely Ill "
            "and Injured. Licence: CC BY-NC-SA 3.0 IGO."
        ),
        license_note=(
            "Jointly published by WHO and ICRC under WHO's standard CC "
            "BY-NC-SA 3.0 IGO license - permits non-commercial reuse/adaptation "
            "with attribution and share-alike, verified directly against "
            "WHO's copyright/licensing pages and the publication's own "
            "colophon, not assumed."
        ),
        content_type="pdf",
    ),
]


def get_source(source_id: str) -> AllowlistedSource | None:
    for source in SOURCE_ALLOWLIST:
        if source.id == source_id:
            return source
    return None
