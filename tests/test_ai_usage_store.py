from datetime import datetime, timedelta, timezone

from app.storage.ai_usage_store import get_average_latency_ms, get_provider_stats, log_attempt


def test_log_attempt_and_get_provider_stats():
    since = datetime.now(timezone.utc) - timedelta(minutes=1)
    log_attempt("gemini", True, 250)
    log_attempt("gemini", False, 100)
    log_attempt("groq", True, 400)
    log_attempt("all_failed", False, None)

    stats = get_provider_stats(since)
    assert stats["gemini"]["success"] >= 1
    assert stats["gemini"]["failure"] >= 1
    assert stats["groq"]["success"] >= 1
    assert stats["all_failed"] >= 1


def test_get_provider_stats_excludes_attempts_before_the_since_cutoff():
    future_cutoff = datetime.now(timezone.utc) + timedelta(hours=1)
    log_attempt("gemini", True, 200)
    stats = get_provider_stats(future_cutoff)
    assert stats["gemini"]["success"] == 0
    assert stats["gemini"]["failure"] == 0


def test_get_average_latency_only_counts_successful_attempts():
    since = datetime.now(timezone.utc) - timedelta(minutes=1)
    log_attempt("groq", True, 100)
    log_attempt("groq", True, 300)
    log_attempt("groq", False, 9999)  # failure - must not skew the average

    avg = get_average_latency_ms("groq", since)
    assert avg is not None
    assert avg < 9999


def test_get_average_latency_returns_none_when_no_data():
    future_cutoff = datetime.now(timezone.utc) + timedelta(hours=1)
    assert get_average_latency_ms("gemini", future_cutoff) is None


def test_log_attempt_never_raises_even_on_bad_input():
    # provider isn't restricted to a fixed set at the storage layer -
    # logging must be resilient, not validate-and-crash.
    log_attempt("some_future_provider", True, 50)
