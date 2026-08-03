import { createFileRoute } from "@tanstack/react-router"

import { LiteratureContainer } from "@/features/literature/containers/LiteratureContainer"
import { LiteratureWorkspace } from "@/features/literature/ui/LiteratureWorkspace"

export const Route = createFileRoute(
  "/_layout/projects/$projectId_/literature",
)({
  validateSearch: (search: Record<string, unknown>) => ({
    searchRunId:
      typeof search.searchRunId === "string" && search.searchRunId.trim()
        ? search.searchRunId
        : undefined,
  }),
  component: LiteratureRoute,
  head: () => ({ meta: [{ title: "Literature - RECA" }] }),
})

function LiteratureRoute() {
  const { projectId } = Route.useParams()
  const { searchRunId } = Route.useSearch()
  const navigate = Route.useNavigate()
  return (
    <LiteratureContainer
      projectId={projectId}
      searchRunId={searchRunId}
      View={LiteratureWorkspace}
      onSearchRunCreated={(nextSearchRunId) =>
        void navigate({ search: { searchRunId: nextSearchRunId } })
      }
    />
  )
}
