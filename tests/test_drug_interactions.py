from app.interactions.matcher import check_interactions, resolve_drug_name


def test_resolve_drug_name_matches_canonical_name():
    result = resolve_drug_name("warfarin")
    assert result is not None
    assert result.canonical_name == "warfarin"


def test_resolve_drug_name_matches_alias_case_insensitively():
    result = resolve_drug_name("COUMADIN")
    assert result is not None
    assert result.canonical_name == "warfarin"


def test_resolve_drug_name_trims_whitespace():
    result = resolve_drug_name("  ibuprofen  ")
    assert result is not None


def test_resolve_unknown_drug_returns_none():
    assert resolve_drug_name("totally-not-a-real-drug-xyz") is None


def test_check_interactions_finds_known_major_interaction():
    matches, unrecognized = check_interactions(["warfarin", "ibuprofen"])
    assert len(matches) == 1
    assert matches[0].severity == "MAJOR"
    assert unrecognized == []


def test_check_interactions_reports_unrecognized_names_separately():
    matches, unrecognized = check_interactions(["warfarin", "not-a-real-drug"])
    assert matches == []
    assert unrecognized == ["not-a-real-drug"]


def test_check_interactions_returns_empty_for_unrelated_known_drugs():
    # Two real, resolvable drugs with no entry in our curated list -
    # should return no matches (not an error), and NOT be in unrecognized
    # either, since they WERE recognized, just not flagged together.
    matches, unrecognized = check_interactions(["sildenafil", "warfarin"])
    assert matches == []
    assert unrecognized == []


def test_check_interactions_does_not_duplicate_when_aliases_of_same_drug_given():
    # "warfarin" and "coumadin" are the same drug - shouldn't match
    # against each other as if they were two different drugs.
    matches, unrecognized = check_interactions(["warfarin", "coumadin", "ibuprofen"])
    assert len(matches) == 1  # only warfarin-ibuprofen, not counted twice


def test_check_interactions_checks_all_pairs_in_a_larger_list():
    matches, unrecognized = check_interactions(["warfarin", "ibuprofen", "aspirin"])
    # warfarin+ibuprofen AND warfarin+aspirin should both be flagged
    assert len(matches) == 2


def test_endpoint_requires_at_least_two_drugs(client):
    resp = client.post("/drug-interactions/check", json={"drugs": ["warfarin"]})
    assert resp.status_code == 422


def test_endpoint_returns_matches_and_disclaimer(client):
    resp = client.post(
        "/drug-interactions/check", json={"drugs": ["warfarin", "ibuprofen"]}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["matches"]) == 1
    assert body["matches"][0]["severity"] == "MAJOR"
    assert "not a comprehensive" in body["disclaimer"].lower()


def test_endpoint_works_without_authentication(client):
    resp = client.post(
        "/drug-interactions/check", json={"drugs": ["warfarin", "ibuprofen"]}
    )
    assert resp.status_code == 200


def test_endpoint_reports_unrecognized_drugs(client):
    resp = client.post(
        "/drug-interactions/check", json={"drugs": ["warfarin", "not-a-real-drug-xyz"]}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["matches"] == []
    assert "not-a-real-drug-xyz" in body["unrecognized_drugs"]
