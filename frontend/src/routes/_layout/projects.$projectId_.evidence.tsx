import { createFileRoute } from "@tanstack/react-router"

import { EvidenceWorkspaceContainer } from "@/features/evidence-workspace/containers/EvidenceWorkspaceContainer"
import { parseEvidenceWorkspaceSearch } from "@/features/evidence-workspace/route-contract"
import type { EvidenceWorkspaceEvent } from "@/features/evidence-workspace/ui/contracts"
import { EvidenceWorkspace } from "@/features/evidence-workspace/ui/EvidenceWorkspace"

export const Route = createFileRoute("/_layout/projects/$projectId_/evidence")({
  validateSearch: parseEvidenceWorkspaceSearch,
  component: EvidenceWorkspaceRoute,
  head: () => ({ meta: [{ title: "Evidence & Export Workspace - RECA" }] }),
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

function EvidenceWorkspaceRoute() {
  const { projectId } = Route.useParams()
  const search = Route.useSearch()
  const navigate = Route.useNavigate()
  const updateSearch = (next: Partial<typeof search>) =>
    void navigate({ search: (previous) => ({ ...previous, ...next }) })

  const onMutationSuccess = (
    event: EvidenceWorkspaceEvent,
    result: unknown,
  ) => {
    const data = envelopeData(result)
    switch (event.action) {
      case "create-evidence-link":
      case "confirm-evidence-link":
      case "invalidate-evidence-link":
        updateSearch({
          claim:
            stringField(data, "claim_id") ??
            (event.action === "create-evidence-link"
              ? event.input.claimId
              : search.claim),
          link:
            stringField(data, "id") ??
            (event.action === "create-evidence-link"
              ? undefined
              : event.linkId),
          view: "claims",
        })
        break
      case "run-claim-audit": {
        const audit = nested(data, "audit_result")
        updateSearch({
          claim: event.claimId,
          audit: stringField(audit, "id"),
          view: "audits",
        })
        break
      }
      case "run-export-readiness":
        updateSearch({ view: "exports" })
        break
      case "request-export-confirmation":
        updateSearch({ export: event.exportId, view: "exports" })
        break
      case "create-repro-package": {
        const exportValue = nested(data, "export")
        updateSearch({
          export: stringField(exportValue, "id"),
          package: undefined,
          view: "exports",
        })
        break
      }
      case "retry-job":
      case "cancel-job":
        updateSearch({ view: "exports" })
        break
      case "download-repro-package": {
        const download = nested(data, "download")
        const downloadUrl = stringField(download, "download_url")
        if (downloadUrl) window.location.assign(downloadUrl)
        break
      }
      case "expand-graph-node":
      case "refresh-graph":
      case "refresh":
        break
    }
  }

  return (
    <EvidenceWorkspaceContainer
      projectId={projectId}
      selection={{
        claim: search.claim,
        node: search.node,
        link: search.link,
        audit: search.audit,
        export: search.export,
        package: search.package,
        view: search.view,
      }}
      View={EvidenceWorkspace}
      initialView={search.view}
      onViewChange={(view) => updateSearch({ view })}
      onSelectionEvent={(event) =>
        updateSearch({ node: event.nodeId, view: "graph" })
      }
      onMutationSuccess={onMutationSuccess}
    />
  )
}
