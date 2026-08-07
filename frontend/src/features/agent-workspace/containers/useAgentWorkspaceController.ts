import { mapUiError } from "../../projects/mappers"
import { useAgentWorkspaceMutation } from "../mutations"
import { useAgentWorkspaceQuery } from "../queries"
import type { AgentWorkspaceRouteSearch } from "../route-contract"
import type { AgentWorkspaceEvent, AgentWorkspaceProps } from "../ui/contracts"

export function useAgentWorkspaceController(
  projectId: string,
  search: AgentWorkspaceRouteSearch,
  onIntent?: AgentWorkspaceProps["onEvent"],
  onToolSelectionChange?: AgentWorkspaceProps["onToolSelectionChange"],
  onMutationSuccess?: (event: AgentWorkspaceEvent, result: unknown) => void,
): AgentWorkspaceProps {
  const query = useAgentWorkspaceQuery(projectId, search)
  const workspace = query.data ?? null
  const mutation = useAgentWorkspaceMutation(
    projectId,
    workspace,
    onMutationSuccess,
  )
  const content: AgentWorkspaceProps["content"] = query.isPending
    ? { state: "loading", label: "Loading Agent workspace" }
    : query.error
      ? { state: "error", error: mapUiError(query.error) }
      : workspace
        ? { state: "ready", data: workspace }
        : { state: "empty", message: "No AgentRun is selected." }
  return {
    content,
    pendingAction: mutation.pendingAction,
    mutationError: mutation.uiError,
    onRetry: () => void query.refetch(),
    onEvent: (event) => {
      if (event.action === "refresh") void query.refetch()
      else if (["open-source", "open-approval"].includes(event.action))
        onIntent?.(event)
      else mutation.mutate(event)
    },
    selectedToolCallId: search.tool ?? null,
    onToolSelectionChange,
  }
}
