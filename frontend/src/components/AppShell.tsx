import { Link, Outlet } from "@tanstack/react-router"
import { Activity, LogIn } from "lucide-react"

import { Button } from "@/components/ui/button"

export function AppShell() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <nav
          aria-label="Primary navigation"
          className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6"
        >
          <Link to="/" className="font-semibold tracking-tight">
            RECA
          </Link>
          <div className="flex items-center gap-2">
            <Link
              to="/system-status"
              className="inline-flex min-h-9 items-center gap-2 rounded-md px-3 text-sm font-medium hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Activity aria-hidden="true" className="size-4" />
              System status
            </Link>
            <Button asChild size="sm" variant="outline">
              <Link to="/login">
                <LogIn aria-hidden="true" />
                Log in
              </Link>
            </Button>
          </div>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
        <Outlet />
      </main>
    </div>
  )
}
