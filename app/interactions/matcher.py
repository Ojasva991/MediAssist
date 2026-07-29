"""
Deterministic drug-name resolution and pairwise interaction lookup
against app/interactions/corpus.py's curated list.

No fuzzy matching, no AI-assisted name resolution - a name either
matches a known alias (case-insensitively, trimmed) or it doesn't.
This is a deliberate choice: fuzzy-matching "warfarin" against a typo
like "wafarin" might feel more helpful, but silently guessing at drug
identity in a safety-relevant feature is exactly the kind of "helpful"
that becomes dangerous when it guesses wrong. An unmatched name is
reported back to the caller explicitly instead.
"""

from dataclasses import dataclass

from app.interactions.corpus import INTERACTIONS, DrugEntry, InteractionEntry


@dataclass(frozen=True)
class ResolvedDrug:
    input_name: str
    canonical_name: str


@dataclass(frozen=True)
class InteractionMatch:
    drug_a: str  # canonical names of the two INPUT drugs that matched
    drug_b: str
    severity: str
    description: str


def _build_alias_index() -> dict[str, DrugEntry]:
    """Maps every lowercased alias/canonical name to its DrugEntry."""
    index: dict[str, DrugEntry] = {}
    for entry in INTERACTIONS:
        for drug in (entry.drug_a, entry.drug_b):
            for name in drug.all_names():
                index[name.lower()] = drug
    return index


_ALIAS_INDEX = _build_alias_index()


def _build_pair_index() -> dict[frozenset, InteractionEntry]:
    """Maps a frozenset of the two canonical drug names to their entry."""
    index: dict[frozenset, InteractionEntry] = {}
    for entry in INTERACTIONS:
        key = frozenset({entry.drug_a.canonical_name, entry.drug_b.canonical_name})
        index[key] = entry
    return index


_PAIR_INDEX = _build_pair_index()


def resolve_drug_name(name: str) -> ResolvedDrug | None:
    """Returns the canonical drug this name matches, or None if unrecognized."""
    normalized = name.strip().lower()
    drug = _ALIAS_INDEX.get(normalized)
    if drug is None:
        return None
    return ResolvedDrug(input_name=name, canonical_name=drug.canonical_name)


def check_interactions(drug_names: list[str]) -> tuple[list[InteractionMatch], list[str]]:
    """
    Resolves each name, then checks every pairwise combination among the
    ones that resolved against the curated interaction table.

    Returns (matches, unrecognized_names) - unrecognized_names is never
    silently dropped, since "we didn't check this one" is materially
    different from "we checked it and found nothing," and callers (see
    app/routes/drug_interactions.py) must surface that distinction.
    """
    resolved: list[ResolvedDrug] = []
    unrecognized: list[str] = []

    for name in drug_names:
        result = resolve_drug_name(name)
        if result is None:
            unrecognized.append(name)
        else:
            resolved.append(result)

    matches: list[InteractionMatch] = []
    seen_canonical_pairs: set[frozenset] = set()

    for i in range(len(resolved)):
        for j in range(i + 1, len(resolved)):
            pair_key = frozenset({resolved[i].canonical_name, resolved[j].canonical_name})
            if pair_key in seen_canonical_pairs:
                continue  # e.g. caller listed "advil" and "ibuprofen" separately - same drug
            entry = _PAIR_INDEX.get(pair_key)
            if entry is not None:
                seen_canonical_pairs.add(pair_key)
                matches.append(
                    InteractionMatch(
                        drug_a=resolved[i].input_name,
                        drug_b=resolved[j].input_name,
                        severity=entry.severity.value,
                        description=entry.description,
                    )
                )

    return matches, unrecognized
