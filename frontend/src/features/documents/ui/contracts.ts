import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { DocumentWorkspaceViewModel } from "../model"

export type DocumentEvent =
  | {
      action: "upload"
      input: {
        file: File
        documentType: "SCHOLARLY_PDF" | "MANUSCRIPT" | "OTHER"
        literatureRecordId: string | null
      }
    }
  | {
      action: "parse"
      input: {
        documentId: string
        allowFallback: boolean
        extractCoordinates: boolean
      }
    }
  | { action: "retry-job"; input: { jobId: string } }

export type DocumentWorkspaceProps = {
  content: Loadable<DocumentWorkspaceViewModel>
  pendingAction: DocumentEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: DocumentEvent) => void
}
