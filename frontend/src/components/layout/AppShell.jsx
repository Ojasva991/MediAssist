import { useState } from "react";
import { Outlet, Navigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { X } from "lucide-react";

export function AppShell() {
  const { user, isLoading } = useAuth();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  if (isLoading) return null;
  if (!user) return <Navigate to={ROUTES.LOGIN} replace />;

  return (
    <div className="flex h-screen overflow-hidden bg-bg">
      <Sidebar className="hidden lg:flex" />

      {mobileNavOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-ink/40"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full animate-fade-up">
            <Sidebar className="flex" onNavigate={() => setMobileNavOpen(false)} />
            <button
              onClick={() => setMobileNavOpen(false)}
              className="absolute right-3 top-3 rounded-md bg-surface p-1.5 shadow-md"
              aria-label="Close menu"
            >
              <X className="size-4" />
            </button>
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
