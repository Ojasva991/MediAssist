import { createContext, useCallback, useContext, useState } from "react";
import { CheckCircle2, XCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

const ToastContext = createContext(null);
let idCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (variant, message) => {
      const id = ++idCounter;
      setToasts((prev) => [...prev, { id, variant, message }]);
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss]
  );

  const toast = {
    success: (message) => push("success", message),
    error: (message) => push("error", message),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4 sm:items-end sm:px-6">
        {toasts.map((t) => (
          <Toast key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function Toast({ toast, onDismiss }) {
  const isSuccess = toast.variant === "success";
  const Icon = isSuccess ? CheckCircle2 : XCircle;

  return (
    <div
      className={cn(
        "animate-fade-up pointer-events-auto flex w-full max-w-sm items-start gap-2.5 rounded-[var(--radius-control)] border bg-surface p-4 shadow-[var(--shadow-card)]",
        isSuccess ? "border-success/30" : "border-danger/30"
      )}
      role="status"
    >
      <Icon
        className={cn("mt-0.5 size-4.5 shrink-0", isSuccess ? "text-success" : "text-danger")}
      />
      <p className="flex-1 text-sm text-ink">{toast.message}</p>
      <button
        onClick={onDismiss}
        className="shrink-0 text-ink-faint transition-colors hover:text-ink"
        aria-label="Dismiss"
      >
        <X className="size-4" />
      </button>
    </div>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
