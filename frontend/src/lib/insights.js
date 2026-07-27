/**
 * Frontend-only insight derivation for the History page's dashboard.
 *
 * Deliberately the same spirit as app/insights/trends.py on the backend:
 * no chart library, no new dependency, just plain array math over data
 * the page already has in memory (entries from GET /history/{user_id}).
 * Nothing here calls the network - it's pure functions over already-
 * fetched data, so there's no new backend endpoint for this feature.
 */

// Ordered low -> high so index doubles as a plottable numeric score.
const SEVERITY_ORDER = ["LOW", "MODERATE", "HIGH", "EMERGENCY"];

/**
 * Turns history entries (most-recent-first, as returned by the API)
 * into a chronological (oldest-first) series suitable for a trend line:
 *   [{ id, date, severity, score }, ...]
 * `score` is 0-3 (LOW..EMERGENCY) - a simple ordinal, not a claim about
 * clinical distance between levels, just enough to plot a line.
 */
export function computeSeverityTrend(entries) {
  if (!entries?.length) return [];
  return [...entries]
    .reverse() // API gives newest-first; charts read left-to-right oldest-first
    .map((entry) => ({
      id: entry.id,
      date: entry.created_at,
      severity: entry.severity,
      score: Math.max(0, SEVERITY_ORDER.indexOf(entry.severity)),
    }));
}

/**
 * Counts how often each possible_conditions label appears across
 * entries, optionally restricted to the current calendar month
 * (server's/browser's local time - this is a lightweight glanceable
 * stat, not a precise report). Returns the top `limit` labels sorted
 * most-frequent-first: [{ label, count }, ...].
 *
 * Falls back to all-time counts if there's nothing in the current
 * month yet, so the chart isn't just empty on the 1st of the month.
 */
export function computeTopConditions(entries, { limit = 5 } = {}) {
  if (!entries?.length) return { items: [], scope: "all-time" };

  const now = new Date();
  const inCurrentMonth = (iso) => {
    const d = new Date(iso);
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
  };

  const tally = (list) => {
    const counts = new Map();
    for (const entry of list) {
      for (const condition of entry.possible_conditions ?? []) {
        counts.set(condition, (counts.get(condition) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .map(([label, count]) => ({ label, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  };

  const thisMonth = entries.filter((e) => inCurrentMonth(e.created_at));
  const monthItems = tally(thisMonth);
  if (monthItems.length > 0) {
    return { items: monthItems, scope: "this-month" };
  }
  return { items: tally(entries), scope: "all-time" };
}

export { SEVERITY_ORDER };
