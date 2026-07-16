import { NavLink } from "react-router-dom";
import { LayoutGrid, Stethoscope, BookHeart, Siren, LogOut } from "lucide-react";
import { Logo } from "@/components/common/Logo";
import { ROUTES } from "@/constants/routes";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", to: ROUTES.DASHBOARD, icon: LayoutGrid },
  { label: "Symptom Analysis", to: ROUTES.SYMPTOM_ANALYSIS, icon: Stethoscope },
  { label: "Health Passport", to: ROUTES.PASSPORT, icon: BookHeart },
  { label: "SOS", to: ROUTES.SOS, icon: Siren, danger: true },
];

export function Sidebar({ className, onNavigate }) {
  const { user, logout } = useAuth();

  return (
    <aside className={cn("flex h-full w-64 flex-col border-r border-border bg-surface", className)}>
      <div className="flex h-16 items-center px-5 border-b border-border">
        <Logo />
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map(({ label, to, icon: Icon, danger }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-[var(--radius-control)] px-3.5 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? danger
                    ? "bg-danger-light text-danger"
                    : "bg-primary-light text-primary-dark"
                  : "text-ink-soft hover:bg-slate-50 hover:text-ink"
              )
            }
          >
            <Icon className="size-[18px] shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        <div className="flex items-center gap-3 rounded-[var(--radius-control)] px-2 py-2">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-light font-display text-sm font-semibold text-primary-dark">
            {user?.name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">{user?.name ?? "Guest"}</p>
            <p className="truncate text-xs text-ink-faint">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            aria-label="Log out"
            className="rounded-md p-1.5 text-ink-faint transition-colors hover:bg-slate-100 hover:text-danger"
          >
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
