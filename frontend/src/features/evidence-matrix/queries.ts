import { useQuery } from "@tanstack/react-query"

import {
  ApiError,
  ArtifactsApi,
  DocumentsApi,
  EvidenceApi,
  type LiteratureMatrixQuery,
} from "@/api/adapter"

import { mapEvidenceLocation, mapEvidenceMatrix } from "./mappers"

export const evidenceMatrixKeys = {
  matrix: (projectId: string, query: LiteratureMatrixQuery) =>
    ["projects", projectId, "evidence-matrix", query] as const,
  span: (spanId: string) => ["evidence-spans", spanId] as const,
  extraction: (extractionId: string) =>
    ["literature-extractions", extractionId] as const,
  document: (projectId: string, documentId: string) =>
    ["projects", projectId, "evidence-documents", documentId] as const,
  page: (documentId: string, pageNumber: number) =>
    ["documents", documentId, "evidence-page", pageNumber] as const,
  download: (artifactId: string) =>
    ["artifacts", artifactId, "evidence-download"] as const,
}

const retry = (count: number, error: Error) =>
  !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
  count < 2

function routeMismatch(message: string, code: string) {
  return new ApiError(404, "NOT_FOUND", message, code)
}

export function useEvidenceMatrixQuery(
  projectId: string,
  query: LiteratureMatrixQuery = {},
  extractionId?: string,
) {
  const matrix = useQuery({
    queryKey: evidenceMatrixKeys.matrix(projectId, query),
    queryFn: () => EvidenceApi.matrix(projectId, query),
    retry,
  })
  const extraction = useQuery({
    queryKey: evidenceMatrixKeys.extraction(extractionId ?? "none"),
    queryFn: async () => {
      const response = await EvidenceApi.extraction(extractionId!)
      if (response.data.project_id !== projectId) {
        throw routeMismatch(
          "The extraction projection does not match this project route.",
          "EXTRACTION_ROUTE_MISMATCH",
        )
      }
      return response.data
    },
    enabled: Boolean(extractionId),
    retry,
  })
  const error = matrix.error ?? extraction.error
  return {
    data:
      matrix.data && !error
        ? mapEvidenceMatrix(
            matrix.data,
            extraction.data ? [extraction.data] : [],
          )
        : undefined,
    error,
    isLoading:
      matrix.isLoading || (Boolean(extractionId) && extraction.isLoading),
    isError: Boolean(error),
    refetch: async () => {
      await Promise.all([
        matrix.refetch(),
        ...(extractionId ? [extraction.refetch()] : []),
      ])
    },
  }
}

export function useEvidenceSpanQuery(
  projectId: string,
  evidenceSpanId?: string,
) {
  return useQuery({
    queryKey: evidenceMatrixKeys.span(evidenceSpanId ?? "none"),
    queryFn: async () => {
      const response = await EvidenceApi.span(evidenceSpanId!)
      if (response.data.project_id !== projectId) {
        throw routeMismatch(
          "The EvidenceSpan projection does not match this project route.",
          "EVIDENCE_SPAN_ROUTE_MISMATCH",
        )
      }
      return mapEvidenceLocation(response.data)
    },
    enabled: Boolean(evidenceSpanId),
    retry,
  })
}

export function useEvidenceDocumentQuery(
  projectId: string,
  documentId?: string,
  pageNumber?: number,
) {
  const document = useQuery({
    queryKey: evidenceMatrixKeys.document(projectId, documentId ?? "none"),
    queryFn: async () => {
      const response = await DocumentsApi.get(documentId!)
      if (
        response.data.id !== documentId ||
        response.data.project_id !== projectId
      ) {
        throw routeMismatch(
          "The Document projection does not match this project route.",
          "DOCUMENT_ROUTE_MISMATCH",
        )
      }
      return response.data
    },
    enabled: Boolean(documentId),
    retry,
  })
  const page = useQuery({
    queryKey: evidenceMatrixKeys.page(documentId ?? "none", pageNumber ?? 0),
    queryFn: async () => {
      const response = await DocumentsApi.getPage(documentId!, pageNumber!)
      if (
        response.data.project_id !== projectId ||
        response.data.document_id !== documentId ||
        response.data.page_number !== pageNumber
      ) {
        throw routeMismatch(
          "The DocumentPage projection does not match this evidence route.",
          "DOCUMENT_PAGE_ROUTE_MISMATCH",
        )
      }
      return response.data
    },
    enabled: Boolean(documentId && pageNumber),
    retry,
  })
  const artifactId = document.data?.artifact_id
  const download = useQuery({
    queryKey: evidenceMatrixKeys.download(artifactId ?? "none"),
    queryFn: async () => {
      const response = await ArtifactsApi.download(artifactId!)
      if (response.data.artifact_id !== artifactId) {
        throw routeMismatch(
          "The authorized Artifact projection does not match this Document.",
          "ARTIFACT_ROUTE_MISMATCH",
        )
      }
      return response.data
    },
    enabled: Boolean(artifactId),
    retry,
  })
  return {
    document: document.data,
    page: page.data,
    download: download.data,
    error: document.error ?? page.error ?? download.error,
    isLoading:
      Boolean(documentId) &&
      (document.isLoading ||
        (Boolean(pageNumber) && page.isLoading) ||
        (Boolean(artifactId) && download.isLoading)),
  }
}
