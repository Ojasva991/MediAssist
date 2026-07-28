import { useState, useEffect, useCallback } from "react";
import { Bell, Plus, Pill, Stethoscope, CalendarClock, Check, Trash2, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import { getReminders, createReminder, completeReminder, deleteReminder } from "@/api/reminders";

const CATEGORIES = [
  { value: "medication", label: "Medication", icon: Pill },
  { value: "follow_up", label: "Follow-up", icon: Stethoscope },
  { value: "other", label: "Other", icon: CalendarClock },
];
const CATEGORY_MAP = Object.fromEntries(CATEGORIES.map((c) => [c.value, c]));

const REPEAT_OPTIONS = [
  { value: "none", label: "One-time" },
  { value: "1", label: "Daily" },
  { value: "7", label: "Weekly" },
];

function formatDateTime(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function isOverdue(iso) {
  return new Date(iso).getTime() < Date.now();
}

// Local datetime input helper - <input type="datetime-local"> works in
// the browser's local time with no timezone suffix, so this converts
// to/from that format without pulling in a date library for one field.
function toDatetimeLocalValue(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

export default function Reminders() {
  const toast = useToast();

  const [reminders, setReminders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [category, setCategory] = useState("medication");
  const [remindAt, setRemindAt] = useState(() => {
    const inOneHour = new Date(Date.now() + 60 * 60 * 1000);
    return toDatetimeLocalValue(inOneHour);
  });
  const [repeat, setRepeat] = useState("none");
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState(null);

  const [completingId, setCompletingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // Notification permission is requested once, lazily, only when the
  // person opts in via the toggle below - never on page load unasked.
  const [notifyEnabled, setNotifyEnabled] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await getReminders();
      setReminders(data);
    } catch (err) {
      setLoadError(err.message || "Couldn't load your reminders.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // In-app "while the tab is open" notifications only - see the scope
  // note in app/models/reminder.py. This is a foreground poll, NOT a
  // background push subscription; it stops the moment the tab closes.
  // That's a real, deliberate limitation, not a placeholder for
  // something more - the UI copy below says so explicitly.
  useEffect(() => {
    if (!notifyEnabled) return;
    const notified = new Set();
    const interval = setInterval(() => {
      reminders.forEach((r) => {
        if (!r.is_active || notified.has(r.id)) return;
        if (new Date(r.remind_at).getTime() <= Date.now()) {
          notified.add(r.id);
          if (Notification.permission === "granted") {
            new Notification(r.title, {
              body: r.notes || "Reminder from Vaeda",
              tag: `reminder-${r.id}`,
            });
          }
        }
      });
    }, 30000);
    return () => clearInterval(interval);
  }, [notifyEnabled, reminders]);

  async function handleToggleNotify() {
    if (!notifyEnabled) {
      if (!("Notification" in window)) {
        toast.error("This browser doesn't support notifications.");
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        toast.error("Notification permission wasn't granted.");
        return;
      }
    }
    setNotifyEnabled((v) => !v);
  }

  function openDialog() {
    setTitle("");
    setNotes("");
    setCategory("medication");
    setRemindAt(toDatetimeLocalValue(new Date(Date.now() + 60 * 60 * 1000)));
    setRepeat("none");
    setFormError(null);
    setDialogOpen(true);
  }

  async function handleCreate() {
    if (!title.trim()) {
      setFormError("Give this reminder a title.");
      return;
    }
    setIsSaving(true);
    setFormError(null);
    try {
      await createReminder({
        title: title.trim(),
        notes: notes.trim() || null,
        category,
        remindAt: new Date(remindAt).toISOString(),
        repeatEveryDays: repeat === "none" ? null : Number(repeat),
      });
      toast.success("Reminder created");
      setDialogOpen(false);
      load();
    } catch (err) {
      setFormError(err.message || "Couldn't create this reminder.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleComplete(id) {
    setCompletingId(id);
    try {
      await completeReminder(id);
      toast.success("Marked done");
      load();
    } catch (err) {
      toast.error(err.message || "Couldn't update this reminder.");
    } finally {
      setCompletingId(null);
    }
  }

  async function handleDelete(id) {
    setDeletingId(id);
    try {
      await deleteReminder(id);
      toast.success("Reminder deleted");
      setReminders((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      toast.error(err.message || "Couldn't delete this reminder.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-medium text-ink">Reminders</h1>
          <p className="mt-1 text-sm text-ink-soft">Medication and follow-up reminders.</p>
        </div>
        <Button onClick={openDialog}>
          <Plus className="size-4" /> New reminder
        </Button>
      </div>

      {/* Honest scope note, not buried in a tooltip - see
          app/models/reminder.py's docstring for why this exists. */}
      <div className="flex items-start gap-2 rounded-[var(--radius-card)] border border-border bg-primary-light p-3 text-xs text-ink-soft">
        <Info className="mt-0.5 size-3.5 shrink-0 text-primary" />
        <p>
          Reminders only notify you while this tab is open in your browser - there's no
          background push, email, or SMS yet.{" "}
          <button
            type="button"
            onClick={handleToggleNotify}
            className="font-medium text-primary underline underline-offset-2"
          >
            {notifyEnabled ? "Notifications on for this tab" : "Enable browser notifications"}
          </button>
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      )}

      {!isLoading && loadError && <p className="text-sm text-danger">{loadError}</p>}

      {!isLoading && !loadError && reminders.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
            <Bell className="size-8 text-ink-faint" />
            <p className="text-sm text-ink-soft">No reminders yet.</p>
            <Button size="sm" variant="outline" onClick={openDialog} className="mt-2">
              <Plus className="size-3.5" /> Add your first reminder
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && !loadError && reminders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Upcoming</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {reminders.map((r) => {
              const meta = CATEGORY_MAP[r.category] ?? CATEGORY_MAP.other;
              const Icon = meta.icon;
              const overdue = isOverdue(r.remind_at);
              return (
                <div
                  key={r.id}
                  className="flex items-center justify-between gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0"
                >
                  <div className="flex min-w-0 items-start gap-3">
                    <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-light text-primary">
                      <Icon className="size-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-ink">{r.title}</p>
                      <p className="mt-0.5 flex flex-wrap items-center gap-1.5 font-mono text-xs">
                        <span className={overdue ? "text-danger" : "text-ink-faint"}>
                          {formatDateTime(r.remind_at)}
                        </span>
                        {r.repeat_every_days && (
                          <Badge variant="neutral" className="text-[10px]">
                            {r.repeat_every_days === 1 ? "Daily" : "Weekly"}
                          </Badge>
                        )}
                        {overdue && (
                          <Badge variant="danger" className="text-[10px]">
                            Overdue
                          </Badge>
                        )}
                      </p>
                      {r.notes && <p className="mt-1 text-xs text-ink-soft">{r.notes}</p>}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleComplete(r.id)}
                      disabled={completingId === r.id}
                    >
                      <Check className="size-3.5" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDelete(r.id)}
                      disabled={deletingId === r.id}
                    >
                      <Trash2 className="size-3.5 text-danger" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New reminder</DialogTitle>
            <DialogDescription>
              For medications, follow-ups, or anything else worth a nudge.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="reminder-title">Title</Label>
              <input
                id="reminder-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Take blood pressure medication"
                className="mt-1 w-full rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 text-sm"
              />
            </div>

            <div>
              <Label htmlFor="reminder-category">Category</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger id="reminder-category" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="reminder-time">When</Label>
              <input
                id="reminder-time"
                type="datetime-local"
                value={remindAt}
                onChange={(e) => setRemindAt(e.target.value)}
                className="mt-1 w-full rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 text-sm"
              />
            </div>

            <div>
              <Label htmlFor="reminder-repeat">Repeat</Label>
              <Select value={repeat} onValueChange={setRepeat}>
                <SelectTrigger id="reminder-repeat" className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {REPEAT_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="reminder-notes">Notes (optional)</Label>
              <textarea
                id="reminder-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="mt-1 w-full rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 text-sm"
              />
            </div>

            {formError && <p className="text-sm text-danger">{formError}</p>}
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={isSaving}>
              {isSaving ? "Saving…" : "Create reminder"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
