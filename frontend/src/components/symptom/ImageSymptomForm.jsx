import { useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Camera, Upload, X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { useApi } from "@/hooks/useApi";
import { analyzeImage } from "@/api/analysis";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/constants/routes";

const MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export function ImageSymptomForm() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { run, isLoading, error } = useApi(analyzeImage);
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState("");
  const [fileError, setFileError] = useState(null);

  function handleFileChange(e) {
    const selected = e.target.files?.[0];
    if (!selected) return;

    if (!ALLOWED_TYPES.includes(selected.type)) {
      setFileError("Please choose a JPEG, PNG, or WEBP image.");
      return;
    }
    if (selected.size > MAX_IMAGE_SIZE_BYTES) {
      setFileError("Image is too large. Maximum size is 8MB.");
      return;
    }

    setFileError(null);
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
  }

  function clearFile() {
    setFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setFileError("Choose a photo to analyze.");
      return;
    }
    try {
      const result = await run({
        image: file,
        symptoms: description.trim() || undefined,
        duration: duration.trim() || undefined,
      });
      navigate(ROUTES.ANALYSIS_RESULT, {
        state: { result, payload: { symptoms: description.trim() || "[Photo-based analysis]" } },
      });
    } catch {
      // error state already surfaced below via `error`
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      <div className="space-y-1.5">
        <Label>Photo</Label>
        {!previewUrl ? (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex w-full flex-col items-center gap-2 rounded-[var(--radius-control)] border-2 border-dashed border-border bg-[var(--color-mist)] px-4 py-10 text-center transition-colors hover:border-primary hover:bg-primary-light"
          >
            <Camera className="size-6 text-ink-faint" />
            <p className="text-sm font-medium text-ink">Choose a photo</p>
            <p className="text-xs text-ink-faint">JPEG, PNG, or WEBP · up to 8MB</p>
          </button>
        ) : (
          <div className="relative overflow-hidden rounded-[var(--radius-control)] border border-border">
            <img src={previewUrl} alt="Selected symptom photo" className="max-h-64 w-full object-contain bg-[var(--color-mist)]" />
            <button
              type="button"
              onClick={clearFile}
              className="absolute right-2 top-2 flex size-7 items-center justify-center rounded-full bg-ink/70 text-white hover:bg-ink"
              aria-label="Remove photo"
            >
              <X className="size-4" />
            </button>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileChange}
          className="hidden"
        />
        {fileError && (
          <p className="flex items-center gap-1.5 text-xs text-danger">
            <AlertCircle className="size-3.5" /> {fileError}
          </p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="image-description">Anything you'd like to add? (optional)</Label>
        <Textarea
          id="image-description"
          placeholder="e.g. It's been itchy and slightly warm to the touch"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={1000}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="image-duration">How long has this been present? (optional)</Label>
        <Input
          id="image-duration"
          placeholder="e.g. 3 days"
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
        />
      </div>

      {!user && (
        <p className="text-xs text-ink-faint">
          <Link to={ROUTES.PASSPORT} className="font-medium text-primary hover:underline">
            Sign in and save a Health Passport
          </Link>{" "}
          for more personalized results (age, gender, and existing conditions factored in
          automatically).
        </p>
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
            <Spinner size={16} /> Analyzing your photo...
          </>
        ) : (
          <>
            <Upload className="size-4" /> Analyze photo
          </>
        )}
      </Button>

      <p className="text-center text-xs text-ink-faint">
        Photo-based analysis is significantly less reliable than an in-person exam and cannot
        rule out serious conditions. Vaeda provides informational guidance only.
      </p>
    </form>
  );
}
