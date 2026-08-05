import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { ManuscriptWorkspaceViewModel } from "../model"
import type { ManuscriptWorkspaceRouteView } from "../route-contract"

export type ManuscriptWorkspaceEvent =
  | {
      action: "upload-manuscript"
      input: { file: File; title: string | null }
    }
  | { action: "select-version"; input: { versionId: string } }
  | {
      action: "start-check"
      input: { versionId: string; checks: readonly string[] }
    }
  | { action: "retry-job"; input: { jobId: string } }
  | { action: "cancel-job"; input: { jobId: string; reason: string } }
  | {
      action: "accept-issue"
      input: { issueId: string; lockVersion: number; reason: string | null }
    }
  | {
      action: "reject-issue"
      input: { issueId: string; lockVersion: number; reason: string }
    }
  | {
      action: "create-fix-plan"
      input: { versionId: string; issueIds: readonly string[] }
    }
  | {
      action: "preview-fix-plan"
      input: { planId: string; lockVersion: number }
    }
  | { action: "request-fix-approval"; input: { planId: string } }
  | { action: "execute-fix-plan"; input: { planId: string } }
  | {
      action: "start-revision-audit"
      input: {
        beforeVersionId: string
        afterVersionId: string
      }
    }
  | {
      action: "create-claim"
      input: {
        claimType: string
        text: string
        scope: string | null
        sourceObjectType: string
        sourceObjectId: string
        sourceLocation: Readonly<Record<string, unknown>>
      }
    }
  | {
      action: "update-claim"
      input: {
        claimId: string
        lockVersion: number
        text?: string
        scope?: string | null
        targetStatus?:
          | "NEEDS_EVIDENCE"
          | "SUPPORTED"
          | "CONFLICTED"
          | "INSUFFICIENT"
          | "REJECTED"
      }
    }
  | { action: "request-claim-confirmation"; input: { claimId: string } }
  | { action: "download-version"; input: { versionId: string } }
  | { action: "refresh" }

export type ManuscriptWorkspaceProps = {
  content: Loadable<ManuscriptWorkspaceViewModel>
  pendingAction: ManuscriptWorkspaceEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: ManuscriptWorkspaceEvent) => void
  initialView?: ManuscriptWorkspaceRouteView
  onViewChange?: (view: ManuscriptWorkspaceRouteView) => void
}
