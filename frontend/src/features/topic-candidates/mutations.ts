import { useMutation } from "@tanstack/react-query"
import { EvidenceApi } from "@/api/adapter"
import { mapUiError } from "../projects/mappers"
import type { TopicCandidatesViewModel } from "./model"
import type { TopicCandidatesEvent } from "./ui/contracts"

export function canExecuteTopicCandidatesEvent(
  model: TopicCandidatesViewModel | null,
  event: TopicCandidatesEvent,
) {
  if (event.action === "generate-topic")
    return (
      event.input.candidateCount === 3 &&
      event.input.summaryId.length > 0 &&
      event.input.researchQuestionVersionId.length > 0
    )
  return (
    model?.knownStatus === true &&
    model.permissionsKnown &&
    model.exactlyThree &&
    model.sourcesValid
  )
}

export function useTopicCandidatesMutation(projectId: string) {
  const mutation = useMutation({
    mutationFn: (event: TopicCandidatesEvent) => {
      if (event.action !== "generate-topic") return Promise.resolve(null)
      return EvidenceApi.generateTopics(
        projectId,
        {
          research_question_version_id: event.input.researchQuestionVersionId,
          evidence_set_summary_id: event.input.summaryId,
          candidate_count: 3,
          user_constraints: event.input.userConstraints,
        },
        crypto.randomUUID(),
      )
    },
  })
  return {
    mutate: mutation.mutate,
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
