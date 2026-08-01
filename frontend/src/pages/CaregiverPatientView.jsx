import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Droplet, Pill, HeartPulse, Phone, Bell, Plus, Check, Trash2, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { useToast } from "@/components/ui/toast";
import {
  getPatientPassport,
  getPatientHistory,
  getPatientReminders,
  createPatientReminder,
  completePatientReminder,
  deletePatientReminder,
} from "@/api/caregivers";
import { ROUTES } from "@/constants/routes";

export default function CaregiverPatientView() {
  const { patientId } = useParams();
  const toast = useToast();

  const [passport, setPassport] = useState(null);
  const [passportError, setPassportError] = useState(null);
  const [history, setHistory] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const [newTitle, setNewTitle] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setPassportError(null);
    try {
      const [historyResult, remindersResult] = await Promise.all([
        getPatientHistory(patientId).catch(() => []),
        getPatientReminders(patientId).catch(() => []),
      ]);
      setHistory(historyResult);
      setReminders(remindersResult);
      try {
        setPassport(await getPatientPassport(patientId));
      } catch (err) {
        setPassportError(err.message || "This person hasn't set up a Health Passport yet.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAddReminder(e) {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setIsAdding(true);
    try {
      await createPatientReminder(patientId, {
        title: newTitle.trim(),
        category: "medication",
        remind_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
        repeat_every_days: null,
      });
      setNewTitle("");
      toast.success("Reminder added");
      load();
    } catch (err) {
      toast.error(err.message || "Couldn't add that reminder.");
    } finally {
      setIsAdding(false);
    }
  }

  async function handleComplete(reminderId) {
    try {
      await completePatientReminder(patientId, reminderId);
      load();
    } catch (err) {
      toast.error(err.message || "Couldn't update that reminder.");
    }
  }

  async function handleDelete(reminderId) {
    try {
      await deletePatientReminder(patientId, reminderId);
      setReminders((prev) => prev.filter((r) => r.id !== reminderId));
    } catch (err) {
      toast.error(err.message || "Couldn't delete that reminder.");
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        to={ROUTES.CAREGIVERS}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
      >
        <ArrowLeft className="size-3.5" /> Back to Caregivers
      </Link>

      <div>
        <h1 className="font-display text-2xl font-medium text-ink">
          {passport?.name || "Patient"}
        </h1>
        <p className="mt-1 text-sm text-ink-soft">Read-only view - you're viewing as a caregiver.</p>
      </div>

      {passportError ? (
        <Card>
          <CardContent className="p-6 text-sm text-ink-soft">{passportError}</CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Health Passport</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <div className="flex items-center gap-2 text-sm">
              <Droplet className="size-4 text-danger" />
              Blood group: <span className="font-mono">{passport.blood_group}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Phone className="size-4 text-primary" />
              {passport.emergency_contact_name}: {passport.emergency_contact_phone}
            </div>
            {passport.allergies && (
              <div className="flex items-center gap-2 text-sm sm:col-span-2">
                <HeartPulse className="size-4 text-warning" /> Allergies: {passport.allergies}
              </div>
            )}
            {passport.medications && (
              <div className="flex items-center gap-2 text-sm sm:col-span-2">
                <Pill className="size-4 text-primary" /> Medications: {passport.medications}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Bell className="size-4 text-primary" /> Reminders
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form onSubmit={handleAddReminder} className="flex gap-2">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Take morning medication"
              className="flex-1 rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 text-sm"
            />
            <Button type="submit" size="sm" disabled={isAdding || !newTitle.trim()}>
              <Plus className="size-3.5" /> Add
            </Button>
          </form>

          {reminders.length === 0 ? (
            <p className="text-sm text-ink-faint">No active reminders.</p>
          ) : (
            reminders.map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between border-t border-border pt-3 first:border-t-0 first:pt-0"
              >
                <div>
                  <p className="text-sm font-medium text-ink">{r.title}</p>
                  <p className="text-xs text-ink-faint">
                    {new Date(r.remind_at).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => handleComplete(r.id)}>
                    <Check className="size-3.5" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => handleDelete(r.id)}>
                    <Trash2 className="size-3.5 text-danger" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Clock className="size-4 text-primary" /> Recent analyses
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {history.length === 0 ? (
            <p className="text-sm text-ink-faint">No saved analyses yet.</p>
          ) : (
            history.slice(0, 10).map((h) => (
              <div key={h.id} className="border-t border-border pt-3 first:border-t-0 first:pt-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-ink">{h.symptoms}</p>
                  <Badge
                    variant={
                      h.severity === "EMERGENCY" || h.severity === "HIGH" ? "danger" : "default"
                    }
                  >
                    {h.severity}
                  </Badge>
                </div>
                <p className="mt-0.5 text-xs text-ink-faint">
                  {new Date(h.created_at).toLocaleDateString()}
                </p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
