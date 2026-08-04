import type { ReactNode } from "react"

import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { DataWorkspaceViewModel } from "../model"
import {
  canExecuteDataWorkspaceEvent,
  useDataWorkspaceMutation,
} from "../mutations"
import { type DataWorkspaceSelection, useDataWorkspaceQuery } from "../queries"
import type {
  DataWorkspaceEvent,
  DataWorkspaceWorkspaceProps,
} from "../ui/contracts"

export function DataWorkspaceContainer({
  projectId,
  selection,
  View,
  initialView,
  onViewChange,
  onSelectionEvent,
  onMutationSuccess,
}: {
  projectId: string
  selection: DataWorkspaceSelection
  View: (props: DataWorkspaceWorkspaceProps) => ReactNode
  initialView?: DataWorkspaceWorkspaceProps["initialView"]
  onViewChange?: DataWorkspaceWorkspaceProps["onViewChange"]
  onSelectionEvent?: (
    event: Extract<
      DataWorkspaceEvent,
      { action: "select-version" | "compare-versions" }
    >,
  ) => void
  onMutationSuccess?: (event: DataWorkspaceEvent, result: unknown) => void
}) {
  const query = useDataWorkspaceQuery(projectId, selection)
  const mutation = useDataWorkspaceMutation(
    projectId,
    query.data ?? null,
    onMutationSuccess,
  )
  const content: Loadable<DataWorkspaceViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading data workspace" }
      : query.isError
        ? { state: "error", error: mapUiError(query.error) }
        : {
            state: "empty",
            message: "No datasets are available in this project.",
          }
  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (
          event.action === "select-version" ||
          event.action === "compare-versions"
        ) {
          if (canExecuteDataWorkspaceEvent(query.data ?? null, event)) {
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
