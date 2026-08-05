import type { ReactNode } from "react"

import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { ManuscriptWorkspaceViewModel } from "../model"
import {
  canExecuteManuscriptWorkspaceEvent,
  useManuscriptWorkspaceMutation,
} from "../mutations"
import {
  type ManuscriptWorkspaceSelection,
  useManuscriptWorkspaceQuery,
} from "../queries"
import type {
  ManuscriptWorkspaceEvent,
  ManuscriptWorkspaceProps,
} from "../ui/contracts"

export function ManuscriptWorkspaceContainer({
  projectId,
  selection,
  View,
  initialView,
  onViewChange,
  onSelectionEvent,
  onMutationSuccess,
}: {
  projectId: string
  selection: ManuscriptWorkspaceSelection
  View: (props: ManuscriptWorkspaceProps) => ReactNode
  initialView?: ManuscriptWorkspaceProps["initialView"]
  onViewChange?: ManuscriptWorkspaceProps["onViewChange"]
  onSelectionEvent?: (
    event: Extract<ManuscriptWorkspaceEvent, { action: "select-version" }>,
  ) => void
  onMutationSuccess?: (event: ManuscriptWorkspaceEvent, result: unknown) => void
}) {
  const query = useManuscriptWorkspaceQuery(projectId, selection)
  const mutation = useManuscriptWorkspaceMutation(
    projectId,
    query.data ?? null,
    onMutationSuccess,
  )
  const content: Loadable<ManuscriptWorkspaceViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading manuscript workspace" }
      : query.isError
        ? { state: "error", error: mapUiError(query.error) }
        : { state: "empty", message: "No manuscript is selected." }

  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (event.action === "refresh") {
          void query.refetch()
          return
        }
        if (event.action === "select-version") {
          if (canExecuteManuscriptWorkspaceEvent(query.data ?? null, event)) {
            onSelectionEvent?.(event)
          }
          return
        }
        mutation.mutate(event)
      }}
      initialView={initialView}
      onViewChange={onViewChange}
    />
  )
}
