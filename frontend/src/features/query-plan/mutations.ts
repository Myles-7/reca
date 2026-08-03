import type { QueryClient } from "@tanstack/react-query"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { QueryPlansApi } from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import { projectKeys } from "../projects/queries"
import type { QueryPlanViewModel } from "./model"
import { queryPlanKeys } from "./queries"
import type { QueryPlanEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

export function canExecuteQueryPlanEvent(
  plan: QueryPlanViewModel | null,
  event: QueryPlanEvent,
): boolean {
  if (!plan || !plan.knownStatus || !plan.permissionsKnown) return false
  if (event.action === "update") {
    return (
      plan.permissions.canUpdate &&
      event.input.queryPlanId === plan.id &&
      event.input.lockVersion === plan.lockVersion
    )
  }
  if (event.action === "generate") {
    return plan.permissions.canGenerate && event.input.queryPlanId === plan.id
  }
  return false
}

function fields(value: import("./model").QueryPlanFieldsViewModel) {
  const groups = (input: Readonly<Record<string, readonly string[]>>) =>
    Object.fromEntries(
      Object.entries(input).map(([name, terms]) => [name, [...terms]]),
    )
  return {
    chinese_terms: [...value.chineseTerms],
    english_terms: [...value.englishTerms],
    synonyms: groups(value.synonyms),
    object_terms: groups(value.objectTerms),
    method_terms: groups(value.methodTerms),
    boolean_query: value.booleanQuery,
    filters: {
      from_year: value.filters.fromYear,
      to_year: value.filters.toYear,
      languages: [...value.filters.languages],
      work_types: [...value.filters.workTypes],
      open_access_only: value.filters.openAccessOnly,
    },
    limitations: [...value.limitations],
  }
}

export async function executeQueryPlanEvent(
  projectId: string,
  event: QueryPlanEvent,
) {
  if (event.action === "create") {
    return QueryPlansApi.create(
      projectId,
      {
        research_question_version_id: event.input.researchQuestionVersionId,
        ...fields(event.input),
      },
      key(),
    )
  }
  if (event.action === "update") {
    return QueryPlansApi.update(
      event.input.queryPlanId,
      {
        fields: fields(event.input.fields),
        change_reason: event.input.changeReason,
      },
      event.input.lockVersion,
    )
  }
  return QueryPlansApi.generate(event.input.queryPlanId, key())
}

export async function invalidateQueryPlanMutation(
  client: QueryClient,
  projectId: string,
  queryPlanId: string,
  event: QueryPlanEvent,
) {
  const invalidations = [
    client.invalidateQueries({
      queryKey: queryPlanKeys.detail(projectId, queryPlanId),
    }),
  ]
  if (event.action === "generate") {
    invalidations.push(
      client.invalidateQueries({ queryKey: projectKeys.jobs(projectId) }),
    )
  }
  await Promise.all(invalidations)
}

export function useQueryPlanMutation(projectId: string, queryPlanId: string) {
  const client = useQueryClient()
  const mutation = useMutation<unknown, Error, QueryPlanEvent>({
    mutationFn: (event: QueryPlanEvent) =>
      executeQueryPlanEvent(projectId, event),
    onSuccess: (_, event) =>
      invalidateQueryPlanMutation(client, projectId, queryPlanId, event),
  })
  return {
    mutate: mutation.mutate,
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
