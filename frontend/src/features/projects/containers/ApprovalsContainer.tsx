import { mapUiError } from "../mappers"
import type { ApprovalViewModel, Loadable } from "../model"
import {
  canExecuteApprovalAction,
  useApprovalActionMutation,
} from "../mutations"
import { useApprovals } from "../queries"
import { ApprovalsPanel } from "../ui/ApprovalsPanel"

export function ApprovalsContainer({ projectId }: { projectId: string }) {
  const query = useApprovals(projectId)
  const mutation = useApprovalActionMutation(projectId)
  const content: Loadable<ApprovalViewModel[]> = query.isLoading
    ? { state: "loading", label: "Loading approvals" }
    : query.data
      ? { state: "ready", data: query.data }
      : { state: "error", error: mapUiError(query.error) }
  const loadError = query.error && query.data ? mapUiError(query.error) : null

  return (
    <ApprovalsPanel
      content={content}
      submittingApprovalId={mutation.submittingApprovalId}
      loadError={loadError}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onAction={(event) => {
        if (canExecuteApprovalAction(query.data ?? [], event)) {
          mutation.mutate(event)
        }
      }}
    />
  )
}
