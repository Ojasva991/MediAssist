import { useEffect, useState, useCallback } from "react";
import { Pencil, Trash2, BookHeart, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { PassportSummary } from "@/components/passport/PassportSummary";
import { PassportForm } from "@/components/passport/PassportForm";
import { useAuth } from "@/context/AuthContext";
import { getPassport, upsertPassport, deletePassport } from "@/api/passport";

export default function Passport() {
  const { user } = useAuth();
  const [passport, setPassport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const [mode, setMode] = useState("view"); // "view" | "edit"
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchPassport = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await getPassport(user.userId);
      setPassport(data);
    } catch (err) {
      if (err.status === 404) {
        setPassport(null); // no passport yet — that's a valid empty state
      } else {
        setLoadError(err);
      }
    } finally {
      setIsLoading(false);
    }
  }, [user.userId]);

  useEffect(() => {
    fetchPassport();
  }, [fetchPassport]);

  async function handleSave(formValues) {
    setIsSaving(true);
    setSaveError(null);
    try {
      const saved = await upsertPassport(user.userId, formValues);
      setPassport(saved ?? formValues);
      setMode("view");
    } catch (err) {
      setSaveError(err);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    setIsDeleting(true);
    try {
      await deletePassport(user.userId);
      setPassport(null);
      setDeleteOpen(false);
    } catch (err) {
      setLoadError(err);
    } finally {
      setIsDeleting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-ink-faint">
        <Spinner size={24} className="mr-2" /> Loading your health passport...
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-xl font-bold text-ink sm:text-2xl">Health Passport</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Your medical profile, ready to share the moment it matters.
          </p>
        </div>

        {passport && mode === "view" && (
          <div className="flex shrink-0 gap-2">
            <Button variant="outline" size="sm" onClick={() => setMode("edit")}>
              <Pencil className="size-3.5" /> Edit
            </Button>
            <Button variant="outline" size="sm" onClick={() => setDeleteOpen(true)}>
              <Trash2 className="size-3.5 text-danger" />
            </Button>
          </div>
        )}
      </div>

      {loadError && (
        <div className="flex items-start gap-2 rounded-[var(--radius-control)] bg-danger-light px-4 py-3 text-sm text-danger">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{loadError.message}</span>
        </div>
      )}

      {!passport && mode === "view" && !loadError && (
        <div className="flex flex-col items-center gap-3 rounded-[var(--radius-card)] border border-dashed border-border bg-surface py-16 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-primary-light text-primary-dark">
            <BookHeart className="size-6" />
          </span>
          <div>
            <p className="font-display font-semibold text-ink">No health passport yet</p>
            <p className="mt-1 text-sm text-ink-soft">
              Create one so your critical info is ready when it's needed most.
            </p>
          </div>
          <Button className="mt-2" onClick={() => setMode("edit")}>
            Create health passport
          </Button>
        </div>
      )}

      {mode === "edit" && (
        <PassportForm
          initialValue={passport}
          onSubmit={handleSave}
          onCancel={passport ? () => setMode("view") : undefined}
          isSaving={isSaving}
          error={saveError}
        />
      )}

      {passport && mode === "view" && <PassportSummary passport={passport} />}

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete health passport?</DialogTitle>
            <DialogDescription>
              This permanently removes your saved medical profile from MediAssist. This
              can't be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={isDeleting}>
                Cancel
              </Button>
            </DialogClose>
            <Button variant="danger" onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? (
                <>
                  <Spinner size={16} /> Deleting...
                </>
              ) : (
                "Delete permanently"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
