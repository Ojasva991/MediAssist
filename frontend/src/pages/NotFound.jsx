import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/constants/routes";

export default function NotFound() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-3 bg-bg px-6 text-center">
      <p className="font-display text-6xl font-bold text-primary">404</p>
      <h1 className="font-display text-lg font-semibold text-ink">Page not found</h1>
      <p className="max-w-xs text-sm text-ink-soft">
        The page you're looking for doesn't exist or may have moved.
      </p>
      <Button asChild className="mt-2">
        <Link to={ROUTES.DASHBOARD}>Go to dashboard</Link>
      </Button>
    </div>
  );
}
