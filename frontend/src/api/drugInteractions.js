import { apiClient } from "./client";

/**
 * POST /drug-interactions/check - public, no auth required.
 * Purely deterministic on the backend (matched against a small curated
 * list, no AI call) - see app/interactions/matcher.py.
 */
export async function checkDrugInteractions(drugs) {
  const { data } = await apiClient.post("/drug-interactions/check", { drugs });
  return data;
}
