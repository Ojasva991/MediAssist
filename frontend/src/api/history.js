import { apiClient } from "./client";

/**
 * POST /history/{user_id}/{history_id}/feedback
 *
 * Confirmed against the live backend's FeedbackRequest model
 * (app/models/history.py). Requires authentication - the caller's
 * user_id must match the URL, and the history_id must belong to them
 * (enforced server-side either way, see app/routes/history.py).
 *
 * Request: { is_helpful: boolean }
 * Response: { status: "recorded", history_id: number, is_helpful: boolean }
 */
export async function submitAnalysisFeedback(userId, historyId, isHelpful) {
  const { data } = await apiClient.post(`/history/${userId}/${historyId}/feedback`, {
    is_helpful: isHelpful,
  });
  return data;
}
