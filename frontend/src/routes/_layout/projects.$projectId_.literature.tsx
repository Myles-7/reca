import { createFileRoute } from "@tanstack/react-router"

import { LiteratureContainer } from "@/features/literature/containers/LiteratureContainer"
import { M3LiteratureWorkspacePage } from "@/features/literature/M3LiteratureWorkspacePage"
import { parseM3LiteratureSearch } from "@/features/literature/m3-route-contract"
import { LiteratureWorkspace } from "@/features/literature/ui/LiteratureWorkspace"

export const Route = createFileRoute(
  "/_layout/projects/$projectId_/literature",
)({
  validateSearch: (search: Record<string, unknown>) => ({
    ...parseM3LiteratureSearch(search),
    searchRunId:
      typeof search.searchRunId === "string" && search.searchRunId.trim()
        ? search.searchRunId
        : undefined,
  }),
  component: LiteratureRoute,
  head: () => ({ meta: [{ title: "Literature Evidence - RECA" }] }),
})

function LiteratureRoute() {
  const { projectId } = Route.useParams()
  const search = Route.useSearch()
  const navigate = Route.useNavigate()
  if (!search.view) {
    return (
      <LiteratureContainer
        projectId={projectId}
        searchRunId={search.searchRunId}
        View={LiteratureWorkspace}
        onSearchRunCreated={(nextSearchRunId) =>
          void navigate({
            search: { searchRunId: nextSearchRunId },
          })
        }
      />
    )
  }
  return (
    <M3LiteratureWorkspacePage
      projectId={projectId}
      search={search}
      onSearchChange={(next) =>
        void navigate({
          search: (previous) => ({
            ...previous,
            ...next,
            searchRunId: undefined,
          }),
        })
      }
    />
  )
}
