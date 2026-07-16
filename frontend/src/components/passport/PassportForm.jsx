import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { AlertCircle } from "lucide-react";

const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "UNKNOWN"];

const EMPTY_FORM = {
  name: "",
  age: "",
  blood_group: "UNKNOWN",
  allergies: "",
  medications: "",
  chronic_diseases: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
};

export function PassportForm({ initialValue, onSubmit, onCancel, isSaving, error }) {
  const [form, setForm] = useState({ ...EMPTY_FORM, ...initialValue });
  const [formErrors, setFormErrors] = useState({});

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function validate() {
    const errs = {};
    if (!form.name.trim()) errs.name = "Full name is required.";
    if (form.age === "" || Number(form.age) < 0 || Number(form.age) > 120) {
      errs.age = "Enter a valid age (0-120).";
    }
    if (!form.emergency_contact_name.trim()) {
      errs.emergency_contact_name = "Emergency contact name is required.";
    }
    const digits = (form.emergency_contact_phone.match(/\d/g) || []).length;
    if (digits < 7) errs.emergency_contact_phone = "Enter a phone number with at least 7 digits.";
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({
      ...form,
      age: Number(form.age),
      allergies: form.allergies.trim() || undefined,
      medications: form.medications.trim() || undefined,
      chronic_diseases: form.chronic_diseases.trim() || undefined,
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{initialValue ? "Edit health passport" : "Create your health passport"}</CardTitle>
        <CardDescription>
          This information can be shared instantly during an emergency via the SOS screen.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                placeholder="Priya Sharma"
              />
              {formErrors.name && <p className="text-xs text-danger">{formErrors.name}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="age">Age</Label>
              <Input
                id="age"
                type="number"
                min="0"
                max="120"
                value={form.age}
                onChange={(e) => update("age", e.target.value)}
              />
              {formErrors.age && <p className="text-xs text-danger">{formErrors.age}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="blood_group">Blood group</Label>
              <Select value={form.blood_group} onValueChange={(v) => update("blood_group", v)}>
                <SelectTrigger id="blood_group">
                  <SelectValue placeholder="Select" />
                </SelectTrigger>
                <SelectContent>
                  {BLOOD_GROUPS.map((bg) => (
                    <SelectItem key={bg} value={bg}>
                      {bg === "UNKNOWN" ? "Unknown" : bg}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="ec_name">Emergency contact name</Label>
              <Input
                id="ec_name"
                value={form.emergency_contact_name}
                onChange={(e) => update("emergency_contact_name", e.target.value)}
                placeholder="Raj Sharma"
              />
              {formErrors.emergency_contact_name && (
                <p className="text-xs text-danger">{formErrors.emergency_contact_name}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="ec_phone">Emergency contact phone</Label>
              <Input
                id="ec_phone"
                type="tel"
                value={form.emergency_contact_phone}
                onChange={(e) => update("emergency_contact_phone", e.target.value)}
                placeholder="+91-9876543210"
              />
              {formErrors.emergency_contact_phone && (
                <p className="text-xs text-danger">{formErrors.emergency_contact_phone}</p>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="allergies">Allergies</Label>
            <Textarea
              id="allergies"
              placeholder="e.g. Penicillin, Peanuts"
              value={form.allergies}
              onChange={(e) => update("allergies", e.target.value)}
              maxLength={500}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="chronic_diseases">Chronic conditions</Label>
            <Textarea
              id="chronic_diseases"
              placeholder="e.g. Asthma, Hypertension"
              value={form.chronic_diseases}
              onChange={(e) => update("chronic_diseases", e.target.value)}
              maxLength={500}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="medications">Current medications</Label>
            <Textarea
              id="medications"
              placeholder="e.g. Metformin 500mg"
              value={form.medications}
              onChange={(e) => update("medications", e.target.value)}
              maxLength={500}
            />
          </div>

          {error && (
            <div className="flex items-start gap-2 rounded-[var(--radius-control)] bg-danger-light px-4 py-3 text-sm text-danger">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <span>{error.message}</span>
            </div>
          )}

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
                Cancel
              </Button>
            )}
            <Button type="submit" disabled={isSaving}>
              {isSaving ? (
                <>
                  <Spinner size={16} /> Saving...
                </>
              ) : (
                "Save health passport"
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
