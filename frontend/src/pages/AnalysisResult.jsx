import { useLocation, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, RefreshCcw, Siren } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SeverityBadge } from "@/components/symptom/SeverityBadge";
import { ROUTES } from "@/constants/routes";

export default function AnalysisResult() {
  const location = useLocation();
  const navigate = useNavigate();
  const { result, payload } = location.state ?? {};

  if (!result) {
    return (
      <div className="mx-auto max-w-md py-16 text-center">
        <h1 className="font-display text-lg font-semibold text-ink">
          No analysis to show
        </h1>
        <p className="mt-1 text-sm text-ink-soft">
          Start a new symptom analysis to see your results here.
        </p>
        <Button className="mt-6" onClick={() => navigate(ROUTES.SYMPTOM_ANALYSIS)}>
          Start analysis
        </Button>
      </div>
    );
  }

  const {
    possible_conditions: conditions = [],
    severity,
    recommended_action,
    sos_recommended,
    disclaimer,
  } = result;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <button
        onClick={() => navigate(ROUTES.SYMPTOM_ANALYSIS)}
        className="flex items-center gap-1.5 text-sm font-medium text-ink-soft transition-colors hover:text-ink"
      >
        <ArrowLeft className="size-4" /> Back to symptoms
      </button>

      {sos_recommended && (
        <Card className="border-danger/30 bg-danger-light">
          <CardContent className="flex flex-col items-start gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <Siren className="mt-0.5 size-5 shrink-0 text-danger" />
              <p className="text-sm font-medium text-danger">
                The AI recommends emergency attention. If you're in danger, seek
                emergency care immediately.
              </p>
            </div>
            <Button asChild variant="danger" size="sm" className="w-full shrink-0 sm:w-auto">
              <Link to={ROUTES.SOS}>Open SOS</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-bold text-ink sm:text-2xl">
            Your analysis
          </h1>
          {payload?.symptoms && (
            <p className="mt-1 text-sm text-ink-soft">Based on: {payload.symptoms}</p>
          )}
        </div>
        <SeverityBadge severity={severity} />
      </div>

      {conditions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Possible conditions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {conditions.map((condition, i) => (
              <Badge key={i} variant="default" className="text-sm">
                {condition}
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {recommended_action && (
        <Card>
          <CardHeader>
            <CardTitle>Recommended next step</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed text-ink">
            {recommended_action}
          </CardContent>
        </Card>
      )}

      <p className="rounded-[var(--radius-control)] bg-slate-50 p-4 text-xs leading-relaxed text-ink-faint">
        {disclaimer}
      </p>

      <Button
        variant="outline"
        className="w-full"
        onClick={() => navigate(ROUTES.SYMPTOM_ANALYSIS)}
      >
        <RefreshCcw className="size-4" /> Run another analysis
      </Button>
    </div>
  );
}
