import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PulseLine } from "@/components/common/PulseLine";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";

export default function Splash() {
  const navigate = useNavigate();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    const timer = setTimeout(() => {
      navigate(user ? ROUTES.DASHBOARD : ROUTES.LOGIN, { replace: true });
    }, 1200);
    return () => clearTimeout(timer);
  }, [isLoading, user, navigate]);

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-[var(--color-abyss)] px-6">
      <div className="flex flex-col items-center gap-6 animate-fade-up">
        <svg width="46" height="46" viewBox="0 0 100 100" fill="none">
          <polyline
            points="14,22 38,74 46,52 53,80 60,52 86,22"
            fill="none"
            stroke="var(--color-success)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div className="text-center">
          <h1 className="font-display text-2xl font-medium text-[#FBFAF7]">vaeda</h1>
          <p className="mt-1 text-sm text-[var(--color-abyss-ink-soft)]">
            Your health, understood instantly.
          </p>
        </div>
        <PulseLine className="w-40" color="var(--color-success)" />
      </div>
    </div>
  );
}
