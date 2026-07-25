import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { ArrowLeft, RefreshCcw, Siren, ListChecks, BookOpen, ThumbsUp, ThumbsDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SeverityBadge } from "@/components/symptom/SeverityBadge";
import { useToast } from "@/components/ui/toast";
import { submitAnalysisFeedback } from "@/api/history";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";

export default function AnalysisResult() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();
  const { result, payload } = location.state ?? {};

  // Local-only state for which button is highlighted/disabled while a
  // feedback submission is in flight - not persisted here, since the
  // saved value lives on the backend and this page doesn't re-fetch it.
  const [feedbackGiven, setFeedbackGiven] = useState(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

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
    rule_engine: ruleEngine,
    retrieved_guidance: retrievedGuidance = [],
    llm_severity: llmSeverity,
    history_id: historyId,
  } = result;

  const severityWasEscalated = llmSeverity && llmSeverity !== severity;

  async function handleFeedback(isHelpful) {
    if (!user || !historyId || isSubmittingFeedback) return;
    setIsSubmittingFeedback(true);
    try {
      await submitAnalysisFeedback(user.userId, historyId, isHelpful);
      setFeedbackGiven(isHelpful);
      toast.success("Thanks for the feedback");
    } catch (err) {
      toast.error(err.message || "Could not submit feedback");
    } finally {
      setIsSubmittingFeedback(false);
    }
  }

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

      {ruleEngine?.fired_rules?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <ListChecks className="size-4 text-ink-soft" /> Why this urgency level
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {severityWasEscalated && (
              <p className="rounded-[var(--radius-control)] bg-warning-light px-3 py-2 text-xs text-warning">
                Our safety check raised this from the AI's initial read of{" "}
                <strong>{llmSeverity}</strong> to <strong>{severity}</strong>, based on the
                reasons below.
              </p>
            )}
            <ul className="space-y-2 text-sm text-ink-soft">
              {ruleEngine.fired_rules.map((rule, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 size-1 shrink-0 rounded-full bg-ink-faint" />
                  {rule}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {retrievedGuidance.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <BookOpen className="size-4 text-ink-soft" /> Reference guidance used
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {retrievedGuidance.map((g, i) => (
              <Badge key={i} variant="neutral" className="text-xs">
                {g.topic}
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {historyId && (
        <Card>
          <CardContent className="flex items-center justify-between gap-3 p-4">
            <p className="text-sm text-ink-soft">Was this analysis helpful?</p>
            <div className="flex gap-2">
              <Button
                variant={feedbackGiven === true ? "default" : "outline"}
                size="sm"
                disabled={isSubmittingFeedback}
                onClick={() => handleFeedback(true)}
                aria-label="This analysis was helpful"
              >
                <ThumbsUp className="size-4" />
              </Button>
              <Button
                variant={feedbackGiven === false ? "danger" : "outline"}
                size="sm"
                disabled={isSubmittingFeedback}
                onClick={() => handleFeedback(false)}
                aria-label="This analysis was not helpful"
              >
                <ThumbsDown className="size-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <p className="rounded-[var(--radius-control)] bg-[var(--color-mist)] p-4 text-xs leading-relaxed text-ink-faint">
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
