import type {
  EvidenceWorkspaceContent,
  EvidenceWorkspaceMutationError,
  EvidenceWorkspaceView,
} from "../model"

export type EvidenceLinkInput = {
  claimId: string
  evidenceObjectType: string
  evidenceObjectId: string
  relationType: string
  strength: string
  explanation?: string
  suggestion?: boolean
}

export type ReproPackageInput = {
  includeOriginalLiteratureFiles: boolean
  includeDatasetVersions: boolean
  includeSensitiveData: boolean
  includeAgentLogs: boolean
  includeModelOutputArtifacts: boolean
  acknowledgeLicenseWarnings: boolean
}

export type EvidenceWorkspaceEvent =
  | { action: "create-evidence-link"; input: EvidenceLinkInput }
  | { action: "confirm-evidence-link"; linkId: string; lockVersion: number }
  | {
      action: "invalidate-evidence-link"
      linkId: string
      lockVersion: number
      reason: string
    }
  | {
      action: "run-claim-audit"
      claimId: string
      requestAiExplanation: boolean
    }
  | { action: "expand-graph-node"; nodeId: string }
  | { action: "refresh-graph" }
  | { action: "run-export-readiness"; input: ReproPackageInput }
  | {
      action: "request-export-confirmation"
      exportId: string
      approvalId: string
    }
  | { action: "create-repro-package"; input: ReproPackageInput }
  | { action: "retry-job"; jobId: string }
  | { action: "cancel-job"; jobId: string; reason: string }
  | { action: "download-repro-package"; packageId: string }
  | { action: "refresh" }

export type EvidenceWorkspaceProps = {
  content: EvidenceWorkspaceContent
  pendingAction: EvidenceWorkspaceEvent["action"] | null
  mutationError: EvidenceWorkspaceMutationError
  initialView?: EvidenceWorkspaceView
  onViewChange?: (view: EvidenceWorkspaceView) => void
  onRetry: () => void
  onEvent: (event: EvidenceWorkspaceEvent) => void
}

/** @deprecated Use EvidenceWorkspaceProps. */
export type EvidenceWorkspaceWorkspaceProps = EvidenceWorkspaceProps
