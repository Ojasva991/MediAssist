import { apiClient } from "./client";

/**
 * GET /history/{user_id}
 *
 * Confirmed against the live backend's AnalysisHistoryItem model
 * (app/models/history.py). Requires authentication; the caller's
 * user_id must match the URL. Returns past analyses, most recent
 * first, each including a `feedback` field (true/false/null).
 */
export async function getHistory(userId, limit = 20) {
  const { data } = await apiClient.get(`/history/${userId}`, { params: { limit } });
  return data;
}

/**
 * GET /history/{user_id}/trends
 *
 * Recurring symptom keywords detected across recent history (see
 * app/insights/trends.py on the backend). Returns [] if there isn't
 * enough recent history for a pattern to be meaningful - never an
 * error, just an empty result.
 */
export async function getTrends(userId) {
  const { data } = await apiClient.get(`/history/${userId}/trends`);
  return data;
}

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
