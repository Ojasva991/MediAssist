import { Menu, Siren } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/constants/routes";

const TITLES = {
  [ROUTES.DASHBOARD]: "Dashboard",
  [ROUTES.SYMPTOM_ANALYSIS]: "Symptom Analysis",
  [ROUTES.ANALYSIS_RESULT]: "Analysis Result",
  [ROUTES.PASSPORT]: "Health Passport",
  [ROUTES.SOS]: "Emergency SOS",
};

export function Topbar({ onMenuClick }) {
  const { pathname } = useLocation();
  const title = TITLES[pathname] ?? "MediAssist AI";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-surface/90 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="rounded-md p-2 text-ink-soft hover:bg-slate-100 lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="size-5" />
        </button>
        <h1 className="font-display text-base font-semibold text-ink sm:text-lg">{title}</h1>
      </div>

      {pathname !== ROUTES.SOS && (
        <Button asChild variant="danger" size="sm">
          <Link to={ROUTES.SOS}>
            <Siren className="size-4" />
            <span className="hidden sm:inline">SOS</span>
          </Link>
        </Button>
      )}
    </header>
  );
}
