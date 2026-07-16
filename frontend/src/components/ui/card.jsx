import { forwardRef } from "react";
import { cn } from "@/lib/utils";

const Card = forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-[var(--radius-card)] border border-border bg-surface shadow-[var(--shadow-card)] transition-shadow",
      className
    )}
    {...props}
  />
));
Card.displayName = "Card";

const CardHeader = forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col gap-1.5 p-6", className)} {...props} />
));
CardHeader.displayName = "CardHeader";

const CardTitle = forwardRef(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("font-display text-lg font-semibold leading-tight text-ink", className)}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = forwardRef(({ className, ...props }, ref) => (
  <p ref={ref} className={cn("text-sm text-ink-soft", className)} {...props} />
));
CardDescription.displayName = "CardDescription";

const CardContent = forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("flex items-center p-6 pt-0", className)} {...props} />
));
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
