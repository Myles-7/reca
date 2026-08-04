import type { LiteratureMatrixQuery } from "@/api/adapter"

import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { EvidenceMatrixViewModel } from "../model"
import {
  canExecuteEvidenceMatrixEvent,
  useEvidenceMatrixMutation,
} from "../mutations"
import {
  useEvidenceDocumentQuery,
  useEvidenceMatrixQuery,
  useEvidenceSpanQuery,
} from "../queries"
import type {
  EvidenceMatrixEvent,
  EvidenceMatrixWorkspaceProps,
} from "../ui/contracts"

export function EvidenceMatrixContainer({
  projectId,
  extractionId,
  documentId,
  evidenceSpanId,
  fieldId,
  matrixQuery = {},
  View,
  onNavigate,
  onQueryChange,
}: {
  projectId: string
  extractionId?: string
  documentId?: string
  evidenceSpanId?: string
  fieldId?: string
  matrixQuery?: LiteratureMatrixQuery
  View: (props: EvidenceMatrixWorkspaceProps) => React.ReactNode
  onNavigate?: (
    input: Extract<
      EvidenceMatrixEvent,
      { action: "open-pdf-location" }
    >["input"],
  ) => void
  onQueryChange?: (
    event: Extract<EvidenceMatrixEvent, { action: "filter" | "sort" }>,
  ) => void
}) {
  const query = useEvidenceMatrixQuery(projectId, matrixQuery, extractionId)
  const spanQuery = useEvidenceSpanQuery(projectId, evidenceSpanId)
  const selectedSpan = spanQuery.data ?? null
  const resolvedDocumentId = selectedSpan?.documentId ?? documentId
  const documentMatchesSpan =
    !documentId || !selectedSpan || documentId === selectedSpan.documentId
  const documentQuery = useEvidenceDocumentQuery(
    projectId,
    documentMatchesSpan ? resolvedDocumentId : undefined,
    selectedSpan?.pageNumber,
  )
  const mutation = useEvidenceMatrixMutation(projectId)
  const coreError = query.error ?? spanQuery.error ?? documentQuery.error
  const content: Loadable<EvidenceMatrixViewModel> = coreError
    ? { state: "error", error: mapUiError(coreError) }
    : query.data
      ? { state: "ready", data: query.data }
      : query.isLoading
        ? { state: "loading", label: "Loading evidence matrix" }
        : {
            state: "empty",
            message: "No literature is available for the matrix.",
          }
  const pdfViewer =
    documentMatchesSpan && resolvedDocumentId
      ? {
          documentId: resolvedDocumentId,
          authorizedPdfUrl: documentQuery.download?.download_url ?? null,
          selectedPage: selectedSpan?.pageNumber ?? 1,
          selectedSpan,
          pageText: documentQuery.page?.text_content ?? null,
          parserType:
            documentQuery.document?.parser_type ??
            selectedSpan?.parserType ??
            null,
          hasTextLayer:
            documentQuery.document?.parser_type !== "PYPDF" &&
            Boolean(documentQuery.page?.text_content),
          degradedReason: !documentQuery.download?.download_url
            ? documentQuery.isLoading
              ? "The authorized PDF is loading."
              : "The authorized PDF is unavailable; server page text remains available."
            : documentQuery.document?.parser_type === "PYPDF"
              ? "pypdf provides degraded text without trusted coordinates."
              : selectedSpan && !selectedSpan.hasCoordinates
                ? "Trusted coordinates are unavailable; showing page and text context only."
                : null,
        }
      : null
  return (
    <View
      content={content}
      pdfViewer={pdfViewer}
      selectedFieldId={fieldId}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (event.action === "open-pdf-location") {
          onNavigate?.(event.input)
          return
        }
        if (event.action === "filter" || event.action === "sort") {
          onQueryChange?.(event)
          return
        }
        if (
          canExecuteEvidenceMatrixEvent(query.data ?? null, event, selectedSpan)
        ) {
          mutation.mutate(event)
        }
      }}
    />
  )
}
