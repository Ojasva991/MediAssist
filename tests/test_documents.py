import io

from app.storage.document_store import MAX_DOCUMENTS_PER_USER, MAX_FILE_SIZE_BYTES

_TINY_PDF = b"%PDF-1.4\n%tiny test file\n"


def _upload(client, user_id, headers, filename="report.pdf", category="BLOOD_TEST", content=_TINY_PDF, content_type="application/pdf"):
    return client.post(
        f"/passport/{user_id}/documents",
        headers=headers,
        data={"category": category},
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


def test_upload_requires_authentication(client):
    resp = client.post(
        "/passport/some-user-id/documents",
        data={"category": "BLOOD_TEST"},
        files={"file": ("x.pdf", io.BytesIO(_TINY_PDF), "application/pdf")},
    )
    assert resp.status_code == 401


def test_upload_and_list_roundtrip(client, make_user):
    headers, user_id, _ = make_user()
    resp = _upload(client, user_id, headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "report.pdf"
    assert body["category"] == "BLOOD_TEST"
    assert body["content_type"] == "application/pdf"
    assert body["file_size"] == len(_TINY_PDF)

    list_resp = client.get(f"/passport/{user_id}/documents", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_upload_rejects_disallowed_file_type(client, make_user):
    headers, user_id, _ = make_user()
    resp = _upload(client, user_id, headers, filename="script.exe", content_type="application/x-msdownload")
    assert resp.status_code == 400


def test_upload_rejects_oversized_file(client, make_user):
    headers, user_id, _ = make_user()
    oversized = b"0" * (MAX_FILE_SIZE_BYTES + 1)
    resp = _upload(client, user_id, headers, content=oversized)
    assert resp.status_code == 400


def test_upload_rejects_empty_file(client, make_user):
    headers, user_id, _ = make_user()
    resp = _upload(client, user_id, headers, content=b"")
    assert resp.status_code == 400


def test_upload_enforces_per_user_document_cap(client, make_user):
    headers, user_id, _ = make_user()
    for _ in range(MAX_DOCUMENTS_PER_USER):
        resp = _upload(client, user_id, headers)
        assert resp.status_code == 201

    over_cap = _upload(client, user_id, headers)
    assert over_cap.status_code == 400


def test_download_returns_the_uploaded_bytes(client, make_user):
    headers, user_id, _ = make_user()
    upload_resp = _upload(client, user_id, headers)
    doc_id = upload_resp.json()["id"]

    resp = client.get(f"/passport/{user_id}/documents/{doc_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.content == _TINY_PDF
    assert resp.headers["content-type"] == "application/pdf"


def test_download_nonexistent_document_returns_404(client, make_user):
    headers, user_id, _ = make_user()
    resp = client.get(f"/passport/{user_id}/documents/999999", headers=headers)
    assert resp.status_code == 404


def test_cannot_download_another_users_document(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()
    upload_resp = _upload(client, user_id_a, headers_a)
    doc_id = upload_resp.json()["id"]

    resp = client.get(f"/passport/{user_id_a}/documents/{doc_id}", headers=headers_b)
    assert resp.status_code == 403


def test_delete_document(client, make_user):
    headers, user_id, _ = make_user()
    upload_resp = _upload(client, user_id, headers)
    doc_id = upload_resp.json()["id"]

    del_resp = client.delete(f"/passport/{user_id}/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 200

    list_resp = client.get(f"/passport/{user_id}/documents", headers=headers)
    assert list_resp.json() == []


def test_cannot_delete_another_users_document(client, make_user):
    headers_a, user_id_a, _ = make_user()
    headers_b, _user_id_b, _ = make_user()
    upload_resp = _upload(client, user_id_a, headers_a)
    doc_id = upload_resp.json()["id"]

    resp = client.delete(f"/passport/{user_id_a}/documents/{doc_id}", headers=headers_b)
    assert resp.status_code == 403


def test_list_documents_most_recent_first(client, make_user):
    headers, user_id, _ = make_user()
    _upload(client, user_id, headers, filename="first.pdf")
    _upload(client, user_id, headers, filename="second.pdf")

    resp = client.get(f"/passport/{user_id}/documents", headers=headers)
    entries = resp.json()
    assert entries[0]["filename"] == "second.pdf"
    assert entries[1]["filename"] == "first.pdf"
