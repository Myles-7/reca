import type { ComponentType } from "react"

import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { LiteratureWorkspaceViewModel } from "../model"
import { canExecuteLiteratureEvent, useLiteratureMutation } from "../mutations"
import { useLiteratureQuery } from "../queries"
import type { LiteratureWorkspaceProps } from "../ui/contracts"

export function LiteratureContainer({
  projectId,
  searchRunId,
  View,
  onSearchRunCreated,
}: {
  projectId: string
  searchRunId?: string
  View: ComponentType<LiteratureWorkspaceProps>
  onSearchRunCreated?: (searchRunId: string) => void
}) {
  const query = useLiteratureQuery(projectId, searchRunId)
  const mutation = useLiteratureMutation(
    projectId,
    searchRunId,
    onSearchRunCreated,
  )
  const content: Loadable<LiteratureWorkspaceViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading literature" }
      : { state: "error", error: mapUiError(query.error) }
  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (canExecuteLiteratureEvent(query.data ?? null, event)) {
          mutation.mutate(event)
        }
      }}
    />
  )
}
