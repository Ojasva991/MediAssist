import { Droplet, User, Phone, Pill, ShieldAlert, HeartPulse } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-ink-soft">
        <Icon className="size-4" />
      </span>
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">{label}</p>
        <p className="mt-0.5 text-sm font-medium text-ink">{value || "—"}</p>
      </div>
    </div>
  );
}

function TextBlock({ icon: Icon, label, value, emptyText }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-ink-soft">
        <Icon className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">{label}</p>
        <p className="mt-0.5 text-sm text-ink">{value?.trim() ? value : <span className="text-ink-faint">{emptyText}</span>}</p>
      </div>
    </div>
  );
}

export function PassportSummary({ passport }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Personal details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <InfoRow icon={User} label="Full name" value={passport.name} />
          <div className="grid grid-cols-2 gap-4">
            <InfoRow icon={HeartPulse} label="Age" value={passport.age} />
            <InfoRow icon={Droplet} label="Blood group" value={passport.blood_group} />
          </div>
          <InfoRow
            icon={Phone}
            label="Emergency contact"
            value={
              passport.emergency_contact_name
                ? `${passport.emergency_contact_name} — ${passport.emergency_contact_phone ?? "no phone"}`
                : passport.emergency_contact_phone
            }
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Medical profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <TextBlock icon={ShieldAlert} label="Allergies" value={passport.allergies} emptyText="No known allergies recorded" />
          <TextBlock icon={HeartPulse} label="Chronic conditions" value={passport.chronic_diseases} emptyText="None recorded" />
          <TextBlock icon={Pill} label="Current medications" value={passport.medications} emptyText="None recorded" />
        </CardContent>
      </Card>
    </div>
  );
}
