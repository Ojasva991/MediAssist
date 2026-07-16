import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { Phone, ShieldAlert, Droplet, Pill, HeartPulse, ArrowLeft, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/context/AuthContext";
import { getPassport } from "@/api/passport";
import { ROUTES } from "@/constants/routes";

const EMERGENCY_NUMBER = "112"; // India's unified emergency number

export default function SOS() {
  const { user } = useAuth();
  const [passport, setPassport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getPassport(user.userId);
      setPassport(data);
    } catch (err) {
      if (err.status === 404) setPassport(null);
      else setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [user.userId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Link
        to={ROUTES.DASHBOARD}
        className="flex items-center gap-1.5 text-sm font-medium text-ink-soft transition-colors hover:text-ink"
      >
        <ArrowLeft className="size-4" /> Back to dashboard
      </Link>

      {/* Emergency call block */}
      <div className="rounded-[var(--radius-card)] bg-danger p-6 text-white sm:p-8">
        <div className="flex items-center gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-white/15">
            <ShieldAlert className="size-6" />
          </span>
          <div>
            <p className="font-display text-lg font-bold">Emergency SOS</p>
            <p className="text-sm text-red-100">If this is life-threatening, call now.</p>
          </div>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          <Button asChild size="lg" className="bg-white text-danger hover:bg-red-50">
            <a href={`tel:${EMERGENCY_NUMBER}`}>
              <Phone className="size-4" /> Call {EMERGENCY_NUMBER}
            </a>
          </Button>
          {passport?.emergency_contact_phone && (
            <Button
              asChild
              size="lg"
              variant="outline"
              className="border-white/40 bg-transparent text-white hover:bg-white/10"
            >
              <a href={`tel:${passport.emergency_contact_phone}`}>
                <Phone className="size-4" />
                Call {passport.emergency_contact_name || "emergency contact"}
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Critical info at a glance */}
      <div>
        <h2 className="mb-3 font-display text-sm font-semibold uppercase tracking-wide text-ink-faint">
          Show this to first responders
        </h2>

        {isLoading && (
          <div className="flex h-40 items-center justify-center text-ink-faint">
            <Spinner size={22} className="mr-2" /> Loading your medical info...
          </div>
        )}

        {error && (
          <div className="rounded-[var(--radius-control)] bg-danger-light px-4 py-3 text-sm text-danger">
            {error.message}
            <Button variant="link" className="ml-1 h-auto p-0 text-danger" onClick={load}>
              Retry
            </Button>
          </div>
        )}

        {!isLoading && !error && !passport && (
          <div className="rounded-[var(--radius-card)] border border-dashed border-border bg-surface p-8 text-center">
            <p className="text-sm text-ink-soft">
              No health passport on file yet. Add one so responders have what they need.
            </p>
            <Button asChild className="mt-4" size="sm">
              <Link to={ROUTES.PASSPORT}>Create health passport</Link>
            </Button>
          </div>
        )}

        {!isLoading && passport && (
          <div className="space-y-4 rounded-[var(--radius-card)] border border-border bg-surface p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
              <div>
                <p className="font-display text-lg font-bold text-ink">{passport.name}</p>
                <p className="text-sm text-ink-soft">
                  {passport.age ? `${passport.age} years` : ""}
                </p>
              </div>
              {passport.blood_group && passport.blood_group !== "UNKNOWN" && (
                <span className="flex items-center gap-1.5 rounded-full bg-danger-light px-3 py-1.5 text-sm font-bold text-danger">
                  <Droplet className="size-4" /> {passport.blood_group}
                </span>
              )}
            </div>

            <InfoBlock icon={ShieldAlert} label="Allergies" value={passport.allergies} emptyText="No known allergies recorded" />
            <InfoBlock icon={HeartPulse} label="Chronic conditions" value={passport.chronic_diseases} emptyText="None recorded" />
            <InfoBlock icon={Pill} label="Current medications" value={passport.medications} emptyText="None recorded" />
          </div>
        )}
      </div>

      {!isLoading && (
        <Button variant="ghost" size="sm" onClick={load} className="mx-auto flex">
          <RefreshCcw className="size-3.5" /> Refresh info
        </Button>
      )}
    </div>
  );
}

function InfoBlock({ icon: Icon, label, value, emptyText }) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-faint">
        <Icon className="size-3.5" /> {label}
      </p>
      <p className="mt-1 text-sm text-ink">
        {value?.trim() ? value : <span className="text-ink-faint">{emptyText}</span>}
      </p>
    </div>
  );
}
