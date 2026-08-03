import { createFileRoute } from "@tanstack/react-router"

import { ResearchQuestionContainer } from "@/features/research-question/containers/ResearchQuestionContainer"

export const Route = createFileRoute(
  "/_layout/projects/$projectId_/research-question",
)({
  component: ResearchQuestionRoute,
  head: () => ({ meta: [{ title: "Research question - RECA" }] }),
})

function ResearchQuestionRoute() {
  const { projectId } = Route.useParams()
  return <ResearchQuestionContainer projectId={projectId} />
}
