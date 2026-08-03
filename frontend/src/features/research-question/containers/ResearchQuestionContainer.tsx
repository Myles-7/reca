import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type {
  ResearchQuestionCapabilityAvailability,
  ResearchQuestionViewModel,
} from "../model"
import {
  canExecuteResearchQuestionEvent,
  useResearchQuestionMutation,
} from "../mutations"
import { useResearchQuestionQuery } from "../queries"
import { ResearchQuestionWorkspace } from "../ui/ResearchQuestionWorkspace"

const unknownCapabilities: ResearchQuestionCapabilityAvailability = {
  researchQuestion: "UNKNOWN",
  aiParse: "UNKNOWN",
  queryPlan: "UNKNOWN",
  literature: "UNKNOWN",
}

export function ResearchQuestionContainer({
  projectId,
}: {
  projectId: string
}) {
  const query = useResearchQuestionQuery(projectId)
  const mutation = useResearchQuestionMutation(projectId)
  const content: Loadable<ResearchQuestionViewModel> = query.data?.question
    ? { state: "ready", data: query.data.question }
    : query.isSuccess
      ? {
          state: "empty",
          message: "No research question has been created for this project.",
        }
      : query.isLoading
        ? { state: "loading", label: "Loading research question" }
        : { state: "error", error: mapUiError(query.error) }

  return (
    <ResearchQuestionWorkspace
      content={content}
      canCreate={query.data?.canCreate ?? false}
      capabilities={query.data?.capabilities ?? unknownCapabilities}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (
          canExecuteResearchQuestionEvent(
            query.data?.question ?? null,
            query.data?.canCreate ?? false,
            event,
          )
        ) {
          mutation.mutate(event)
        }
      }}
    />
  )
}
