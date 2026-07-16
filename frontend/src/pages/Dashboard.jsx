import { Stethoscope, BookHeart, Siren, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { FeatureCard } from "@/components/dashboard/FeatureCard";
import { Button } from "@/components/ui/button";
import { PulseLine } from "@/components/common/PulseLine";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";

export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.name?.split(" ")[0] ?? "there";

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-[var(--radius-card)] bg-primary p-8 text-white sm:p-10">
        <div className="relative z-10 max-w-lg">
          <p className="text-sm font-medium text-blue-100">Good to see you, {firstName}</p>
          <h1 className="mt-2 font-display text-2xl font-bold leading-tight sm:text-3xl">
            How are you feeling today?
          </h1>
          <p className="mt-2 text-sm text-blue-100">
            Describe your symptoms and get an instant AI-powered read on what might be
            going on — plus clear next steps.
          </p>
          <Button asChild variant="default" size="lg" className="mt-6 bg-white text-primary hover:bg-blue-50">
            <Link to={ROUTES.SYMPTOM_ANALYSIS}>
              Start symptom analysis
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
        <PulseLine className="absolute inset-x-0 bottom-0 w-full opacity-30" color="white" />
      </div>

      {/* Feature grid */}
      <div>
        <h2 className="mb-3 font-display text-sm font-semibold uppercase tracking-wide text-ink-faint">
          Quick actions
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <FeatureCard
            to={ROUTES.SYMPTOM_ANALYSIS}
            icon={Stethoscope}
            title="AI Symptom Analysis"
            description="Enter what you're experiencing and get an AI-generated assessment in seconds."
            accent="primary"
          />
          <FeatureCard
            to={ROUTES.PASSPORT}
            icon={BookHeart}
            title="Health Passport"
            description="Your allergies, conditions, and medications — stored, editable, and ready to share."
            accent="success"
          />
          <FeatureCard
            to={ROUTES.SOS}
            icon={Siren}
            title="Emergency SOS"
            description="One tap to surface your critical health info when every second counts."
            accent="danger"
          />
        </div>
      </div>
    </div>
  );
}
