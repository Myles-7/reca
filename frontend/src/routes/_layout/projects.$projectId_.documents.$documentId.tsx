import { createFileRoute } from "@tanstack/react-router"

import { DocumentContainer } from "@/features/documents/containers/DocumentContainer"
import { DocumentWorkspace } from "@/features/documents/ui/DocumentWorkspace"

export const Route = createFileRoute(
  "/_layout/projects/$projectId_/documents/$documentId",
)({
  validateSearch: (search: Record<string, unknown>) => ({
    jobId:
      typeof search.jobId === "string" && search.jobId.trim()
        ? search.jobId
        : undefined,
  }),
  component: DocumentRoute,
  head: () => ({ meta: [{ title: "Document - RECA" }] }),
})

function DocumentRoute() {
  const { projectId, documentId } = Route.useParams()
  const { jobId } = Route.useSearch()
  const navigate = Route.useNavigate()
  return (
    <DocumentContainer
      projectId={projectId}
      documentId={documentId}
      jobId={jobId}
      View={DocumentWorkspace}
      onDocumentUploaded={(nextDocumentId) =>
        void navigate({
          to: "/projects/$projectId/documents/$documentId",
          params: { projectId, documentId: nextDocumentId },
          search: { jobId: undefined },
        })
      }
      onParseJobCreated={(nextJobId) =>
        void navigate({ search: { jobId: nextJobId } })
      }
    />
  )
}
