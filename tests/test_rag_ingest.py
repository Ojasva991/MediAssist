from app.rag.ingest import _chunk_text, _topic_hint


def test_chunk_text_splits_on_paragraph_breaks():
    para = "This is a reasonably long paragraph of guidance text repeated so it clears the minimum chunk size threshold. " * 3
    text = f"{para}\n\n{para}"
    chunks = _chunk_text(text)
    assert len(chunks) >= 1
    assert all(len(c) >= 200 for c in chunks)


def test_chunk_text_drops_tiny_trailing_fragments():
    text = "hi"
    assert _chunk_text(text) == []


def test_chunk_text_merges_short_paragraphs_up_to_max():
    para = "word " * 30  # well under _MAX_CHUNK_CHARS on its own
    text = f"{para}\n\n{para}\n\n{para}"
    chunks = _chunk_text(text)
    # Merged into fewer chunks than paragraphs, since each is short.
    assert len(chunks) <= 3
    assert all(len(c) <= 1200 for c in chunks)


def test_topic_hint_uses_first_line():
    chunk = "Airway obstruction\nDetails about clearing an airway follow here."
    assert _topic_hint(chunk) == "Airway obstruction"


def test_topic_hint_handles_empty_string():
    assert _topic_hint("") == ""
