import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "bg-primary-light text-primary-dark",
        success: "bg-success-light text-success",
        warning: "bg-warning-light text-warning",
        danger: "bg-danger-light text-danger",
        neutral: "bg-slate-100 text-ink-soft",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

function Badge({ className, variant, ...props }) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
