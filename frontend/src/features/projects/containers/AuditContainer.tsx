import { mapUiError } from "../mappers"
import type { AuditViewModel, Loadable } from "../model"
import { useAudit } from "../queries"
import { AuditPanel } from "../ui/AuditPanel"

export function AuditContainer({ projectId }: { projectId: string }) {
  const query = useAudit(projectId)
  const content: Loadable<AuditViewModel[]> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading audit history" }
      : { state: "error", error: mapUiError(query.error) }
  const loadError = query.error && query.data ? mapUiError(query.error) : null

  return (
    <AuditPanel
      content={content}
      loadError={loadError}
      onRetry={() => void query.refetch()}
    />
  )
}
