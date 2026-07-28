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

/**
 * POST /analyze/image (multipart/form-data)
 *
 * `image` is a File/Blob. All other fields optional - a photo can be
 * submitted with zero accompanying text, unlike POST /analyze.
 *
 * Response shape is the same SymptomAnalysisResponse as analyzeSymptoms(),
 * plus:
 *   visual_observation?: string  // what the AI saw, in its own words
 *   image_rejected: boolean      // true if this looked like a medical
 *                                // scan/document rather than a symptom photo
 */
export async function analyzeImage({
  image,
  symptoms,
  duration,
  age,
  gender,
  existingConditions,
}) {
  const formData = new FormData();
  formData.append("image", image);
  if (symptoms) formData.append("symptoms", symptoms);
  if (duration) formData.append("duration", duration);
  if (age !== undefined && age !== null && age !== "") formData.append("age", age);
  if (gender) formData.append("gender", gender);
  if (existingConditions) formData.append("existing_conditions", existingConditions);

  const { data } = await apiClient.post("/analyze/image", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
