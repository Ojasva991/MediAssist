import { forwardRef } from "react";
import { cn } from "@/lib/utils";

const Input = forwardRef(({ className, type = "text", ...props }, ref) => {
  return (
    <input
      type={type}
      ref={ref}
      className={cn(
        "flex h-11 w-full rounded-[var(--radius-control)] border border-border bg-surface px-3.5 text-sm text-ink placeholder:text-ink-faint transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:border-primary",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
});
Input.displayName = "Input";

export { Input };
