import { mapUiError } from "../mappers"
import type { Loadable, OverviewViewModel } from "../model"
import { useOverview } from "../queries"
import { OverviewPanel } from "../ui/OverviewPanel"

export function OverviewContainer({ projectId }: { projectId: string }) {
  const query = useOverview(projectId)
  const content: Loadable<OverviewViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading project overview" }
      : { state: "error", error: mapUiError(query.error) }
  const loadError = query.error && query.data ? mapUiError(query.error) : null

  return (
    <OverviewPanel
      content={content}
      loadError={loadError}
      onRetry={() => void query.refetch()}
    />
  )
}
