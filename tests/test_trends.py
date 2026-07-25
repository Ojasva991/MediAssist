from datetime import datetime, timedelta, timezone

from app.insights.trends import detect_trends
from app.models.history import AnalysisHistoryItem

_BASE_ITEM = {
    "duration": "3 hours",
    "existing_conditions": None,
    "possible_conditions": [],
    "severity": "LOW",
    "recommended_action": "n/a",
    "sos_recommended": False,
    "disclaimer": "n/a",
    "feedback": None,
}


def _item(id_, symptoms, days_ago=0, age=30, gender="Female"):
    return AnalysisHistoryItem(
        id=id_,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        age=age,
        gender=gender,
        symptoms=symptoms,
        **_BASE_ITEM,
    )


def test_no_trend_with_too_few_entries():
    entries = [_item(1, "Headache"), _item(2, "Headache")]
    assert detect_trends(entries) == []


def test_recurring_keyword_is_detected():
    entries = [
        _item(1, "Bad headache today"),
        _item(2, "Headache again this afternoon"),
        _item(3, "Another headache after lunch"),
    ]
    findings = detect_trends(entries)
    assert any(f.keyword == "headache" for f in findings)
    headache_finding = next(f for f in findings if f.keyword == "headache")
    assert headache_finding.occurrences == 3


def test_repeating_word_within_one_entry_only_counts_once():
    # "headache headache headache" in a single description should count
    # as ONE entry mentioning it, not three.
    entries = [
        _item(1, "headache headache headache"),
        _item(2, "Feeling tired"),
        _item(3, "Feeling tired"),
    ]
    findings = detect_trends(entries)
    assert not any(f.keyword == "headache" for f in findings)


def test_stopwords_never_appear_as_findings():
    entries = [_item(i, "I have a mild fever today") for i in range(3)]
    findings = detect_trends(entries)
    keywords = {f.keyword for f in findings}
    assert "today" not in keywords
    assert "mild" not in keywords
    assert "fever" in keywords


def test_entries_outside_the_lookback_window_are_ignored():
    entries = [
        _item(1, "Persistent headache", days_ago=1),
        _item(2, "Persistent headache", days_ago=2),
        _item(3, "Persistent headache", days_ago=40),  # too old
    ]
    findings = detect_trends(entries)
    assert findings == []


def test_no_findings_when_nothing_recurs():
    entries = [
        _item(1, "Sore throat"),
        _item(2, "Twisted ankle"),
        _item(3, "Upset stomach"),
    ]
    assert detect_trends(entries) == []


def test_findings_sorted_most_frequent_first():
    entries = [
        _item(1, "Headache and nausea"),
        _item(2, "Headache again"),
        _item(3, "Headache and dizziness"),
        _item(4, "Nausea returned"),
    ]
    findings = detect_trends(entries)
    assert findings[0].keyword == "headache"
    assert findings[0].occurrences == 3
