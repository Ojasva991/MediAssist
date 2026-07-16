import { apiClient } from "./client";

/**
 * POST /analyze
 *
 * Confirmed against the live backend's SymptomAnalysisRequest /
 * SymptomAnalysisResponse models (app/models/symptom.py).
 *
 * Request:
 * {
 *   age: number,               // required, 0-120
 *   gender: string,            // required
 *   symptoms: string,          // required, single free-text string (not an array)
 *   duration: string,          // required, e.g. "3 days"
 *   existing_conditions?: string
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
