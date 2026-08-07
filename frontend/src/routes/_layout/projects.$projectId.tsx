import { createFileRoute } from "@tanstack/react-router"

import { ProjectWorkspacePage } from "@/features/projects/ProjectWorkspacePage"

type ProjectWorkspaceSearch = {
  tab?: "approvals"
  approval?: string
}

function parseProjectWorkspaceSearch(
  search: Record<string, unknown>,
): ProjectWorkspaceSearch {
  const result: ProjectWorkspaceSearch = {}
  if (search.tab === "approvals") result.tab = "approvals"
  if (
    typeof search.approval === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      search.approval,
    )
  )
    result.approval = search.approval
  return result
}

export const Route = createFileRoute("/_layout/projects/$projectId")({
  validateSearch: parseProjectWorkspaceSearch,
  component: ProjectRoute,
  head: () => ({ meta: [{ title: "Project workspace - RECA" }] }),
})

function ProjectRoute() {
  const { projectId } = Route.useParams()
  const search = Route.useSearch()
  return <ProjectWorkspacePage projectId={projectId} initialTab={search.tab} />
}
