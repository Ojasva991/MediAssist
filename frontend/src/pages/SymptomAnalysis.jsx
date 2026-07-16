import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useApi } from "@/hooks/useApi";
import { analyzeSymptoms } from "@/api/analysis";
import { ROUTES } from "@/constants/routes";

export default function SymptomAnalysis() {
  const navigate = useNavigate();
  const { run, isLoading, error } = useApi(analyzeSymptoms);

  const [symptoms, setSymptoms] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [duration, setDuration] = useState("");
  const [existingConditions, setExistingConditions] = useState("");
  const [formErrors, setFormErrors] = useState({});

  function validate() {
    const errs = {};
    if (symptoms.trim().length < 3) errs.symptoms = "Describe your symptoms (at least 3 characters).";
    if (!age || Number(age) < 0 || Number(age) > 120) errs.age = "Enter a valid age (0-120).";
    if (!gender) errs.gender = "Select a gender.";
    if (!duration.trim()) errs.duration = "Let us know how long this has lasted.";
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;

    const payload = {
      age: Number(age),
      gender,
      symptoms: symptoms.trim(),
      duration: duration.trim(),
      ...(existingConditions.trim() && { existing_conditions: existingConditions.trim() }),
    };

    try {
      const result = await run(payload);
      navigate(ROUTES.ANALYSIS_RESULT, { state: { result, payload } });
    } catch {
      // error state already surfaced below via `error`
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-xl font-bold text-ink sm:text-2xl">
          Tell us what's going on
        </h1>
        <p className="mt-1 text-sm text-ink-soft">
          The more detail you give, the more useful your analysis will be. This isn't a
          diagnosis — it's a starting point.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Symptom details</CardTitle>
          <CardDescription>All fields except existing conditions are required.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="symptoms">Symptoms</Label>
              <Textarea
                id="symptoms"
                placeholder="e.g. Chest pain and sweating"
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                maxLength={1000}
              />
              {formErrors.symptoms && (
                <p className="flex items-center gap-1.5 text-xs text-danger">
                  <AlertCircle className="size-3.5" /> {formErrors.symptoms}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label htmlFor="age">Age</Label>
                <Input
                  id="age"
                  type="number"
                  min="0"
                  max="120"
                  placeholder="28"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                />
                {formErrors.age && <p className="text-xs text-danger">{formErrors.age}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="gender">Gender</Label>
                <Select value={gender} onValueChange={setGender}>
                  <SelectTrigger id="gender">
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Female">Female</SelectItem>
                    <SelectItem value="Male">Male</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
                {formErrors.gender && <p className="text-xs text-danger">{formErrors.gender}</p>}
              </div>

              <div className="col-span-2 space-y-1.5 sm:col-span-1">
                <Label htmlFor="duration">Duration</Label>
                <Input
                  id="duration"
                  placeholder="e.g. 3 days"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                />
                {formErrors.duration && <p className="text-xs text-danger">{formErrors.duration}</p>}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="existing_conditions">Existing conditions (optional)</Label>
              <Input
                id="existing_conditions"
                placeholder="e.g. diabetes, asthma"
                value={existingConditions}
                onChange={(e) => setExistingConditions(e.target.value)}
                maxLength={500}
              />
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-[var(--radius-control)] bg-danger-light px-4 py-3 text-sm text-danger">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{error.message}</span>
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Spinner size={16} /> Analyzing your symptoms...
                </>
              ) : (
                <>
                  <Sparkles className="size-4" /> Get AI analysis
                </>
              )}
            </Button>

            <p className="text-center text-xs text-ink-faint">
              MediAssist AI provides informational guidance only and is not a
              substitute for professional medical advice.
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
