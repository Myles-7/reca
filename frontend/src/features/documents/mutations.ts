import type { QueryClient } from "@tanstack/react-query"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { DocumentsApi, JobsApi } from "@/api/adapter"

import { literatureKeys } from "../literature/queries"
import { mapUiError } from "../projects/mappers"
import type { DocumentWorkspaceViewModel } from "./model"
import { documentKeys } from "./queries"
import type { DocumentEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

export function canExecuteDocumentEvent(
  workspace: DocumentWorkspaceViewModel | null,
  event: DocumentEvent,
): boolean {
  if (!workspace || !workspace.permissionsKnown) return false
  if (event.action === "upload") {
    return workspace.canUpload && event.input.file.size > 0
  }
  if (event.action === "parse") {
    return (
      workspace.document.id === event.input.documentId &&
      workspace.document.knownStatus &&
      workspace.document.permissions.canParse
    )
  }
  return workspace.job?.id === event.input.jobId && workspace.job.canRetry
}

export async function executeDocumentEvent(
  projectId: string,
  event: DocumentEvent,
) {
  if (event.action === "upload") {
    const response = await DocumentsApi.upload(
      projectId,
      event.input.file,
      event.input.documentType,
      event.input.literatureRecordId,
      key(),
    )
    return {
      action: event.action,
      documentId: response.data.document.id,
    } as const
  }
  if (event.action === "parse") {
    const response = await DocumentsApi.parse(
      event.input.documentId,
      {
        allow_fallback: event.input.allowFallback,
        extract_coordinates: event.input.extractCoordinates,
      },
      key(),
    )
    return { action: event.action, jobId: response.data.id } as const
  }
  await JobsApi.retry(event.input.jobId, key())
  return { action: event.action } as const
}

export async function invalidateDocumentMutation(
  client: QueryClient,
  projectId: string,
  documentId: string,
  event: DocumentEvent,
  result: Awaited<ReturnType<typeof executeDocumentEvent>>,
) {
  const invalidations: Promise<unknown>[] = []
  if (event.action === "upload" && result.action === "upload") {
    invalidations.push(
      client.invalidateQueries({
        queryKey: documentKeys.detail(projectId, result.documentId),
      }),
      client.invalidateQueries({
        queryKey: documentKeys.pages(result.documentId),
      }),
    )
    if (event.input.literatureRecordId) {
      invalidations.push(
        client.invalidateQueries({
          queryKey: literatureKeys.records(projectId),
        }),
      )
    }
  }
  if (event.action === "parse" && result.action === "parse") {
    invalidations.push(
      client.invalidateQueries({
        queryKey: documentKeys.detail(projectId, documentId),
      }),
      client.invalidateQueries({ queryKey: documentKeys.pages(documentId) }),
      client.invalidateQueries({ queryKey: documentKeys.job(result.jobId) }),
    )
  }
  if (event.action === "retry-job") {
    invalidations.push(
      client.invalidateQueries({
        queryKey: documentKeys.detail(projectId, documentId),
      }),
      client.invalidateQueries({
        queryKey: documentKeys.job(event.input.jobId),
      }),
    )
  }
  await Promise.all(invalidations)
}

export function useDocumentMutation(
  projectId: string,
  documentId: string,
  onDocumentUploaded?: (documentId: string) => void,
  onParseJobCreated?: (jobId: string) => void,
) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: (event: DocumentEvent) =>
      executeDocumentEvent(projectId, event),
    onSuccess: async (result, event) => {
      await invalidateDocumentMutation(
        client,
        projectId,
        documentId,
        event,
        result,
      )
      if (result.action === "upload") {
        onDocumentUploaded?.(result.documentId)
      }
      if (result.action === "parse") {
        onParseJobCreated?.(result.jobId)
      }
    },
  })
  return {
    mutate: mutation.mutate,
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
