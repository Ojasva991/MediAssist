import { useCallback, useEffect, useState } from "react";
import { Stethoscope, BookHeart, Siren, ArrowRight, Droplet, Phone, ShieldCheck, Clock, Bell, Pill, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { FeatureCard } from "@/components/dashboard/FeatureCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { Button } from "@/components/ui/button";
import { PulseLine } from "@/components/common/PulseLine";
import { useAuth } from "@/context/AuthContext";
import { getPassport } from "@/api/passport";
import { ROUTES } from "@/constants/routes";

export default function Dashboard() {
  const { user } = useAuth();
  const firstName = user?.name?.split(" ")[0] ?? "there";

  // The Dashboard's stat row only ever shows fields that genuinely exist
  // on the Health Passport (see src/api/passport.js) - age, blood group,
  // and whether an emergency contact is on file. There is deliberately
  // no numeric "risk score" or "recent activity" card here: the backend
  // has no such endpoint (GET /analyze returns a one-off result, not a
  // history list, and there's no scoring concept in the API at all).
  // TODO(backend): if/when a GET /history/{user_id} endpoint exists,
  // a real "last check-in" stat could be added here instead of omitted.
  const [passport, setPassport] = useState(null);
  const [isLoadingPassport, setIsLoadingPassport] = useState(true);

  const loadPassport = useCallback(async () => {
    setIsLoadingPassport(true);
    try {
      const data = await getPassport(user.userId);
      setPassport(data);
    } catch {
      // 404 just means no passport yet - a normal, expected state here,
      // not an error worth surfacing on the Dashboard itself (the
      // Passport page already owns that error state).
      setPassport(null);
    } finally {
      setIsLoadingPassport(false);
    }
  }, [user.userId]);

  useEffect(() => {
    loadPassport();
  }, [loadPassport]);

  const hasPassport = !!passport;
  const hasEmergencyContact = !!passport?.emergency_contact_phone;

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-[var(--radius-card)] bg-primary p-8 text-white sm:p-10">
        <div className="relative z-10 max-w-lg">
          <p className="text-sm font-medium text-[var(--color-primary-light)]">
            Good to see you, {firstName}
          </p>
          <h1 className="mt-2 font-display text-2xl font-medium leading-tight sm:text-3xl">
            How are you feeling today?
          </h1>
          <p className="mt-2 text-sm text-[var(--color-primary-light)]">
            Describe your symptoms and get an instant AI-powered read on what might be
            going on — plus clear next steps.
          </p>
          <Button asChild variant="default" size="lg" className="mt-6 bg-white text-primary hover:bg-primary-light">
            <Link to={ROUTES.SYMPTOM_ANALYSIS}>
              Start symptom analysis
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
        <PulseLine className="absolute inset-x-0 bottom-0 w-full opacity-30" color="white" />
      </div>

      {/* Stat row - every value here comes straight from the Health
          Passport; nothing is fabricated to fill space. */}
      <div className="grid gap-3 sm:grid-cols-3">
        {isLoadingPassport ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-[68px] animate-pulse rounded-[var(--radius-card)] bg-border" />
          ))
        ) : (
          <>
            <StatCard
              label="Health Passport"
              value={hasPassport ? "Complete" : "Not set up"}
              icon={ShieldCheck}
              tone={hasPassport ? "good" : "neutral"}
            />
            <StatCard
              label="Blood group"
              value={hasPassport && passport.blood_group !== "UNKNOWN" ? passport.blood_group : "Not set"}
              icon={Droplet}
            />
            <StatCard
              label="Emergency contact"
              value={hasEmergencyContact ? "On file" : "Missing"}
              icon={Phone}
              tone={hasEmergencyContact ? "good" : "neutral"}
            />
          </>
        )}
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
            to={ROUTES.HISTORY}
            icon={Clock}
            title="History"
            description="Every past analysis, with trends and severity over time."
            accent="neutral"
          />
          <FeatureCard
            to={ROUTES.REMINDERS}
            icon={Bell}
            title="Reminders"
            description="Medication and follow-up reminders, one-time or recurring."
            accent="warning"
          />
          <FeatureCard
            to={ROUTES.DRUG_INTERACTIONS}
            icon={Pill}
            title="Drug Interactions"
            description="Check your medications against well-known, well-documented interactions."
            accent="warning"
          />
          <FeatureCard
            to={ROUTES.CAREGIVERS}
            icon={Users}
            title="Caregivers & Family"
            description="Give a trusted person read-only access, or manage reminders for someone else."
            accent="primary"
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
