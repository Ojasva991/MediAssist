import { apiClient } from "./client";

export async function getAdminAnalytics(windowDays = 30) {
  const { data } = await apiClient.get("/admin/analytics", {
    params: { window_days: windowDays },
  });
  return data;
}
