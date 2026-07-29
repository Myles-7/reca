import { Link } from "@tanstack/react-router"
import type { FallbackProps } from "react-error-boundary"

import { Button } from "@/components/ui/button"

export function AppErrorBoundary({ resetErrorBoundary }: FallbackProps) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-2xl font-semibold">Application error</h1>
      <p className="max-w-md text-muted-foreground">
        The page could not be displayed safely. No diagnostic details are shown
        here.
      </p>
      <div className="flex gap-3">
        <Button onClick={resetErrorBoundary} variant="outline">
          Try again
        </Button>
        <Button asChild>
          <Link to="/">Go home</Link>
        </Button>
      </div>
    </main>
  )
}
