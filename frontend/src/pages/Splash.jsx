import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Logo } from "@/components/common/Logo";
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
    <div className="flex h-screen flex-col items-center justify-center bg-primary px-6">
      <div className="flex flex-col items-center gap-6 animate-fade-up">
        <div className="flex size-20 items-center justify-center rounded-2xl bg-white/15">
          <svg width="44" height="44" viewBox="0 0 32 32" fill="none">
            <path
              d="M5 17h5l2-6 4 12 3-9 2 3h6"
              stroke="white"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div className="text-center">
          <h1 className="font-display text-2xl font-bold text-white">MediAssist AI</h1>
          <p className="mt-1 text-sm text-blue-100">Your health, understood instantly.</p>
        </div>
        <PulseLine className="w-40" color="rgba(255,255,255,0.5)" />
      </div>
    </div>
  );
}
