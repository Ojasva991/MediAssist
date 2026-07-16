import { cn } from "@/lib/utils";

export function Logo({ className, iconOnly = false }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <svg width="30" height="30" viewBox="0 0 32 32" fill="none" className="shrink-0">
        <rect width="32" height="32" rx="9" fill="#2563EB" />
        <path
          d="M5 17h5l2-6 4 12 3-9 2 3h6"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {!iconOnly && (
        <span className="font-display text-[1.05rem] font-bold tracking-tight text-ink">
          MediAssist<span className="text-primary"> AI</span>
        </span>
      )}
    </div>
  );
}
