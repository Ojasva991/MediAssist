import { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Clock, TrendingUp, AlertCircle, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { SeverityBadge } from "@/components/symptom/SeverityBadge";
import { getHistory, getTrends } from "@/api/history";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { computeSeverityTrend, computeTopConditions } from "@/lib/insights";
import { SeverityTrendChart } from "@/components/history/SeverityTrendChart";
import { TopConditionsChart } from "@/components/history/TopConditionsChart";

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

function HistoryEntrySkeleton() {
  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-28" />
          </div>
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}

export default function History() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [entries, setEntries] = useState([]);
  const [trends, setTrends] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      // Independent requests - a trend-detection hiccup shouldn't block
      // the history list itself from rendering, and vice versa.
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
  }, [user.userId]);

  useEffect(() => {
    load();
  }, [load]);

  const severityTrend = useMemo(() => computeSeverityTrend(entries), [entries]);
  const topConditions = useMemo(() => computeTopConditions(entries, { limit: 5 }), [entries]);

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
        <Card className="border-primary/20 bg-primary-light">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="size-4 text-primary" /> Recurring symptoms
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {trends.map((t) => (
              <Badge key={t.keyword} variant="default" className="font-mono text-xs">
                "{t.keyword}" · {t.occurrences}x in {t.window_days}d
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {!isLoading && !loadError && severityTrend.length >= 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="size-4 text-primary" /> Severity over time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SeverityTrendChart data={severityTrend} />
          </CardContent>
        </Card>
      )}

      {!isLoading && !loadError && topConditions.items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Sparkles className="size-4 text-primary" />
              Most common possible conditions
              <span className="ml-auto font-mono text-xs font-normal text-ink-faint">
                {topConditions.scope === "this-month" ? "this month" : "all time"}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TopConditionsChart items={topConditions.items} />
          </CardContent>
        </Card>
      )}

      {isLoading && (
        <div className="space-y-3">
          <HistoryEntrySkeleton />
          <HistoryEntrySkeleton />
          <HistoryEntrySkeleton />
        </div>
      )}

      {!isLoading && loadError && (
        <div className="flex items-start gap-2 rounded-[var(--radius-control)] bg-danger-light px-4 py-3 text-sm text-danger">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{loadError.message}</span>
        </div>
      )}

      {!isLoading && !loadError && entries.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-[var(--radius-card)] border border-dashed border-border bg-surface py-16 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-primary-light text-primary-dark">
            <Clock className="size-6" />
          </span>
          <div>
            <p className="font-display font-semibold text-ink">No analyses saved yet</p>
            <p className="mt-1 text-sm text-ink-soft">
              Run a symptom check while logged in and it'll show up here.
            </p>
          </div>
          <Button className="mt-2" onClick={() => navigate(ROUTES.SYMPTOM_ANALYSIS)} size="sm">
            <Sparkles className="size-4" /> Run your first analysis
          </Button>
        </div>
      )}

      {!isLoading && entries.length > 0 && (
        <div className="space-y-3">
          {entries.map((entry) => (
            <Card key={entry.id}>
              <CardContent className="space-y-3 p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-ink">{entry.symptoms}</p>
                    <p className="mt-1 font-mono text-xs text-ink-faint">
                      {formatDate(entry.created_at)} · {entry.duration}
                    </p>
                  </div>
                  <SeverityBadge severity={entry.severity} />
                </div>

                {entry.possible_conditions?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 border-t border-border pt-3">
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
