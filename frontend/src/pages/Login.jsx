import { useState } from "react";
import { useNavigate, Navigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PulseLine } from "@/components/common/PulseLine";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (user) return <Navigate to={ROUTES.DASHBOARD} replace />;

  function validate() {
    const next = {};
    if (!/^\S+@\S+\.\S+$/.test(email)) next.email = "Enter a valid email address.";
    if (!password) next.password = "Enter your password.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;
    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate(ROUTES.DASHBOARD);
    } catch (err) {
      setErrors({ form: err.message || "Incorrect email or password." });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[var(--color-abyss)] px-6 py-12">
      <div className="relative z-10 flex w-full max-w-sm flex-col items-center animate-fade-up">
        <svg width="40" height="40" viewBox="0 0 100 100" fill="none" className="shrink-0">
          <polyline
            points="14,22 38,74 46,52 53,80 60,52 86,22"
            fill="none"
            stroke="var(--color-success)"
            strokeWidth="9"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <h1 className="mt-4 font-display text-xl font-medium tracking-tight text-[#FBFAF7]">
          vaeda
        </h1>

        <div className="mt-8 w-full rounded-[var(--radius-card)] border border-[var(--color-abyss-line)] bg-[var(--color-abyss-soft)] p-7 shadow-[var(--shadow-card-hover)] sm:p-8">
          <h2 className="font-display text-lg font-semibold text-[#FBFAF7]">Welcome back</h2>
          <p className="mt-1 text-sm text-[var(--color-abyss-ink-soft)]">
            Sign in to access your symptom analysis and health passport.
          </p>

          <form onSubmit={handleSubmit} className="mt-7 space-y-5" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-[var(--color-abyss-ink-soft)]">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={!!errors.email}
                className="border-[var(--color-abyss-line)] bg-[var(--color-abyss)] text-[#FBFAF7] placeholder:text-[var(--color-abyss-ink-faint)] focus-visible:border-primary focus-visible:ring-primary/30"
              />
              {errors.email && <p className="text-xs text-danger">{errors.email}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-[var(--color-abyss-ink-soft)]">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={!!errors.password}
                className="border-[var(--color-abyss-line)] bg-[var(--color-abyss)] text-[#FBFAF7] placeholder:text-[var(--color-abyss-ink-faint)] focus-visible:border-primary focus-visible:ring-primary/30"
              />
              {errors.password && <p className="text-xs text-danger">{errors.password}</p>}
            </div>

            {errors.form && <p className="text-xs text-danger">{errors.form}</p>}

            <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
              {isSubmitting ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          <div className="my-6 flex items-center gap-3">
            <span className="h-px flex-1 bg-[var(--color-abyss-line)]" />
            <span className="text-xs uppercase tracking-wide text-[var(--color-abyss-ink-faint)]">or</span>
            <span className="h-px flex-1 bg-[var(--color-abyss-line)]" />
          </div>

          <p className="text-center text-sm text-[var(--color-abyss-ink-soft)]">
            New here?{" "}
            <Link to={ROUTES.SIGNUP} className="font-medium text-[var(--color-success)] hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </div>

      <PulseLine
        className="absolute inset-x-0 bottom-0 w-full opacity-40"
        color="var(--color-success)"
      />
    </div>
  );
}
