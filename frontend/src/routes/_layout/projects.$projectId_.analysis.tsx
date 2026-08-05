import { createFileRoute } from "@tanstack/react-router"

import { AnalysisWorkspaceContainer } from "@/features/analysis-workspace/containers/AnalysisWorkspaceContainer"
import { parseAnalysisWorkspaceSearch } from "@/features/analysis-workspace/route-contract"
import { AnalysisWorkspace } from "@/features/analysis-workspace/ui/AnalysisWorkspace"
import type { AnalysisWorkspaceEvent } from "@/features/analysis-workspace/ui/contracts"

export const Route = createFileRoute("/_layout/projects/$projectId_/analysis")({
  validateSearch: parseAnalysisWorkspaceSearch,
  component: AnalysisWorkspaceRoute,
  head: () => ({ meta: [{ title: "Analysis Workspace - RECA" }] }),
})

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null
}

function envelopeData(value: unknown) {
  return record(record(value)?.data)
}

function nested(value: Record<string, unknown> | null, field: string) {
  return record(value?.[field])
}

function stringField(value: Record<string, unknown> | null, field: string) {
  const item = value?.[field]
  return typeof item === "string" ? item : undefined
}

function AnalysisWorkspaceRoute() {
  const { projectId } = Route.useParams()
  const search = Route.useSearch()
  const navigate = Route.useNavigate()
  const updateSearch = (next: Partial<typeof search>) =>
    void navigate({ search: (previous) => ({ ...previous, ...next }) })

  const onMutationSuccess = (
    event: AnalysisWorkspaceEvent,
    result: unknown,
  ) => {
    const data = envelopeData(result)
    switch (event.action) {
      case "create-analysis-plan":
        updateSearch({
          analysisPlan: stringField(data, "id"),
          version:
            stringField(data, "dataset_version_id") ??
            event.input.datasetVersionId,
          view: "plan",
        })
        break
      case "update-analysis-plan":
      case "validate-analysis-plan":
        updateSearch({
          analysisPlan: stringField(data, "id") ?? event.input.planId,
          version: stringField(data, "dataset_version_id"),
          view: "plan",
        })
        break
      case "request-analysis-approval":
        updateSearch({
          analysisPlan: event.input.planId,
          approval: stringField(data, "approval_id"),
          view: "plan",
        })
        break
      case "run-analysis": {
        const run = nested(data, "analysis_run")
        const job = nested(data, "job")
        updateSearch({
          analysisPlan: event.input.planId,
          analysisRun: stringField(run, "id"),
          analysisResult: undefined,
          approval: stringField(run, "approval_record_id"),
          job: stringField(job, "id"),
          view: "runs",
        })
        break
      }
      case "invalidate-analysis-run":
        updateSearch({ analysisRun: event.input.runId, view: "runs" })
        break
      case "retry-job":
      case "cancel-job":
        updateSearch({ job: stringField(data, "id") ?? event.input.jobId })
        break
      case "create-figure-plan":
        updateSearch({
          version: event.input.datasetVersionId,
          analysisRun: event.input.analysisRunId ?? undefined,
          analysisResult: event.input.analysisResultId ?? undefined,
          figurePlan: stringField(data, "id"),
          renderRun: undefined,
          figure: undefined,
          view: "figures",
        })
        break
      case "render-figure": {
        const renderRun = nested(data, "figure_render_run")
        const job = nested(data, "job")
        updateSearch({
          figurePlan: event.input.figurePlanId,
          renderRun: stringField(renderRun, "id"),
          figure: stringField(renderRun, "figure_id"),
          job: stringField(job, "id"),
          view: "figures",
        })
        break
      }
      case "request-figure-confirmation":
        updateSearch({
          figure: event.input.figureId,
          approval: stringField(data, "approval_id"),
          view: "figures",
        })
        break
      case "decide-figure-confirmation":
        updateSearch({ approval: event.input.approvalId, view: "figures" })
        break
      case "download-artifact": {
        const downloadUrl = stringField(data, "download_url")
        if (downloadUrl) window.location.assign(downloadUrl)
        break
      }
      case "request-suggestion":
      case "request-interpretation":
        break
    }
  }

  return (
    <AnalysisWorkspaceContainer
      projectId={projectId}
      selection={{
        datasetId: search.dataset,
        versionId: search.version,
        analysisPlanId: search.analysisPlan,
        analysisRunId: search.analysisRun,
        analysisResultId: search.analysisResult,
        approvalId: search.approval,
        jobId: search.job,
        figurePlanId: search.figurePlan,
        figureId: search.figure,
        renderRunId: search.renderRun,
      }}
      View={AnalysisWorkspace}
      initialView={search.view}
      onViewChange={(view) => updateSearch({ view })}
      onMutationSuccess={onMutationSuccess}
    />
  )
}
