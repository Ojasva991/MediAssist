"""
A tiny, dependency-free TF-IDF retriever over the curated first-aid/
triage guidance corpus (app/rag/corpus.py).

This is intentionally NOT a full vector-embedding RAG pipeline with a
vector database - the corpus is a few dozen short entries, and Render's
free tier has limited memory/CPU and cold-starts on inactivity, so
pulling in an embeddings model or a vector DB would add real deployment
risk and startup time for very little benefit at this scale. Plain
term-frequency / inverse-document-frequency matching (the classic
pre-neural search technique) is fast, adds zero new dependencies to
requirements.txt, and is good enough to surface the 1-3 most relevant
guidance entries for a symptom description.

Flow: symptoms text -> retrieve top-k guidance entries -> included as
grounding context in the Gemini prompt (see app/ai/prompts.py). The
sources actually used are also returned to the caller for transparency
(see SymptomAnalysisResponse.retrieved_guidance).
"""

import math
import re
from collections import Counter

from app.rag.corpus import CORPUS, GuidanceEntry

_TOKEN_PATTERN = re.compile(r"[a-z]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def _document_text(entry: GuidanceEntry) -> str:
    # Keywords are given extra weight by simple repetition (this is
    # bag-of-words matching, not a separate structured field search),
    # so a symptom description matching the keyword list scores higher
    # than one that only loosely overlaps the prose content.
    return f"{entry.topic} {entry.keywords} {entry.keywords} {entry.content}"


_DOCS: list[list[str]] = [_tokenize(_document_text(e)) for e in CORPUS]
_DOC_FREQ: Counter = Counter()
for _doc in _DOCS:
    _DOC_FREQ.update(set(_doc))
_NUM_DOCS = len(_DOCS)


def _idf(term: str) -> float:
    # +1 smoothing (both in the numerator and denominator) so a term
    # that appears in every document, or in none, never divides by
    # zero or produces a negative weight.
    df = _DOC_FREQ.get(term, 0)
    return math.log((_NUM_DOCS + 1) / (df + 1)) + 1


def _tfidf_vector(tokens: list[str]) -> Counter:
    tf = Counter(tokens)
    return Counter({term: count * _idf(term) for term, count in tf.items()})


def _cosine_similarity(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


_DOC_VECTORS = [_tfidf_vector(doc) for doc in _DOCS]

# Below this similarity, a match is considered too weak to be useful
# grounding - it's better to send Gemini nothing than a barely-related
# entry that could distract it from the actual symptoms described.
_MIN_SIMILARITY = 0.05


def retrieve(query: str, top_k: int = 3) -> list[GuidanceEntry]:
    """
    Return up to `top_k` corpus entries most relevant to `query`,
    ordered by relevance, dropping anything below a minimum similarity
    threshold. Never raises - an empty/unmatched query just returns [].
    """
    query_tokens = _tokenize(query or "")
    if not query_tokens:
        return []

    query_vector = _tfidf_vector(query_tokens)
    scored = [
        (_cosine_similarity(query_vector, doc_vector), entry)
        for doc_vector, entry in zip(_DOC_VECTORS, CORPUS)
    ]
    scored = [(score, entry) for score, entry in scored if score >= _MIN_SIMILARITY]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[:top_k]]
