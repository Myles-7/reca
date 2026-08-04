import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { CleaningActionInput, DataWorkspaceViewModel } from "../model"
import type { DataWorkspaceRouteView } from "../route-contract"

export type DataWorkspaceEvent =
  | { action: "upload-dataset"; input: { file: File; name: string } }
  | {
      action: "select-worksheet"
      input: {
        versionId: string
        worksheetName: string
        acknowledgeHidden: boolean
      }
    }
  | {
      action: "update-dataset-identity"
      input: {
        datasetId: string
        lockVersion: number
        changes: {
          name?: string
          description?: string | null
          publisher?: string | null
          licenseName?: string | null
        }
      }
    }
  | {
      action: "update-column"
      input: {
        columnId: string
        lockVersion: number
        changes: {
          displayName?: string | null
          confirmedType?: string | null
          semanticRole?: string | null
          unit?: string | null
          isSensitive?: boolean
          confirmationStatus?: "UNCONFIRMED" | "CONFIRMED"
        }
      }
    }
  | {
      action: "select-version"
      input: { datasetId: string; versionId: string }
    }
  | {
      action: "compare-versions"
      input: {
        datasetId: string
        baseVersionId: string
        targetVersionId: string
      }
    }
  | { action: "run-quality"; input: { versionId: string } }
  | { action: "acknowledge-issue"; input: { issueId: string } }
  | { action: "ignore-issue"; input: { issueId: string; reason: string } }
  | {
      action: "create-plan"
      input: {
        versionId: string
        title: string
        rationale: string | null
        actions: readonly CleaningActionInput[]
      }
    }
  | {
      action: "update-plan"
      input: {
        planId: string
        lockVersion: number
        title?: string
        rationale?: string | null
        actions?: readonly CleaningActionInput[]
      }
    }
  | { action: "preview-plan"; input: { planId: string } }
  | { action: "request-approval"; input: { planId: string } }
  | { action: "execute-plan"; input: { planId: string } }
  | { action: "retry-job"; input: { jobId: string } }

export type DataWorkspaceWorkspaceProps = {
  content: Loadable<DataWorkspaceViewModel>
  pendingAction: DataWorkspaceEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: DataWorkspaceEvent) => void
  initialView?: DataWorkspaceRouteView
  onViewChange?: (view: DataWorkspaceRouteView) => void
}
