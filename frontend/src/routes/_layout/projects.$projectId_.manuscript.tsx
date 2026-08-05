import { createFileRoute } from "@tanstack/react-router"

import { ManuscriptWorkspaceContainer } from "@/features/manuscript-workspace/containers/ManuscriptWorkspaceContainer"
import { parseManuscriptWorkspaceSearch } from "@/features/manuscript-workspace/route-contract"
import type { ManuscriptWorkspaceEvent } from "@/features/manuscript-workspace/ui/contracts"
import { ManuscriptWorkspace } from "@/features/manuscript-workspace/ui/ManuscriptWorkspace"

export const Route = createFileRoute(
  "/_layout/projects/$projectId_/manuscript",
)({
  validateSearch: parseManuscriptWorkspaceSearch,
  component: ManuscriptRoute,
  head: () => ({ meta: [{ title: "Manuscript - RECA" }] }),
})

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null
}

function idFrom(value: unknown): string | undefined {
  const item = record(value)?.id
  return typeof item === "string" ? item : undefined
}

function ManuscriptRoute() {
  const { projectId } = Route.useParams()
  const search = Route.useSearch()
  const navigate = Route.useNavigate()
  const updateSearch = (next: Partial<typeof search>) =>
    void navigate({ search: (previous) => ({ ...previous, ...next }) })

  const onMutationSuccess = (
    event: ManuscriptWorkspaceEvent,
    result: unknown,
  ) => {
    const data = record(record(result)?.data)
    const id = idFrom(data)
    switch (event.action) {
      case "select-version":
        updateSearch({ version: event.input.versionId })
        break
      case "start-check":
        updateSearch({
          version: event.input.versionId,
          checkRun: id,
          view: "checks",
        })
        break
      case "create-fix-plan":
        updateSearch({
          transformation: id,
          version: event.input.versionId,
          view: "fixes",
        })
        break
      case "preview-fix-plan":
      case "request-fix-approval":
      case "execute-fix-plan":
        updateSearch({
          transformation: id ?? event.input.planId,
          view: "fixes",
        })
        break
      case "start-revision-audit":
        updateSearch({ audit: id, view: "audits" })
        break
      case "create-claim":
      case "update-claim":
      case "request-claim-confirmation":
        updateSearch({
          claim:
            id ?? ("claimId" in event.input ? event.input.claimId : undefined),
          view: "claims",
        })
        break
      case "upload-manuscript":
      case "accept-issue":
      case "reject-issue":
      case "retry-job":
      case "cancel-job":
      case "download-version":
      case "refresh":
        break
    }
  }

  return (
    <ManuscriptWorkspaceContainer
      projectId={projectId}
      selection={{
        manuscript: search.manuscript,
        version: search.version,
        checkRun: search.checkRun,
        issue: search.issue,
        transformation: search.transformation,
        audit: search.audit,
        claim: search.claim,
      }}
      View={ManuscriptWorkspace}
      initialView={search.view}
      onViewChange={(view) => updateSearch({ view })}
      onMutationSuccess={onMutationSuccess}
    />
  )
}
