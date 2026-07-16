import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function FeatureCard({ to, icon: Icon, title, description, accent = "primary" }) {
  const accentClasses = {
    primary: "bg-primary-light text-primary-dark",
    danger: "bg-danger-light text-danger",
    success: "bg-success-light text-success",
  };

  return (
    <Link to={to} className="group block">
      <Card className="h-full p-6 transition-all hover:-translate-y-0.5 hover:shadow-[var(--shadow-card-hover)]">
        <div className="flex items-start justify-between">
          <span className={cn("flex size-11 items-center justify-center rounded-xl", accentClasses[accent])}>
            <Icon className="size-5" />
          </span>
          <ArrowUpRight className="size-4 text-ink-faint transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-ink-soft" />
        </div>
        <h3 className="mt-4 font-display text-base font-semibold text-ink">{title}</h3>
        <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{description}</p>
      </Card>
    </Link>
  );
}
