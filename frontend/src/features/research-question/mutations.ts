import { useMutation, useQueryClient } from "@tanstack/react-query"

import { ResearchQuestionsApi } from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import type { UiErrorViewModel } from "../projects/model"
import type { ResearchQuestionViewModel } from "./model"
import { researchQuestionKeys } from "./queries"
import type {
  ResearchQuestionCreateEvent,
  ResearchQuestionEvent,
  ResearchQuestionMarkReadyEvent,
  ResearchQuestionRequestConfirmationEvent,
  ResearchQuestionSaveVersionEvent,
} from "./ui/contracts"

function idempotencyKey(): string {
  return crypto.randomUUID()
}

export type ResearchQuestionMutationPort = {
  create: (
    projectId: string,
    event: ResearchQuestionCreateEvent,
  ) => Promise<unknown>
  saveVersion: (event: ResearchQuestionSaveVersionEvent) => Promise<unknown>
  markReady: (event: ResearchQuestionMarkReadyEvent) => Promise<unknown>
  requestConfirmation: (
    event: ResearchQuestionRequestConfirmationEvent,
  ) => Promise<unknown>
}

export const researchQuestionMutationPort: ResearchQuestionMutationPort = {
  create: (projectId, event) =>
    ResearchQuestionsApi.create(
      projectId,
      { raw_input: event.rawInput },
      idempotencyKey(),
    ),
  saveVersion: (event) =>
    ResearchQuestionsApi.createVersion(
      event.questionId,
      {
        based_on_version_id: event.basedOnVersionId,
        change_reason: event.changeReason,
        fields: {
          raw_input: event.fields.rawInput,
          normalized_question: event.fields.normalizedQuestion,
          research_object: event.fields.researchObject,
          population: event.fields.population,
          context: event.fields.context,
          independent_variables: event.fields.independentVariables,
          dependent_variables: event.fields.dependentVariables,
          control_variables: event.fields.controlVariables,
          research_goal: event.fields.researchGoal,
          relationship_type: event.fields.relationshipType,
          method_preference: event.fields.methodPreference,
          time_scope: event.fields.timeScope,
          region_scope: event.fields.regionScope,
          language_scope: event.fields.languageScope,
          resource_constraints: event.fields.resourceConstraints,
          ethical_constraints: event.fields.ethicalConstraints,
          uncertainties: event.fields.uncertainties,
        },
      },
      idempotencyKey(),
    ),
  markReady: (event) =>
    ResearchQuestionsApi.markReady(
      event.versionId,
      { reason: event.reason },
      idempotencyKey(),
    ),
  requestConfirmation: (event) =>
    ResearchQuestionsApi.requestConfirmation(event.versionId, idempotencyKey()),
}

export function executeResearchQuestionEvent(
  projectId: string,
  event: ResearchQuestionEvent,
  port: ResearchQuestionMutationPort = researchQuestionMutationPort,
) {
  if (event.action === "create") return port.create(projectId, event.input)
  if (event.action === "save-version") return port.saveVersion(event.input)
  if (event.action === "mark-ready") return port.markReady(event.input)
  return port.requestConfirmation(event.input)
}

export function canExecuteResearchQuestionEvent(
  question: ResearchQuestionViewModel | null,
  canCreate: boolean,
  event: ResearchQuestionEvent,
): boolean {
  if (event.action === "create") {
    return (
      question === null && canCreate && event.input.rawInput.trim().length > 0
    )
  }
  if (!question || !question.knownStatus || !question.permissionsKnown) {
    return false
  }
  if (event.action === "save-version") {
    return (
      question.permissions.canEdit &&
      question.permissions.canCreateVersion &&
      event.input.questionId === question.questionId &&
      event.input.basedOnVersionId === question.currentVersionId
    )
  }
  if (event.action === "mark-ready") {
    return (
      question.permissions.canMarkReady &&
      event.input.versionId === question.currentVersionId
    )
  }
  return (
    question.permissions.canRequestConfirmation &&
    event.input.versionId === question.currentVersionId
  )
}

export function useResearchQuestionMutation(projectId: string) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (event: ResearchQuestionEvent) =>
      executeResearchQuestionEvent(projectId, event),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: researchQuestionKeys.current(projectId),
      }),
  })
  return {
    mutate: mutation.mutate,
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error
      ? (mapUiError(mutation.error) satisfies UiErrorViewModel)
      : null,
  }
}
