import { useQuery } from "@tanstack/react-query"
import { useEffect } from "react"

import {
  ApiError,
  type DocumentEnvelope,
  type DocumentPageListEnvelope,
  DocumentsApi,
  JobsApi,
  ProjectsApi,
} from "@/api/adapter"

import { mapDocument, mapDocumentJob, mapDocumentPage } from "./mappers"

export const documentKeys = {
  detail: (projectId: string, documentId: string) =>
    ["projects", projectId, "documents", documentId] as const,
  pages: (documentId: string) => ["documents", documentId, "pages"] as const,
  job: (jobId: string) => ["jobs", jobId] as const,
  retryPermission: (projectId: string) =>
    ["projects", projectId, "documents", "retry-permission"] as const,
}

const retry = (failureCount: number, error: Error) => {
  if (error instanceof ApiError && [401, 403, 404].includes(error.status)) {
    return false
  }
  return failureCount < 2
}

function routeMismatch(message: string) {
  return new ApiError(404, "NOT_FOUND", message, "DOCUMENT_ROUTE_MISMATCH")
}

function validateDocumentRoute(
  projectId: string,
  documentId: string,
  envelope: DocumentEnvelope,
) {
  if (
    envelope.data.id !== documentId ||
    envelope.data.project_id !== projectId
  ) {
    throw routeMismatch(
      "The Document projection does not match this project route.",
    )
  }
  return envelope
}

function validatePageRoute(
  projectId: string,
  documentId: string,
  envelope: DocumentPageListEnvelope,
) {
  if (
    envelope.data.some(
      (page) =>
        page.project_id !== projectId || page.document_id !== documentId,
    )
  ) {
    throw routeMismatch(
      "The DocumentPage projection does not match this Document route.",
    )
  }
  return envelope
}

function validateJobRoute(
  projectId: string,
  documentId: string,
  jobId: string,
  envelope: Awaited<ReturnType<typeof JobsApi.get>>,
) {
  const value = envelope.data
  if (
    value.id !== jobId ||
    value.project_id !== projectId ||
    value.resource_type !== "document" ||
    value.resource_id !== documentId
  ) {
    throw routeMismatch(
      "The Job projection does not match this Document route.",
    )
  }
  return envelope
}

const activeStatuses = new Set(["QUEUED", "RUNNING", "CANCEL_REQUESTED"])

export function useDocumentQuery(
  projectId: string,
  documentId: string,
  jobId?: string,
) {
  const document = useQuery({
    queryKey: documentKeys.detail(projectId, documentId),
    queryFn: async () =>
      validateDocumentRoute(
        projectId,
        documentId,
        await DocumentsApi.get(documentId),
      ),
    retry,
    refetchInterval: (query) =>
      activeStatuses.has(query.state.data?.data.parse_status ?? "")
        ? 1500
        : false,
  })
  const pages = useQuery({
    queryKey: documentKeys.pages(documentId),
    queryFn: async () =>
      validatePageRoute(
        projectId,
        documentId,
        await DocumentsApi.listPages(documentId),
      ),
    retry,
    refetchInterval: activeStatuses.has(document.data?.data.parse_status ?? "")
      ? 1500
      : false,
  })
  const job = useQuery({
    queryKey: documentKeys.job(jobId ?? "none"),
    queryFn: async () =>
      validateJobRoute(
        projectId,
        documentId,
        jobId!,
        await JobsApi.get(jobId!),
      ),
    enabled: Boolean(jobId),
    retry,
    refetchInterval: (query) =>
      activeStatuses.has(query.state.data?.data.status ?? "") ? 1500 : false,
  })
  const project = useQuery({
    queryKey: documentKeys.retryPermission(projectId),
    queryFn: () => ProjectsApi.get(projectId),
    retry,
  })

  useEffect(() => {
    if (job.data && activeStatuses.has(job.data.data.status)) {
      void document.refetch()
    }
    if (
      document.data?.data.parse_status === "COMPLETED" ||
      job.data?.data.status === "COMPLETED"
    ) {
      void pages.refetch()
    }
  }, [
    document.data?.data.parse_status,
    job.data?.data.status,
    job.data?.data.progress_percent,
  ])

  const coreLoading = document.isLoading || pages.isLoading
  const coreError = document.error ?? pages.error
  const data = document.data
    ? {
        document: mapDocument(document.data.data),
        pages: pages.data?.data.map(mapDocumentPage) ?? [],
        job: job.data
          ? mapDocumentJob(
              job.data.data,
              document.data.data,
              project.data?.data ?? null,
            )
          : null,
        permissionsKnown: Array.isArray(document.data.data.allowed_actions),
        canUpload:
          Array.isArray(document.data.data.allowed_actions) &&
          document.data.data.allowed_actions.includes("document.upload"),
      }
    : undefined

  return {
    data: coreLoading || coreError ? undefined : data,
    error: coreError,
    isLoading: coreLoading,
    refetch: async () => {
      const reloads: Promise<unknown>[] = [
        document.refetch(),
        pages.refetch(),
        project.refetch(),
      ]
      if (jobId) reloads.push(job.refetch())
      await Promise.all(reloads)
    },
  }
}
