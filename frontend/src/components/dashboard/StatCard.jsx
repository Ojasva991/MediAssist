import { cn } from "@/lib/utils";

/**
 * Small porcelain stat card for the Dashboard hero row. `tone="good"`
 * gives it the jade treatment for a positive/complete state; default is
 * neutral. Values are rendered in the mono face, matching the rest of
 * the app's "data" typography (blood group badges, ages, etc.).
 *
 * Every instance of this on Dashboard.jsx is backed by a real field
 * from GET /passport/{user_id} - see the comment in Dashboard.jsx for
 * why there's no numeric "risk score" or activity-count card here.
 */
export function StatCard({ label, value, icon: Icon, tone = "neutral" }) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-[var(--radius-card)] border p-4",
        tone === "good"
          ? "border-primary/20 bg-primary-light"
          : "border-border bg-surface"
      )}
    >
      <span
        className={cn(
          "flex size-9 shrink-0 items-center justify-center rounded-lg",
          tone === "good" ? "bg-primary text-white" : "bg-[var(--color-mist)] text-ink-soft"
        )}
      >
        <Icon className="size-4" />
      </span>
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">{label}</p>
        <p
          className={cn(
            "truncate font-mono text-base font-medium",
            tone === "good" ? "text-primary-dark" : "text-ink"
          )}
        >
          {value}
        </p>
      </div>
    </div>
  );
}
