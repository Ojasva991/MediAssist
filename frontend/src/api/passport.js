import { apiClient } from "./client";

/**
 * Confirmed against the live backend's HealthPassport model
 * (app/models/passport.py). Notably: no `gender` field, and
 * allergies/medications/chronic_diseases are free-text strings,
 * not arrays.
 *
 * {
 *   name: string,                    // required
 *   age: number,                     // required, 0-120
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
