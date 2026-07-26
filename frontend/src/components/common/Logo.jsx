import { cn } from "@/lib/utils";

/**
 * The Vaeda mark: a single continuous stroke that is both a "V" and an
 * ECG-style pulse -- the heartbeat sits exactly at the vertex of the V,
 * so the two ideas share one line rather than being two motifs glued
 * together. Scales cleanly down to favicon size.
 */
export function Logo({ className, iconOnly = false }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <svg width="28" height="28" viewBox="0 0 100 100" fill="none" className="shrink-0">
        <polyline
          points="14,22 38,74 46,52 53,80 60,52 86,22"
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="9"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {!iconOnly && (
        <span className="font-display text-[1.15rem] font-medium tracking-tight text-ink">
          vaeda
        </span>
      )}
    </div>
  );
}
