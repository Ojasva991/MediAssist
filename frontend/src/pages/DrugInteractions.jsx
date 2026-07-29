import { useState } from "react";
import { Pill, X, Plus, AlertTriangle, Info, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useApi } from "@/hooks/useApi";
import { checkDrugInteractions } from "@/api/drugInteractions";

export default function DrugInteractions() {
  const [drugs, setDrugs] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const { run, isLoading, error } = useApi(checkDrugInteractions);
  const [result, setResult] = useState(null);

  function addDrug() {
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    if (drugs.some((d) => d.toLowerCase() === trimmed.toLowerCase())) {
      setInputValue("");
      return;
    }
    setDrugs((prev) => [...prev, trimmed]);
    setInputValue("");
  }

  function removeDrug(name) {
    setDrugs((prev) => prev.filter((d) => d !== name));
    setResult(null);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addDrug();
    }
  }

  async function handleCheck() {
    if (drugs.length < 2) return;
    try {
      const data = await run(drugs);
      setResult(data);
    } catch {
      // error surfaced below via `error`
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-medium text-ink">Drug Interaction Checker</h1>
        <p className="mt-1 text-sm text-ink-soft">
          Check a list of medications against known interactions.
        </p>
      </div>

      {/* Honest scope note, not buried - see app/interactions/corpus.py */}
      <div className="flex items-start gap-2 rounded-[var(--radius-card)] border border-border bg-primary-light p-3 text-xs text-ink-soft">
        <Info className="mt-0.5 size-3.5 shrink-0 text-primary" />
        <p>
          This checks against a small, hand-picked list of well-known interactions - it is{" "}
          <strong>not</strong> a comprehensive drug database. A combination not flagged here has
          not been checked against a complete reference, and does not mean it's safe. Always ask
          a pharmacist or doctor.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Your medications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="e.g. Warfarin"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <Button type="button" variant="outline" onClick={addDrug}>
              <Plus className="size-4" /> Add
            </Button>
          </div>

          {drugs.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {drugs.map((d) => (
                <Badge key={d} variant="neutral" className="gap-1.5 pr-1.5">
                  <Pill className="size-3" /> {d}
                  <button
                    type="button"
                    onClick={() => removeDrug(d)}
                    className="ml-1 rounded-full p-0.5 hover:bg-ink/10"
                    aria-label={`Remove ${d}`}
                  >
                    <X className="size-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}

          {drugs.length === 1 && (
            <p className="text-xs text-ink-faint">Add at least one more medication to check.</p>
          )}

          {error && <p className="text-sm text-danger">{error.message}</p>}

          <Button
            className="w-full"
            disabled={drugs.length < 2 || isLoading}
            onClick={handleCheck}
          >
            {isLoading ? (
              <>
                <Spinner size={16} /> Checking...
              </>
            ) : (
              "Check interactions"
            )}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {result.matches.length === 0 ? (
              <p className="text-sm text-ink-soft">
                No interactions found in our reference list for these medications. As above, this
                doesn't mean the combination is safe - it means it's not in this limited list.
              </p>
            ) : (
              <div className="space-y-3">
                {result.matches.map((m, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-3 rounded-[var(--radius-control)] p-3 ${
                      m.severity === "MAJOR" ? "bg-danger-light" : "bg-warning-light"
                    }`}
                  >
                    <AlertTriangle
                      className={`mt-0.5 size-4 shrink-0 ${
                        m.severity === "MAJOR" ? "text-danger" : "text-warning"
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-ink">
                          {m.drug_a} + {m.drug_b}
                        </p>
                        <Badge variant={m.severity === "MAJOR" ? "danger" : "warning"}>
                          {m.severity === "MAJOR" ? "Major" : "Moderate"}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-ink-soft">{m.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {result.unrecognized_drugs.length > 0 && (
              <div className="flex items-start gap-2 rounded-[var(--radius-control)] bg-[var(--color-mist)] p-3 text-xs text-ink-soft">
                <ShieldAlert className="mt-0.5 size-3.5 shrink-0 text-ink-faint" />
                <p>
                  Not recognized in our reference list (not checked, not confirmed safe):{" "}
                  <span className="font-medium">{result.unrecognized_drugs.join(", ")}</span>
                </p>
              </div>
            )}

            <p className="text-xs text-ink-faint">{result.disclaimer}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
