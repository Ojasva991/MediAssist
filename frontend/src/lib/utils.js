import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge conditional classnames and resolve Tailwind conflicts.
 * Usage: cn("p-4", condition && "p-6", className)
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
