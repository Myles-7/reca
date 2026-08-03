import { useQuery } from "@tanstack/react-query"

import { ApiError, type QueryPlanEnvelope, QueryPlansApi } from "@/api/adapter"

import { mapQueryPlan } from "./mappers"

export const queryPlanKeys = {
  detail: (projectId: string, queryPlanId: string) =>
    ["projects", projectId, "query-plans", queryPlanId] as const,
}

export async function loadQueryPlan(
  queryPlanId: string,
  get: (id: string) => Promise<QueryPlanEnvelope> = QueryPlansApi.get,
) {
  return mapQueryPlan((await get(queryPlanId)).data)
}

export function useQueryPlanQuery(projectId: string, queryPlanId: string) {
  return useQuery({
    queryKey: queryPlanKeys.detail(projectId, queryPlanId),
    queryFn: () => loadQueryPlan(queryPlanId),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
        return false
      }
      return failureCount < 2
    },
  })
}
