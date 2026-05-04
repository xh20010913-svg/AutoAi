import { useToasts, dismissToast } from "@/lib/toast"

export function ToastContainer() {
  const toasts = useToasts()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => {
        const bg =
          t.type === "error"
            ? "border-destructive/30 bg-destructive/10 text-destructive"
            : t.type === "success"
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
              : "border-border bg-card text-card-foreground"
        return (
          <div
            key={t.id}
            className={`rounded-md border px-4 py-2.5 text-sm shadow-lg animate-in slide-in-from-bottom-2 ${bg}`}
            onClick={() => dismissToast(t.id)}
            style={{ cursor: "pointer", animation: "slideInFromBottom 0.2s ease-out" }}
          >
            {t.message}
          </div>
        )
      })}
    </div>
  )
}
