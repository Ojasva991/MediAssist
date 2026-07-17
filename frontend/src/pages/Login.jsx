import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { ShieldCheck, Stethoscope, BookHeart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Logo } from "@/components/common/Logo";
import { PulseLine } from "@/components/common/PulseLine";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";

const FEATURES = [
  { icon: Stethoscope, text: "AI-powered symptom analysis in seconds" },
  { icon: BookHeart, text: "One portable health passport, always with you" },
  { icon: ShieldCheck, text: "Built for emergencies, designed for calm" },
];

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (user) return <Navigate to={ROUTES.DASHBOARD} replace />;

  function validate() {
    const next = {};
    if (!name.trim()) next.name = "Enter your full name.";
    if (!/^\S+@\S+\.\S+$/.test(email)) next.email = "Enter a valid email address.";
    if (password.length < 8) next.password = "Password must be at least 8 characters.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;
    setIsSubmitting(true);
    try {
      await login({ name, email, password });
      navigate(ROUTES.DASHBOARD);
    } catch (err) {
      setErrors({ form: err.message || "Sign in failed. Please try again." });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-primary p-10 text-white lg:flex">
        <Logo className="[&_span]:text-white" />

        <div className="max-w-sm">
          <h2 className="font-display text-3xl font-bold leading-tight">
            Clarity, right when you need it most.
          </h2>
          <p className="mt-3 text-sm text-blue-100">
            MediAssist AI reads your symptoms, gives you a clear next step, and keeps
            your full medical history one tap away — even in an emergency.
          </p>
          <ul className="mt-8 space-y-4">
            {FEATURES.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-white/15">
                  <Icon className="size-4" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>

        <PulseLine className="w-full opacity-60" color="rgba(255,255,255,0.6)" />
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center bg-bg px-6 py-12">
        <div className="w-full max-w-sm animate-fade-up">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>

          <h1 className="font-display text-2xl font-bold text-ink">Welcome back</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Sign in to access your symptom analysis and health passport.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                placeholder="Jordan Lee"
                value={name}
                onChange={(e) => setName(e.target.value)}
                aria-invalid={!!errors.name}
              />
              {errors.name && <p className="text-xs text-danger">{errors.name}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={!!errors.email}
              />
              {errors.email && <p className="text-xs text-danger">{errors.email}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={!!errors.password}
              />
              {errors.password && <p className="text-xs text-danger">{errors.password}</p>}
            </div>

            {errors.form && <p className="text-xs text-danger">{errors.form}</p>}

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Signing in..." : "Continue"}
            </Button>

            <p className="text-center text-xs text-ink-faint">
              First time here? Just enter your details — an account will be created
              automatically.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
