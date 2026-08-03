import { useState, useEffect } from "react";
import {
  Users,
  Stethoscope,
  Bell,
  UserCheck,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Siren,
  Cpu,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { getAdminAnalytics } from "@/api/adminAnalytics";

function StatCard({ icon: Icon, label, value, accent = "primary" }) {
  const accentClasses = {
    primary: "bg-primary-light text-primary-dark",
    danger: "bg-danger-light text-danger",
    success: "bg-success-light text-success",
    warning: "bg-warning-light text-warning",
    neutral: "bg-[var(--color-mist)] text-ink-soft",
  };
  return (
    <div className="rounded-[var(--radius-card)] border border-border bg-surface p-4">
      <div className="flex items-center gap-2">
        <div className={`flex size-8 items-center justify-center rounded-full ${accentClasses[accent]}`}>
          <Icon className="size-4" />
        </div>
        <p className="text-xs font-medium text-ink-faint">{label}</p>
      </div>
      <p className="mt-2 font-display text-2xl font-medium text-ink">{value}</p>
    </div>
  );
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export default function AdminAnalytics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getAdminAnalytics(30)
      .then(setData)
      .catch((err) => setError(err.message || "Couldn't load analytics."))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-danger">{error}</p>;
  }

  const p = data.ai_provider_stats;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-medium text-ink">Admin Analytics</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Every number below is a real query against live data - nothing here is estimated.
          Window: last {data.window_days} days for time-scoped metrics.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Users} label="Total users" value={data.total_users} />
        <StatCard icon={Stethoscope} label="Total analyses" value={data.total_analyses} accent="success" />
        <StatCard icon={Siren} label="SOS recommended" value={data.sos_recommended_count} accent="danger" />
        <StatCard icon={Bell} label="Active reminders" value={data.active_reminders} accent="warning" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Severity breakdown (all-time)</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Object.entries(data.severity_breakdown).map(([severity, count]) => (
            <div key={severity} className="rounded-[var(--radius-control)] bg-[var(--color-mist)] p-3 text-center">
              <p className="font-mono text-xs text-ink-faint">{severity}</p>
              <p className="mt-1 font-display text-xl text-ink">{count}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Cpu className="size-4 text-primary" /> AI provider usage
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-[var(--radius-control)] bg-[var(--color-mist)] p-3">
              <p className="text-xs font-medium text-ink-faint">Gemini</p>
              <p className="mt-1 text-sm text-ink">
                {p.gemini.success} ok / {p.gemini.failure} failed
              </p>
              {p.gemini_avg_latency_ms != null && (
                <p className="mt-0.5 font-mono text-xs text-ink-faint">
                  avg {p.gemini_avg_latency_ms}ms
                </p>
              )}
            </div>
            <div className="rounded-[var(--radius-control)] bg-[var(--color-mist)] p-3">
              <p className="text-xs font-medium text-ink-faint">Groq</p>
              <p className="mt-1 text-sm text-ink">
                {p.groq.success} ok / {p.groq.failure} failed
              </p>
              {p.groq_avg_latency_ms != null && (
                <p className="mt-0.5 font-mono text-xs text-ink-faint">
                  avg {p.groq_avg_latency_ms}ms
                </p>
              )}
            </div>
            <div className="rounded-[var(--radius-control)] bg-danger-light p-3">
              <p className="text-xs font-medium text-danger">Fell through to rule engine</p>
              <p className="mt-1 text-sm text-danger">{p.all_failed} requests</p>
            </div>
          </div>
          <p className="flex items-start gap-1.5 text-xs text-ink-faint">
            <Info className="mt-0.5 size-3.5 shrink-0" /> {p.note}
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <UserCheck className="size-4 text-primary" /> Caregiver links
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-ink-soft">
            <p>Active: {data.caregiver_links_active}</p>
            <p>Pending: {data.caregiver_links_pending}</p>
            <p>Revoked: {data.caregiver_links_revoked}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <FileText className="size-4 text-primary" /> Passport documents
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-ink-soft">
            <p>{data.total_passport_documents} files uploaded</p>
            <p>{formatBytes(data.total_document_storage_bytes)} total storage used</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Reminders</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-ink-soft">
            <p>{data.total_reminders} total created</p>
            <p>{data.active_reminders} currently active</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Analysis feedback</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4 text-sm text-ink-soft">
            <span className="flex items-center gap-1.5">
              <ThumbsUp className="size-3.5 text-success" /> {data.feedback_positive}
            </span>
            <span className="flex items-center gap-1.5">
              <ThumbsDown className="size-3.5 text-danger" /> {data.feedback_negative}
            </span>
          </CardContent>
        </Card>
      </div>

      {data.signups_by_day.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Signups by day (recent, where recorded)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {data.signups_by_day.map((d) => (
                <span
                  key={d.date}
                  className="rounded-full bg-[var(--color-mist)] px-2.5 py-1 font-mono text-xs text-ink-soft"
                >
                  {d.date}: {d.count}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
