import type { ReactNode } from "react"

import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { EvidenceWorkspaceViewModel } from "../model"
import {
  canExecuteEvidenceWorkspaceEvent,
  useEvidenceWorkspaceMutation,
} from "../mutations"
import {
  type EvidenceWorkspaceSelection,
  useEvidenceWorkspaceQuery,
} from "../queries"
import type {
  EvidenceWorkspaceEvent,
  EvidenceWorkspaceProps,
} from "../ui/contracts"

export function EvidenceWorkspaceContainer({
  projectId,
  selection,
  View,
  initialView,
  onViewChange,
  onSelectionEvent,
  onMutationSuccess,
}: {
  projectId: string
  selection: EvidenceWorkspaceSelection
  View: (props: EvidenceWorkspaceProps) => ReactNode
  initialView?: EvidenceWorkspaceProps["initialView"]
  onViewChange?: EvidenceWorkspaceProps["onViewChange"]
  onSelectionEvent?: (
    event: Extract<EvidenceWorkspaceEvent, { action: "expand-graph-node" }>,
  ) => void
  onMutationSuccess?: (event: EvidenceWorkspaceEvent, result: unknown) => void
}) {
  const query = useEvidenceWorkspaceQuery(projectId, selection)
  const mutation = useEvidenceWorkspaceMutation(
    projectId,
    query.data ?? null,
    onMutationSuccess,
  )
  const content: Loadable<EvidenceWorkspaceViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading evidence workspace" }
      : query.isError
        ? { state: "error", error: mapUiError(query.error) }
        : { state: "empty", message: "No authorized evidence is available." }

  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (["refresh", "refresh-graph"].includes(event.action)) {
          void query.refetch()
          return
        }
        if (event.action === "expand-graph-node") {
          if (canExecuteEvidenceWorkspaceEvent(query.data ?? null, event))
            onSelectionEvent?.(event)
          return
        }
        mutation.mutate(event)
      }}
      initialView={initialView}
      onViewChange={onViewChange}
    />
  )
}
