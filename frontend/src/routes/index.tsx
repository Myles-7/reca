import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowRight, HeartPulse } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { publicEnvironment } from "@/shared/environment"

export const Route = createFileRoute("/")({
  component: HomePage,
  head: () => ({ meta: [{ title: "RECA | Research Evidence Chain Agent" }] }),
})

function HomePage() {
  return (
    <section aria-labelledby="reca-title" className="space-y-8 py-8 sm:py-16">
      <div className="max-w-3xl space-y-5">
        <p className="font-medium text-primary">研证链 AI</p>
        <h1
          id="reca-title"
          className="text-4xl font-semibold tracking-tight sm:text-5xl"
        >
          RECA
        </h1>
        <p className="text-xl text-muted-foreground">
          Research Evidence Chain Agent
        </p>
        <p className="max-w-2xl leading-7 text-muted-foreground">
          RECA is currently in its engineering foundation phase. Authentication,
          infrastructure, configuration, and system health foundations are being
          established; research project and evidence-chain business workflows
          are not available yet.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to="/system-status">
              <HeartPulse aria-hidden="true" />
              View system status
              <ArrowRight aria-hidden="true" />
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/login">Log in</Link>
          </Button>
        </div>
      </div>
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Current runtime</CardTitle>
          <CardDescription>
            Only public application settings are shown.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          <p>
            <span className="font-medium">Environment:</span>{" "}
            {publicEnvironment.appEnv}
          </p>
          <p>
            <span className="font-medium">Demo Mode:</span>{" "}
            {publicEnvironment.demoMode ? "enabled" : "disabled"}
          </p>
        </CardContent>
      </Card>
    </section>
  )
}
