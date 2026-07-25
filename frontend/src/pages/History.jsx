import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Clock, TrendingUp, AlertCircle, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { SeverityBadge } from "@/components/symptom/SeverityBadge";
import { getHistory, getTrends } from "@/api/history";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";

function formatDate(isoString) {
  try {
    return new Date(isoString).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

export default function History() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [entries, setEntries] = useState([]);
  const [trends, setTrends] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const load = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    setLoadError(null);
    try {
      // Independent requests - a trend-detection hiccup shouldn't block
      // the history list itself from showing, and vice versa.
      const [historyResult, trendsResult] = await Promise.allSettled([
        getHistory(user.userId, 50),
        getTrends(user.userId),
      ]);
      if (historyResult.status === "fulfilled") {
        setEntries(historyResult.value);
      } else {
        setLoadError(historyResult.reason);
      }
      if (trendsResult.status === "fulfilled") {
        setTrends(trendsResult.value);
      }
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-display text-xl font-bold text-ink sm:text-2xl">
          Your analysis history
        </h1>
        <p className="mt-1 text-sm text-ink-soft">
          Past symptom checks saved while you were logged in.
        </p>
      </div>

      {trends.length > 0 && (
        <Card className="border-primary/20 bg-primary-light/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="size-4 text-primary" /> Recurring symptoms
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {trends.map((t) => (
              <Badge key={t.keyword} variant="default" className="text-xs">
                "{t.keyword}" · {t.occurrences}x in {t.window_days} days
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {isLoading && (
        <div className="flex h-40 items-center justify-center text-ink-faint">
          <Spinner size={22} className="mr-2" /> Loading your history...
        </div>
      )}

      {!isLoading && loadError && (
        <div className="flex items-start gap-2 rounded-[var(--radius-control)] bg-danger-light px-4 py-3 text-sm text-danger">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{loadError.message}</span>
        </div>
      )}

      {!isLoading && !loadError && entries.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-[var(--radius-card)] border border-dashed border-border py-16 text-center">
          <Clock className="size-8 text-ink-faint" />
          <p className="text-sm text-ink-soft">No analyses saved yet.</p>
          <Button onClick={() => navigate(ROUTES.SYMPTOM_ANALYSIS)} size="sm">
            <Sparkles className="size-4" /> Run your first analysis
          </Button>
        </div>
      )}

      {!isLoading && entries.length > 0 && (
        <div className="space-y-3">
          {entries.map((entry) => (
            <Card key={entry.id}>
              <CardContent className="flex flex-col gap-2 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-ink">{entry.symptoms}</p>
                    <p className="mt-0.5 text-xs text-ink-faint">
                      {formatDate(entry.created_at)} · {entry.duration}
                    </p>
                  </div>
                  <SeverityBadge severity={entry.severity} />
                </div>
                {entry.possible_conditions?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {entry.possible_conditions.map((c, i) => (
                      <Badge key={i} variant="neutral" className="text-xs">
                        {c}
                      </Badge>
                    ))}
                  </div>
                )}
                {entry.feedback !== null && (
                  <p className="text-xs text-ink-faint">
                    You marked this as {entry.feedback ? "helpful" : "not helpful"}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
