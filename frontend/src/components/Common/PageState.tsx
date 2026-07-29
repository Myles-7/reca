import { AlertCircle, LoaderCircle } from "lucide-react"
import type { ReactNode } from "react"

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div
      aria-live="polite"
      className="flex items-center gap-2 text-muted-foreground"
    >
      <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />
      <span>{label}</span>
    </div>
  )
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div
      aria-live="polite"
      className="flex items-start gap-2 text-sm text-destructive"
    >
      <AlertCircle aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <span>{message}</span>
    </div>
  )
}
