import type { ReactNode } from "react"
import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { TopicCandidatesViewModel } from "../model"
import {
  canExecuteTopicCandidatesEvent,
  useTopicCandidatesMutation,
} from "../mutations"
import { useTopicGenerationRunQuery } from "../queries"
import type { TopicCandidatesWorkspaceProps } from "../ui/contracts"

export function TopicCandidatesContainer({
  projectId,
  runId,
  View,
  onOpenSource,
}: {
  projectId: string
  runId?: string
  View: (props: TopicCandidatesWorkspaceProps) => ReactNode
  onOpenSource?: (
    input: Extract<
      import("../ui/contracts").TopicCandidatesEvent,
      { action: "open-source" }
    >["input"],
  ) => void
}) {
  const query = useTopicGenerationRunQuery(projectId, runId)
  const mutation = useTopicCandidatesMutation(projectId)
  const projection = query.data ?? null
  const content: Loadable<TopicCandidatesViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading topic candidates" }
      : query.isError
        ? { state: "error", error: mapUiError(query.error) }
        : { state: "empty", message: "No topic run is selected." }
  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (event.action === "open-source") {
          onOpenSource?.(event.input)
          return
        }
        if (canExecuteTopicCandidatesEvent(projection, event))
          mutation.mutate(event)
      }}
    />
  )
}
