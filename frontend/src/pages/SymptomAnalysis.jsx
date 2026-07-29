import { useState, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Sparkles, AlertCircle, UserCheck, Pencil, Mic, MicOff, MessageSquareText, Camera } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useApi } from "@/hooks/useApi";
import { useVoiceInput } from "@/hooks/useVoiceInput";
import { analyzeSymptoms } from "@/api/analysis";
import { getPassport } from "@/api/passport";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";
import { ImageSymptomForm } from "@/components/symptom/ImageSymptomForm";

export default function SymptomAnalysis() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { run, isLoading, error } = useApi(analyzeSymptoms);

  // "text" | "photo" - which input mode is showing. Photo mode is a
  // fully separate form (see ImageSymptomForm) since it hits a
  // different endpoint (POST /analyze/image) with different required
  // fields (nothing is strictly required there but the photo itself).
  const [mode, setMode] = useState("text");

  // Saved Health Passport for the logged-in user, if any. Once this is
  // loaded, age/gender/existing conditions come from it automatically
  // instead of being asked for on every symptom check.
  const [passport, setPassport] = useState(null);
  const [isLoadingPassport, setIsLoadingPassport] = useState(!!user);

  const [symptoms, setSymptoms] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [duration, setDuration] = useState("");
  const [existingConditions, setExistingConditions] = useState("");
  const [formErrors, setFormErrors] = useState({});

  const voiceInput = useVoiceInput({
    onResult: (transcript) =>
      setSymptoms((prev) => (prev.trim() ? `${prev.trim()} ${transcript}` : transcript)),
  });

  const fetchPassport = useCallback(async () => {
    if (!user) {
      setIsLoadingPassport(false);
      return;
    }
    setIsLoadingPassport(true);
    try {
      const data = await getPassport(user.userId);
      setPassport(data);
    } catch {
      // 404 just means no passport yet - that's a normal state, not an
      // error. Anything else, fall back to asking inline rather than
      // blocking the page.
      setPassport(null);
    } finally {
      setIsLoadingPassport(false);
    }
  }, [user]);

  useEffect(() => {
    fetchPassport();
  }, [fetchPassport]);

  // True once we know age/gender will come from the saved passport, so
  // those fields don't need to be shown or collected in this form at all.
  const usingSavedProfile = !!(passport && passport.age && passport.gender);

  function validate() {
    const errs = {};
    if (symptoms.trim().length < 3) errs.symptoms = "Describe your symptoms (at least 3 characters).";
    if (!usingSavedProfile) {
      if (!age || Number(age) < 0 || Number(age) > 120) errs.age = "Enter a valid age (0-120).";
      if (!gender) errs.gender = "Select a gender.";
    }
    if (!duration.trim()) errs.duration = "Let us know how long this has lasted.";
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;

    const payload = {
      symptoms: symptoms.trim(),
      duration: duration.trim(),
      // When using the saved passport, age/gender/existing_conditions are
      // deliberately left out - the backend fills them in from the
      // caller's Health Passport. Otherwise (no passport, or logged out)
      // they're collected inline as before.
      ...(!usingSavedProfile && {
        age: Number(age),
        gender,
        ...(existingConditions.trim() && { existing_conditions: existingConditions.trim() }),
      }),
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
          <div className="flex items-center justify-between gap-3">
            <CardTitle>{mode === "text" ? "Symptom details" : "Photo analysis"}</CardTitle>
            <div className="flex overflow-hidden rounded-md border border-border">
              <button
                type="button"
                onClick={() => setMode("text")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium ${
                  mode === "text" ? "bg-primary-light text-primary-dark" : "text-ink-soft"
                }`}
              >
                <MessageSquareText className="size-3.5" /> Describe
              </button>
              <button
                type="button"
                onClick={() => setMode("photo")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium ${
                  mode === "photo" ? "bg-primary-light text-primary-dark" : "text-ink-soft"
                }`}
              >
                <Camera className="size-3.5" /> Photo
              </button>
            </div>
          </div>
          <CardDescription>
            {mode === "photo"
              ? "Upload a photo of a visible symptom - a rash, wound, swelling, or similar."
              : usingSavedProfile
                ? "Just describe what's going on — your profile details are already saved."
                : "All fields except existing conditions are required."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {mode === "photo" ? (
            <ImageSymptomForm />
          ) : isLoadingPassport ? (
            <div className="flex items-center justify-center py-10 text-ink-faint">
              <Spinner size={20} />
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6" noValidate>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="symptoms">Symptoms</Label>
                  {voiceInput.isSupported && (
                    <button
                      type="button"
                      onClick={voiceInput.isListening ? voiceInput.stop : voiceInput.start}
                      className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium transition-colors ${
                        voiceInput.isListening
                          ? "bg-danger-light text-danger"
                          : "text-primary hover:bg-primary-light"
                      }`}
                    >
                      {voiceInput.isListening ? (
                        <>
                          <MicOff className="size-3.5" /> Listening…
                        </>
                      ) : (
                        <>
                          <Mic className="size-3.5" /> Speak
                        </>
                      )}
                    </button>
                  )}
                </div>
                <Textarea
                  id="symptoms"
                  placeholder="e.g. Chest pain and sweating"
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  maxLength={1000}
                />
                <p className="text-xs text-ink-faint">
                  You can describe your symptoms in any language and the AI will reply in kind -
                  but our automatic red-flag safety checks currently only recognize English
                  wording. If you're writing in another language and anything feels urgent,
                  please still use the SOS page or contact emergency services directly rather
                  than relying on this alone.
                </p>
                {voiceInput.error && <p className="text-xs text-danger">{voiceInput.error}</p>}
                {formErrors.symptoms && (
                  <p className="flex items-center gap-1.5 text-xs text-danger">
                    <AlertCircle className="size-3.5" /> {formErrors.symptoms}
                  </p>
                )}
              </div>

              {usingSavedProfile ? (
                <div className="flex items-start justify-between gap-3 rounded-[var(--radius-control)] border border-border bg-[var(--color-mist)] px-4 py-3">
                  <div className="flex items-start gap-2.5">
                    <UserCheck className="mt-0.5 size-4 shrink-0 text-primary" />
                    <div className="text-sm text-ink">
                      <p className="font-medium">Using your saved profile</p>
                      <p className="mt-0.5 text-ink-soft">
                        Age {passport.age} · {passport.gender}
                        {passport.chronic_diseases ? ` · ${passport.chronic_diseases}` : ""}
                      </p>
                    </div>
                  </div>
                  <Link
                    to={ROUTES.PASSPORT}
                    className="flex shrink-0 items-center gap-1 text-xs font-medium text-primary hover:underline"
                  >
                    <Pencil className="size-3" /> Edit
                  </Link>
                </div>
              ) : (
                <>
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

                  {user && !passport && (
                    <p className="text-xs text-ink-faint">
                      Tip: save your age, gender and conditions once in your{" "}
                      <Link to={ROUTES.PASSPORT} className="font-medium text-primary hover:underline">
                        Health Passport
                      </Link>{" "}
                      so you don't have to enter them every time.
                    </p>
                  )}
                </>
              )}

              {usingSavedProfile && (
                <div className="space-y-1.5">
                  <Label htmlFor="duration">Duration</Label>
                  <Input
                    id="duration"
                    placeholder="e.g. 3 days"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                  />
                  {formErrors.duration && <p className="text-xs text-danger">{formErrors.duration}</p>}
                </div>
              )}

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
                Vaeda provides informational guidance only and is not a
                substitute for professional medical advice.
              </p>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
