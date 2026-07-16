import { cn } from "@/lib/utils";

/**
 * The app's signature element: a thin, continuously-traveling ECG-style
 * stroke. Used sparingly — in the topbar brand mark and on loading/analysis
 * states — to reinforce "live vitals" without resorting to generic spinners
 * everywhere.
 */
export function PulseLine({ className, color = "currentColor" }) {
  return (
    <svg
      viewBox="0 0 240 40"
      className={cn("w-full h-auto overflow-visible", className)}
      preserveAspectRatio="none"
    >
      <path
        d="M0 20 H60 L72 20 L80 6 L92 34 L102 20 L112 20 L120 12 L128 28 L136 20 H240"
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="6 6"
        className="animate-[pulse-line_2.4s_linear_infinite]"
      />
    </svg>
  );
}
