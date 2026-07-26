import { forwardRef } from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-control)] text-sm font-semibold transition-all duration-150 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-white shadow-[0_1px_2px_rgba(15,107,92,0.3)] hover:bg-primary-dark active:scale-[0.98]",
        danger:
          "bg-danger text-white shadow-[0_1px_2px_rgba(220,38,38,0.3)] hover:bg-danger-dark active:scale-[0.98]",
        outline:
          "border border-border bg-surface text-ink hover:bg-[var(--color-mist)] active:scale-[0.98]",
        ghost: "text-ink-soft hover:bg-[var(--color-mist)] hover:text-ink",
        link: "text-primary underline-offset-4 hover:underline",
        subtle: "bg-primary-light text-primary-dark hover:bg-primary-light/70",
      },
      size: {
        default: "h-11 px-5",
        sm: "h-9 px-3.5 text-[0.8rem]",
        lg: "h-13 px-7 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

const Button = forwardRef(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
