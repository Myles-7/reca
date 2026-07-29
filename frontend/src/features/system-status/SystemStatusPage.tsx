import { useQuery } from "@tanstack/react-query"
import {
  CircleAlert,
  CircleCheck,
  CircleHelp,
  CircleOff,
  CirclePause,
  LoaderCircle,
} from "lucide-react"

import {
  ApiError,
  type DependenciesHealthResponse,
  type DependencyCheck,
  type DependencyStatus,
  HealthService,
} from "@/client"
import { ErrorState, LoadingState } from "@/components/Common/PageState"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { publicEnvironment } from "@/shared/environment"

type DisplayStatus = DependencyStatus | "LOADING"

type StatusCardData = {
  name: string
  status: DisplayStatus
  detail: string
}

const dependencyLabels: Readonly<Record<string, string>> = {
  api: "API",
  postgres: "PostgreSQL",
  pgvector: "pgvector",
  valkey: "Valkey",
  worker: "Worker",
  minio: "MinIO",
  grobid: "GROBID",
  model: "Model",
  openalex: "OpenAlex",
}

const requiredDependencies = Object.keys(dependencyLabels)

function isDependencyStatus(
  value: string | undefined,
): value is DependencyStatus {
  return Boolean(
    value &&
      [
        "HEALTHY",
        "DEGRADED",
        "UNAVAILABLE",
        "UNCONFIGURED",
        "UNKNOWN",
      ].includes(value),
  )
}

function displayStatus(value: string | undefined): DependencyStatus {
  return isDependencyStatus(value) ? value : "UNKNOWN"
}

function statusDescription(status: DisplayStatus): string {
  switch (status) {
    case "HEALTHY":
      return "Service responded normally"
    case "DEGRADED":
      return "Service is available with reduced capability"
    case "UNAVAILABLE":
      return "Service could not be reached"
    case "UNCONFIGURED":
      return "Optional service is not configured"
    case "LOADING":
      return "Waiting for health information"
    default:
      return "No safe health status is available"
  }
}

function statusIcon(status: DisplayStatus) {
  const className = "size-4 shrink-0"
  switch (status) {
    case "HEALTHY":
      return <CircleCheck aria-hidden="true" className={className} />
    case "DEGRADED":
      return <CircleAlert aria-hidden="true" className={className} />
    case "UNAVAILABLE":
      return <CircleOff aria-hidden="true" className={className} />
    case "UNCONFIGURED":
      return <CirclePause aria-hidden="true" className={className} />
    case "LOADING":
      return (
        <LoaderCircle
          aria-hidden="true"
          className={`${className} animate-spin`}
        />
      )
    default:
      return <CircleHelp aria-hidden="true" className={className} />
  }
}

function statusVariant(
  status: DisplayStatus,
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "HEALTHY") return "default"
  if (status === "UNAVAILABLE") return "destructive"
  if (status === "LOADING") return "secondary"
  return "outline"
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status >= 500) {
    return "The API reported a server error. Health information may be incomplete."
  }
  return "Health information could not be loaded. Check API connectivity and try again."
}

function toCards(
  response: DependenciesHealthResponse | undefined,
  loading: boolean,
  failed: boolean,
): StatusCardData[] {
  const byName = new Map<string, DependencyCheck>(
    response?.dependencies.map((dependency) => [dependency.name, dependency]),
  )
  return requiredDependencies.map((name) => {
    const dependency = byName.get(name)
    if (dependency) {
      return {
        name: dependencyLabels[name],
        status: displayStatus(dependency.status),
        detail:
          dependency.detail ||
          statusDescription(displayStatus(dependency.status)),
      }
    }
    if (loading)
      return {
        name: dependencyLabels[name],
        status: "LOADING",
        detail: statusDescription("LOADING"),
      }
    return {
      name: dependencyLabels[name],
      status: failed ? "UNAVAILABLE" : "UNKNOWN",
      detail: failed
        ? "Dependency status endpoint was unavailable"
        : statusDescription("UNKNOWN"),
    }
  })
}

export function SystemStatusPage() {
  const live = useQuery({
    queryKey: ["health", "live"],
    queryFn: () => HealthService.liveHealthGetApiV1HealthLive(),
    retry: false,
  })
  const ready = useQuery({
    queryKey: ["health", "ready"],
    queryFn: () => HealthService.readyHealthGetApiV1HealthReady(),
    retry: false,
  })
  const dependencies = useQuery({
    queryKey: ["health", "dependencies"],
    queryFn: () => HealthService.dependenciesHealthGetApiV1HealthDependencies(),
    retry: false,
  })

  const cards = toCards(
    dependencies.data,
    dependencies.isLoading,
    dependencies.isError,
  )
  const apiStatus: DisplayStatus = live.isLoading
    ? "LOADING"
    : live.isError
      ? "UNAVAILABLE"
      : displayStatus(live.data?.status)
  const readyStatus: DisplayStatus = ready.isLoading
    ? "LOADING"
    : ready.isError
      ? "UNAVAILABLE"
      : displayStatus(ready.data?.status)

  return (
    <section aria-labelledby="system-status-title" className="space-y-8">
      <div className="space-y-3">
        <p className="text-sm font-medium text-primary">
          RECA engineering foundation
        </p>
        <h1
          id="system-status-title"
          className="text-3xl font-semibold tracking-tight"
        >
          System status
        </h1>
        <p className="max-w-3xl text-muted-foreground">
          Live, readiness, and dependency health are fetched from the RECA API.
          A failed request is shown as a failure, never as a healthy service.
        </p>
      </div>

      {(live.isError || ready.isError || dependencies.isError) && (
        <ErrorState
          message={errorMessage(
            dependencies.error ?? ready.error ?? live.error,
          )}
        />
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <HealthSummaryCard
          label="API live"
          status={apiStatus}
          detail={
            live.isError
              ? errorMessage(live.error)
              : statusDescription(apiStatus)
          }
        />
        <HealthSummaryCard
          label="Core readiness"
          status={readyStatus}
          detail={
            ready.isError
              ? errorMessage(ready.error)
              : statusDescription(readyStatus)
          }
        />
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Dependencies</h2>
        {dependencies.isLoading ? (
          <LoadingState label="Loading dependency status" />
        ) : null}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <HealthSummaryCard key={card.name} {...card} />
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Runtime context</CardTitle>
          <CardDescription>
            Public build-time settings only; no server credentials are
            displayed.
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

function HealthSummaryCard({
  name,
  label,
  status,
  detail,
}: Omit<StatusCardData, "name"> & { name?: string; label?: string }) {
  const title = label ?? name
  return (
    <Card aria-label={`${title}: ${status}`}>
      <CardHeader className="gap-3">
        <CardTitle className="text-base">{title}</CardTitle>
        <Badge variant={statusVariant(status)}>
          {statusIcon(status)}
          {status}
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {detail || statusDescription(status)}
        </p>
      </CardContent>
    </Card>
  )
}
