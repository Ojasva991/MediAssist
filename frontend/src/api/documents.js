import { apiClient } from "./client";

/**
 * Confirmed against the live backend (app/routes/documents.py,
 * app/models/document.py). Categories: BLOOD_TEST, MRI, XRAY,
 * SONOGRAPHY, PRESCRIPTION, OTHER.
 *
 * Limits enforced server-side (app/storage/document_store.py): 5 MB
 * max per file, PDF/JPEG/PNG/WEBP only, 20 documents max per user.
 * The backend returns a plain-text 400 message for any of these -
 * safe to show directly to the user (see api/client.js's error
 * normalization).
 */

/** POST /passport/{user_id}/documents (multipart/form-data) */
export async function uploadDocument(userId, file, category) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", category);
  const { data } = await apiClient.post(`/passport/${userId}/documents`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/** GET /passport/{user_id}/documents */
export async function listDocuments(userId) {
  const { data } = await apiClient.get(`/passport/${userId}/documents`);
  return data;
}

/** GET /passport/{user_id}/documents/{document_id} - returns a Blob */
export async function downloadDocument(userId, documentId) {
  const { data } = await apiClient.get(`/passport/${userId}/documents/${documentId}`, {
    responseType: "blob",
  });
  return data;
}

/** DELETE /passport/{user_id}/documents/{document_id} */
export async function deleteDocument(userId, documentId) {
  const { data } = await apiClient.delete(`/passport/${userId}/documents/${documentId}`);
  return data;
}
