import { createFileRoute } from "@tanstack/react-router"

import { QueryPlanContainer } from "@/features/query-plan/containers/QueryPlanContainer"
import { QueryPlanWorkspace } from "@/features/query-plan/ui/QueryPlanWorkspace"

export const Route = createFileRoute(
  "/_layout/projects/$projectId_/query-plans/$queryPlanId",
)({
  component: QueryPlanRoute,
  head: () => ({ meta: [{ title: "Query plan - RECA" }] }),
})

function QueryPlanRoute() {
  const { projectId, queryPlanId } = Route.useParams()
  return (
    <QueryPlanContainer
      projectId={projectId}
      queryPlanId={queryPlanId}
      View={QueryPlanWorkspace}
    />
  )
}
