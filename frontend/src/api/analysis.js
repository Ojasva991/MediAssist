import { apiClient } from "./client";

/**
 * POST /analyze
 *
 * Confirmed against the live backend's SymptomAnalysisRequest /
 * SymptomAnalysisResponse models (app/models/symptom.py).
 *
 * Request:
 * {
 *   age?: number,              // 0-120. Optional if saved in the caller's
 *                              // Health Passport - the backend fills it in
 *                              // automatically for logged-in callers who
 *                              // omit it. Required otherwise (400 if missing
 *                              // and no passport exists).
 *   gender?: string,           // same rule as age
 *   symptoms: string,          // required, single free-text string (not an array)
 *   duration: string,          // required, e.g. "3 days"
 *   existing_conditions?: string  // also auto-filled from the Health
 *                                 // Passport's chronic_diseases when omitted
 * }
 *
 * Response:
 * {
 *   possible_conditions: string[],
 *   severity: "LOW" | "MODERATE" | "HIGH" | "EMERGENCY",
 *   recommended_action: string,
 *   sos_recommended: boolean,
 *   disclaimer: string
 * }
 */
export async function analyzeSymptoms(payload) {
  const { data } = await apiClient.post("/analyze", payload);
  return data;
}
