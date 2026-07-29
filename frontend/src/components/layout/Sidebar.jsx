import { NavLink } from "react-router-dom";
import { LayoutGrid, Stethoscope, BookHeart, Clock, Bell, Pill, Siren, LogOut } from "lucide-react";
import { ROUTES } from "@/constants/routes";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", to: ROUTES.DASHBOARD, icon: LayoutGrid },
  { label: "Symptom Analysis", to: ROUTES.SYMPTOM_ANALYSIS, icon: Stethoscope },
  { label: "Health Passport", to: ROUTES.PASSPORT, icon: BookHeart },
  { label: "History", to: ROUTES.HISTORY, icon: Clock },
  { label: "Reminders", to: ROUTES.REMINDERS, icon: Bell },
  { label: "Drug Interactions", to: ROUTES.DRUG_INTERACTIONS, icon: Pill },
  { label: "SOS", to: ROUTES.SOS, icon: Siren, danger: true },
];

export function Sidebar({ className, onNavigate }) {
  const { user, logout } = useAuth();

  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col bg-[var(--color-abyss)] border-r border-[var(--color-abyss-line)]",
        className
      )}
    >
      <div className="flex h-16 items-center gap-2.5 px-5 border-b border-[var(--color-abyss-line)]">
        <svg width="22" height="22" viewBox="0 0 100 100" fill="none" className="shrink-0">
          <polyline
            points="14,22 38,74 46,52 53,80 60,52 86,22"
            fill="none"
            stroke="var(--color-success)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span className="font-display text-[1.05rem] font-medium tracking-tight text-[#FBFAF7]">
          vaeda
        </span>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS.map(({ label, to, icon: Icon, danger }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-r-md border-l-2 px-3.5 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? danger
                    ? "border-danger bg-danger/10 text-danger"
                    : "border-primary bg-primary/10 text-[var(--color-primary-light)]"
                  : "border-transparent text-[var(--color-abyss-ink-soft)] hover:bg-white/5 hover:text-[#FBFAF7]"
              )
            }
          >
            <Icon className="size-[18px] shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-[var(--color-abyss-line)] p-3">
        <div className="flex items-center gap-3 rounded-[var(--radius-control)] px-2 py-2">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-[#E4F3EF] font-display text-sm font-medium">
            {user?.name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-[#FBFAF7]">{user?.name ?? "Guest"}</p>
            <p className="truncate text-xs text-[var(--color-abyss-ink-faint)]">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            aria-label="Log out"
            className="rounded-md p-1.5 text-[var(--color-abyss-ink-faint)] transition-colors hover:bg-white/10 hover:text-danger"
          >
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
