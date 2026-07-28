import base64
import json

from app.ai.gemini_client import GeminiClientError

# A minimal valid 1x1 transparent PNG, hand-crafted rather than pulling in
# an image library as a new test-only dependency.
_TINY_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _mock_image_success(monkeypatch, response_dict):
    monkeypatch.setattr(
        "app.ai.triage_service.gemini_client.generate_with_image",
        lambda system_prompt, user_prompt, image_bytes, mime_type: json.dumps(response_dict),
    )


def _mock_image_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise GeminiClientError("simulated Gemini outage")

    monkeypatch.setattr(
        "app.ai.triage_service.gemini_client.generate_with_image", _raise
    )


def _upload(client, **form_fields):
    files = {"image": ("photo.png", _TINY_PNG_BYTES, "image/png")}
    return client.post("/analyze/image", files=files, data=form_fields)


def test_rejects_unsupported_content_type(client):
    files = {"image": ("notes.txt", b"just some text", "text/plain")}
    resp = client.post("/analyze/image", files=files, data={})
    assert resp.status_code == 400


def test_rejects_oversized_image(client, monkeypatch):
    # Avoid actually allocating 8MB+ in the test - patch the cap down
    # instead of the payload up.
    monkeypatch.setattr("app.routes.analyze.MAX_IMAGE_SIZE_BYTES", 10)
    resp = _upload(client)
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"].lower()


def test_rejects_empty_image(client):
    files = {"image": ("empty.png", b"", "image/png")}
    resp = client.post("/analyze/image", files=files, data={})
    assert resp.status_code == 400


def test_works_without_any_text_context(client, monkeypatch):
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "A small red patch on the forearm.",
            "possible_conditions": ["Mild skin irritation"],
            "severity": "LOW",
            "recommended_action": "Monitor for changes.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
            "image_rejected": False,
        },
    )
    resp = _upload(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["visual_observation"] == "A small red patch on the forearm."
    assert body["image_rejected"] is False


def test_disclaimer_always_includes_photo_reliability_caveat(client, monkeypatch):
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "A mole on the shoulder.",
            "possible_conditions": ["Common mole"],
            "severity": "LOW",
            "recommended_action": "Monitor for changes.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
            "image_rejected": False,
        },
    )
    resp = _upload(client)
    assert resp.status_code == 200
    assert "significantly less reliable" in resp.json()["disclaimer"].lower()


def test_disclaimer_not_duplicated_if_model_already_included_it(client, monkeypatch):
    already_thorough = (
        "This is not a medical diagnosis. Photo-based assessment is "
        "significantly less reliable than an in-person examination and "
        "cannot rule out serious conditions, including skin cancer. If "
        "you have a new, changing, or unusual-looking growth or wound, "
        "see a healthcare professional promptly regardless of this "
        "assessment."
    )
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "A mole.",
            "possible_conditions": ["Common mole"],
            "severity": "LOW",
            "recommended_action": "Monitor.",
            "sos_recommended": False,
            "disclaimer": already_thorough,
            "image_rejected": False,
        },
    )
    resp = _upload(client)
    body = resp.json()
    # Should appear exactly once, not appended a second time.
    assert body["disclaimer"].count("significantly less reliable") == 1


def test_rejected_scan_image_does_not_get_a_forced_severity(client, monkeypatch):
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "This appears to be an X-ray image, not a photo of skin.",
            "possible_conditions": [],
            "severity": "LOW",
            "recommended_action": "Please have this X-ray reviewed by the ordering doctor or a radiologist.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
            "image_rejected": True,
        },
    )
    resp = _upload(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["image_rejected"] is True
    assert body["possible_conditions"] == []
    assert body["rule_engine"] is None


def test_falls_back_when_gemini_fails(client, monkeypatch):
    _mock_image_failure(monkeypatch)
    resp = _upload(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["possible_conditions"] == []  # fallback never lists conditions


def test_rule_engine_floor_applies_when_text_context_has_red_flags(client, monkeypatch):
    # Even though the LLM says LOW, a red-flag phrase in the accompanying
    # text should raise the floor via the rule engine, same as the
    # text-only /analyze path.
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "Swelling visible.",
            "possible_conditions": ["Localized swelling"],
            "severity": "LOW",
            "recommended_action": "Monitor.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
            "image_rejected": False,
        },
    )
    resp = _upload(client, symptoms="severe difficulty breathing and swelling")
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"] == "EMERGENCY"
    assert body["llm_severity"] == "LOW"  # shows the original LLM read, pre-reconciliation


def test_works_without_authentication(client, monkeypatch):
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "A rash.",
            "possible_conditions": ["Contact dermatitis"],
            "severity": "LOW",
            "recommended_action": "Monitor.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
            "image_rejected": False,
        },
    )
    resp = _upload(client)
    assert resp.status_code == 200
    assert resp.json()["history_id"] is None  # not logged in, nothing saved


def test_saves_to_history_when_age_and_gender_are_available(client, make_user, monkeypatch):
    headers, _, _ = make_user()
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "A rash.",
            "possible_conditions": ["Contact dermatitis"],
            "severity": "LOW",
            "recommended_action": "Monitor.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
            "image_rejected": False,
        },
    )
    files = {"image": ("photo.png", _TINY_PNG_BYTES, "image/png")}
    resp = client.post(
        "/analyze/image",
        files=files,
        data={"age": "30", "gender": "Female"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["history_id"] is not None


def test_skips_history_gracefully_when_no_age_or_gender_available(client, make_user, monkeypatch):
    # No saved passport, no age/gender in the form - the analysis should
    # still succeed (200, real result), just without a history_id, rather
    # than crashing on the NOT NULL age/gender columns shared with the
    # text-only /analyze history table.
    headers, _, _ = make_user()
    _mock_image_success(
        monkeypatch,
        {
            "visual_observation": "A rash.",
            "possible_conditions": ["Contact dermatitis"],
            "severity": "LOW",
            "recommended_action": "Monitor.",
            "sos_recommended": False,
            "disclaimer": "This is not a medical diagnosis.",
            "image_rejected": False,
        },
    )
    files = {"image": ("photo.png", _TINY_PNG_BYTES, "image/png")}
    resp = client.post("/analyze/image", files=files, data={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["history_id"] is None
