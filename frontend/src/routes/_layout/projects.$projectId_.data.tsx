import { createFileRoute } from "@tanstack/react-router"

import { DataWorkspaceContainer } from "@/features/data-workspace/containers/DataWorkspaceContainer"
import { parseDataWorkspaceSearch } from "@/features/data-workspace/route-contract"
import type { DataWorkspaceEvent } from "@/features/data-workspace/ui/contracts"
import { DataWorkspace } from "@/features/data-workspace/ui/DataWorkspace"

export const Route = createFileRoute("/_layout/projects/$projectId_/data")({
  validateSearch: parseDataWorkspaceSearch,
  component: DataWorkspaceRoute,
  head: () => ({ meta: [{ title: "Data Workspace - RECA" }] }),
})

function envelopeData(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object") return null
  const data = (value as { data?: unknown }).data
  return data && typeof data === "object"
    ? (data as Record<string, unknown>)
    : null
}

function stringField(value: Record<string, unknown> | null, field: string) {
  const item = value?.[field]
  return typeof item === "string" ? item : undefined
}

function DataWorkspaceRoute() {
  const { projectId } = Route.useParams()
  const search = Route.useSearch()
  const navigate = Route.useNavigate()
  const updateSearch = (next: Partial<typeof search>) =>
    void navigate({ search: (previous) => ({ ...previous, ...next }) })

  const onSelectionEvent = (
    event: Extract<
      DataWorkspaceEvent,
      { action: "select-version" | "compare-versions" }
    >,
  ) => {
    if (event.action === "select-version") {
      updateSearch({
        dataset: event.input.datasetId,
        version: event.input.versionId,
        qualityRun: undefined,
        plan: undefined,
        approval: undefined,
        job: undefined,
        compareWith: undefined,
      })
      return
    }
    updateSearch({
      dataset: event.input.datasetId,
      version: event.input.targetVersionId,
      compareWith: event.input.baseVersionId,
      view: "versions",
    })
  }

  const onMutationSuccess = (event: DataWorkspaceEvent, result: unknown) => {
    const data = envelopeData(result)
    switch (event.action) {
      case "upload-dataset": {
        const dataset =
          data?.dataset && typeof data.dataset === "object"
            ? (data.dataset as Record<string, unknown>)
            : null
        const version =
          data?.version && typeof data.version === "object"
            ? (data.version as Record<string, unknown>)
            : null
        updateSearch({
          dataset: stringField(dataset, "id"),
          version: stringField(version, "id"),
          qualityRun: undefined,
          plan: undefined,
          approval: undefined,
          job: undefined,
          compareWith: undefined,
          view: "data",
        })
        break
      }
      case "run-quality": {
        const run =
          data?.run && typeof data.run === "object"
            ? (data.run as Record<string, unknown>)
            : null
        const job =
          data?.job && typeof data.job === "object"
            ? (data.job as Record<string, unknown>)
            : null
        updateSearch({
          qualityRun: stringField(run, "id"),
          job: stringField(job, "id"),
          view: "quality",
        })
        break
      }
      case "create-plan":
      case "update-plan":
      case "preview-plan":
        updateSearch({ plan: stringField(data, "id"), view: "cleaning" })
        break
      case "request-approval":
        updateSearch({
          plan: event.input.planId,
          approval: stringField(data, "approval_id"),
          view: "cleaning",
        })
        break
      case "execute-plan": {
        const job =
          data?.job && typeof data.job === "object"
            ? (data.job as Record<string, unknown>)
            : null
        updateSearch({
          plan: event.input.planId,
          job: stringField(job, "id"),
          view: "cleaning",
        })
        break
      }
      default:
        break
    }
  }

  return (
    <DataWorkspaceContainer
      projectId={projectId}
      selection={{
        datasetId: search.dataset,
        versionId: search.version,
        qualityRunId: search.qualityRun,
        planId: search.plan,
        approvalId: search.approval,
        jobId: search.job,
        compareWithVersionId: search.compareWith,
      }}
      View={DataWorkspace}
      initialView={search.view}
      onViewChange={(view) => updateSearch({ view })}
      onSelectionEvent={onSelectionEvent}
      onMutationSuccess={onMutationSuccess}
    />
  )
}
