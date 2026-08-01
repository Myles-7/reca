import { createFileRoute } from "@tanstack/react-router"

import { ProjectWorkspacePage } from "@/features/projects/ProjectWorkspacePage"

export const Route = createFileRoute("/_layout/projects/$projectId")({
  component: ProjectRoute,
  head: () => ({ meta: [{ title: "Project workspace - RECA" }] }),
})

function ProjectRoute() {
  const { projectId } = Route.useParams()
  return <ProjectWorkspacePage projectId={projectId} />
}
