import type { ComponentType } from "react"

import { mapUiError } from "../../projects/mappers"
import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { QueryPlanViewModel } from "../model"
import { canExecuteQueryPlanEvent, useQueryPlanMutation } from "../mutations"
import { useQueryPlanQuery } from "../queries"
import type { QueryPlanWorkspaceProps } from "../ui/contracts"

export function QueryPlanContainer({
  projectId,
  queryPlanId,
  View,
}: {
  projectId: string
  queryPlanId: string
  View: ComponentType<QueryPlanWorkspaceProps>
}) {
  const query = useQueryPlanQuery(projectId, queryPlanId)
  const mutation = useQueryPlanMutation(projectId, queryPlanId)
  const planMatchesRoute =
    query.data?.projectId === projectId && query.data.id === queryPlanId
  const routeMismatchError: UiErrorViewModel = {
    title: "Query plan unavailable",
    message: "The query plan projection does not match this project route.",
    code: "QUERY_PLAN_ROUTE_MISMATCH",
    requestId: null,
    retryable: false,
    forbidden: false,
    notFound: true,
    conflict: false,
  }
  const plan: QueryPlanViewModel | null =
    planMatchesRoute && query.data ? query.data : null
  const content: Loadable<QueryPlanViewModel> = plan
    ? { state: "ready", data: plan }
    : query.data
      ? { state: "error", error: routeMismatchError }
      : query.isLoading
        ? { state: "loading", label: "Loading query plan" }
        : { state: "error", error: mapUiError(query.error) }
  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (canExecuteQueryPlanEvent(plan, event)) {
          mutation.mutate(event)
        }
      }}
    />
  )
}
