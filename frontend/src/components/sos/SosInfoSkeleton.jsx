import { Skeleton } from "@/components/ui/skeleton";

/**
 * Mirrors the shape of SOS.jsx's "critical info at a glance" card
 * (name/age header row + three labeled info blocks).
 */
export function SosInfoSkeleton() {
  return (
    <div className="space-y-4 rounded-[var(--radius-card)] border border-border bg-surface p-5">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
        <div className="space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="h-7 w-16 rounded-full" />
      </div>

      {[0, 1, 2].map((i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-3 w-28" />
          <Skeleton className="h-4 w-full max-w-xs" />
        </div>
      ))}
    </div>
  );
}
