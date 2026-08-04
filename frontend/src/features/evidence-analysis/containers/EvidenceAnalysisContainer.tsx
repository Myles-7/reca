import type { ReactNode } from "react"
import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { EvidenceAnalysisViewModel } from "../model"
import {
  canExecuteEvidenceAnalysisEvent,
  useEvidenceAnalysisMutation,
} from "../mutations"
import {
  useEvidenceAnalysisCapabilitiesQuery,
  useEvidenceSummaryQuery,
} from "../queries"
import type { EvidenceAnalysisWorkspaceProps } from "../ui/contracts"

export function EvidenceAnalysisContainer({
  projectId,
  summaryId,
  View,
}: {
  projectId: string
  summaryId?: string
  View: (props: EvidenceAnalysisWorkspaceProps) => ReactNode
}) {
  const query = useEvidenceSummaryQuery(projectId, summaryId)
  const capabilitiesQuery = useEvidenceAnalysisCapabilitiesQuery(projectId)
  const mutation = useEvidenceAnalysisMutation(projectId)
  const content: Loadable<EvidenceAnalysisViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading current evidence analysis" }
      : query.isError
        ? { state: "error", error: mapUiError(query.error) }
        : { state: "empty", message: "No evidence summary is selected." }
  return (
    <View
      content={content}
      capabilities={
        capabilitiesQuery.data ?? {
          permissionsKnown: false,
          canSearchEvidence: false,
          canCreateSummary: false,
          disabledReason: capabilitiesQuery.isError
            ? "Evidence analysis capabilities are unavailable."
            : "Evidence analysis capabilities are loading.",
        }
      }
      searchResult={null}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (
          canExecuteEvidenceAnalysisEvent(
            query.data ?? null,
            capabilitiesQuery.data ?? null,
            event,
          )
        )
          mutation.mutate(event)
      }}
    />
  )
}
