import { apiClient } from "./client";

/**
 * Confirmed against the live backend's HealthPassport model
 * (app/models/passport.py). allergies/medications/chronic_diseases are
 * free-text strings, not arrays.
 *
 * {
 *   name: string,                    // required
 *   age: number,                     // required, 0-120
 *   gender: string,                  // required - saved once here, reused
 *                                    // automatically by /analyze instead of
 *                                    // being asked for on every check
 *   blood_group: "A+"|"A-"|"B+"|"B-"|"AB+"|"AB-"|"O+"|"O-"|"UNKNOWN",
 *   allergies?: string,              // free text, e.g. "Penicillin, Peanuts"
 *   medications?: string,
 *   chronic_diseases?: string,
 *   emergency_contact_name: string,  // required
 *   emergency_contact_phone: string  // required, min 7 digits
 * }
 */

/** GET /passport/{user_id} */
export async function getPassport(userId) {
  const { data } = await apiClient.get(`/passport/${userId}`);
  return data;
}

/** PUT /passport/{user_id} — creates or fully replaces the passport */
export async function upsertPassport(userId, payload) {
  const { data } = await apiClient.put(`/passport/${userId}`, payload);
  return data;
}

/** DELETE /passport/{user_id} */
export async function deletePassport(userId) {
  const { data } = await apiClient.delete(`/passport/${userId}`);
  return data;
}

/**
 * GET /passport/{user_id}/report
 *
 * Downloads a one-page, doctor-facing PDF summary of the passport plus
 * the 5 most recent symptom analyses (see app/reports/passport_report.py
 * on the backend). Returns the raw PDF as a Blob - the caller is
 * responsible for turning that into an actual file download (see
 * Passport.jsx for the object-URL-and-click pattern).
 *
 * Requires a saved passport - the backend 404s otherwise.
 */
export async function downloadPassportReport(userId) {
  const { data } = await apiClient.get(`/passport/${userId}/report`, {
    responseType: "blob",
  });
  return data;
}
