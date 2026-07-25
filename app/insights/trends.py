"""
Symptom trend detection - flags symptom keywords mentioned repeatedly
across a user's saved analysis history within a recent time window
(e.g. "you've mentioned 'headache' in 4 analyses over the last 14 days").

Deliberately simple (word-frequency over recent history), same spirit
as the RAG retriever (app/rag/retriever.py): no ML model, no new
dependency, fast enough to run on every history/dashboard load without
worrying about cost or cold-start time on Render's free tier.
"""

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.models.history import AnalysisHistoryItem, TrendFinding

_TOKEN_PATTERN = re.compile(r"[a-z]+")

# Common words that show up in almost every symptom description and
# would otherwise dominate the count without representing a meaningful
# trend on their own.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "with", "without", "of", "in",
    "on", "at", "for", "to", "is", "are", "was", "were", "since", "this",
    "that", "it", "my", "me", "i", "have", "has", "had", "feeling", "feel",
    "bit", "little", "very", "mild", "slight", "some", "been", "am",
    "morning", "today", "yesterday", "night", "day", "days", "hours",
    "hour", "week", "weeks", "after", "before", "during", "also", "just",
}

# A finding needs to show up in at least this many SEPARATE analyses
# (not just repeated within one description) to count as a trend -
# two mentions of "tired" shouldn't be treated as a pattern.
_MIN_OCCURRENCES = 3
_LOOKBACK_DAYS = 14
_MIN_TOKEN_LENGTH = 4


def _tokenize(text: str) -> list[str]:
    tokens = _TOKEN_PATTERN.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) >= _MIN_TOKEN_LENGTH]


def _as_aware_utc(dt: datetime) -> datetime:
    # Normalizes away timezone-awareness differences between Postgres
    # (tz-aware) and SQLite in tests (often naive) so comparisons never
    # raise - assumes a naive datetime is already UTC (true for both
    # backends here), only used for the cutoff comparison, never displayed.
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def detect_trends(entries: list[AnalysisHistoryItem]) -> list[TrendFinding]:
    """
    Given a user's history entries (as returned by get_history), flag
    any symptom keyword mentioned in at least _MIN_OCCURRENCES separate
    analyses within the last _LOOKBACK_DAYS days. Returns [] if nothing
    recurs - this is meant to surface a real pattern, not force a
    finding out of two loosely-related mentions.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)
    recent = [e for e in entries if _as_aware_utc(e.created_at) >= cutoff]
    if len(recent) < _MIN_OCCURRENCES:
        return []

    # Count each token once per ENTRY, not per raw occurrence in the
    # text, so a description that repeats a word twice doesn't inflate
    # its own count.
    token_entry_counts: Counter = Counter()
    for entry in recent:
        token_entry_counts.update(set(_tokenize(entry.symptoms)))

    findings = [
        TrendFinding(keyword=token, occurrences=count, window_days=_LOOKBACK_DAYS)
        for token, count in token_entry_counts.items()
        if count >= _MIN_OCCURRENCES
    ]
    findings.sort(key=lambda f: f.occurrences, reverse=True)
    return findings
