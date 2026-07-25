from app.rag.retriever import retrieve


def test_chest_pain_retrieves_chest_pain_guidance():
    results = retrieve("Sudden chest pain and sweating")
    assert results
    assert any(r.id == "chest_pain" for r in results)


def test_choking_retrieves_choking_guidance():
    results = retrieve("My child is choking and can't breathe")
    assert results
    assert results[0].id == "choking"


def test_nonsense_query_returns_nothing():
    results = retrieve("asdkjfh qwerty zzxxcc")
    assert results == []


def test_empty_query_returns_nothing():
    assert retrieve("") == []
    assert retrieve(None) == []


def test_top_k_is_respected():
    results = retrieve("pain fever swelling bleeding breathing", top_k=2)
    assert len(results) <= 2


def test_results_are_ordered_most_relevant_first():
    results = retrieve("severe uncontrolled bleeding from a deep wound", top_k=5)
    assert results
    assert results[0].id == "severe_bleeding"


def test_mental_health_crisis_is_retrievable():
    # Worth its own test given how sensitive this category is - it must
    # actually surface so the model gets pointed toward "seek help
    # immediately" framing rather than nothing at all.
    results = retrieve("I've been having thoughts of suicide")
    assert any(r.id == "mental_health_crisis" for r in results)
