import { cn } from "@/lib/utils";

/**
 * A pulsing placeholder block. Compose these into shapes that match the
 * real content that's about to load — reduces perceived wait time far
 * more than a centered spinner does.
 *
 * Usage: <Skeleton className="h-4 w-32" /> for a text line,
 *        <Skeleton className="size-9 rounded-full" /> for an avatar, etc.
 */
export function Skeleton({ className }) {
  return <div className={cn("animate-pulse rounded-md bg-border", className)} />;
}
