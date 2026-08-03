import type { ComponentType } from "react"

import { mapUiError } from "../../projects/mappers"
import type { Loadable } from "../../projects/model"
import type { DocumentWorkspaceViewModel } from "../model"
import { canExecuteDocumentEvent, useDocumentMutation } from "../mutations"
import { useDocumentQuery } from "../queries"
import type { DocumentWorkspaceProps } from "../ui/contracts"

export function DocumentContainer({
  projectId,
  documentId,
  jobId,
  View,
  onDocumentUploaded,
  onParseJobCreated,
}: {
  projectId: string
  documentId: string
  jobId?: string
  View: ComponentType<DocumentWorkspaceProps>
  onDocumentUploaded?: (documentId: string) => void
  onParseJobCreated?: (jobId: string) => void
}) {
  const query = useDocumentQuery(projectId, documentId, jobId)
  const mutation = useDocumentMutation(
    projectId,
    documentId,
    onDocumentUploaded,
    onParseJobCreated,
  )
  const content: Loadable<DocumentWorkspaceViewModel> = query.data
    ? { state: "ready", data: query.data }
    : query.isLoading
      ? { state: "loading", label: "Loading document" }
      : { state: "error", error: mapUiError(query.error) }
  return (
    <View
      content={content}
      pendingAction={mutation.pendingAction}
      mutationError={mutation.uiError}
      onRetry={() => void query.refetch()}
      onEvent={(event) => {
        if (canExecuteDocumentEvent(query.data ?? null, event)) {
          mutation.mutate(event)
        }
      }}
    />
  )
}
