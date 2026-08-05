import type { ReactNode } from "react"

import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { AnalysisWorkspaceViewModel } from "../model"
import { useAnalysisWorkspaceMutation } from "../mutations"
import {
  type AnalysisWorkspaceSelection,
  useAnalysisWorkspaceQuery,
} from "../queries"
import type {
  AnalysisWorkspaceEvent,
  AnalysisWorkspaceWorkspaceProps,
} from "../ui/contracts"

export function AnalysisWorkspaceContainer({
  projectId,
  selection,
  View,
  initialView,
  onViewChange,
  onMutationSuccess,
}: {
  projectId: string
  selection: AnalysisWorkspaceSelection
  View: (props: AnalysisWorkspaceWorkspaceProps) => ReactNode
  initialView?: AnalysisWorkspaceWorkspaceProps["initialView"]
  onViewChange?: AnalysisWorkspaceWorkspaceProps["onViewChange"]
  onMutationSuccess?: (event: AnalysisWorkspaceEvent, result: unknown) => void
}) {
  const query = useAnalysisWorkspaceQuery(projectId, selection)
  const mutation = useAnalysisWorkspaceMutation(
    projectId,
    query.data ?? null,
    onMutationSuccess,
  )
  const content: Loadable<AnalysisWorkspaceViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading analysis workspace" }
      : query.isError
        ? { state: "error", error: mapUiError(query.error) }
        : {
            state: "empty",
            message: "No analysis context is selected in this project.",
          }
  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={mutation.mutate}
      initialView={initialView}
      onViewChange={onViewChange}
    />
  )
}
