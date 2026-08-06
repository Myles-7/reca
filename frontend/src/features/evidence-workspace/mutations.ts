import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  ApprovalsApi,
  EvidenceGraphApi,
  ExportsApi,
  JobsApi,
} from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import { mapReadiness } from "./mappers"
import type { EvidenceWorkspaceViewModel } from "./model"
import type { EvidenceWorkspaceEvent, ReproPackageInput } from "./ui/contracts"

const key = () => crypto.randomUUID()

function exportInput(input: ReproPackageInput) {
  return {
    include_original_literature_files: input.includeOriginalLiteratureFiles,
    include_dataset_versions: input.includeDatasetVersions,
    include_sensitive_data: input.includeSensitiveData,
    include_agent_logs: input.includeAgentLogs,
    include_model_output_artifacts: input.includeModelOutputArtifacts,
    acknowledge_license_warnings: input.acknowledgeLicenseWarnings,
  }
}

export function canExecuteEvidenceWorkspaceEvent(
  workspace: EvidenceWorkspaceViewModel | null,
  event: EvidenceWorkspaceEvent,
) {
  if (["refresh", "refresh-graph"].includes(event.action)) return true
  if (!workspace?.permissionsKnown) return false
  const capabilities = workspace.capabilities
  switch (event.action) {
    case "create-evidence-link":
      return (
        capabilities.createEvidenceLink.allowed &&
        workspace.selectedClaim?.id === event.input.claimId &&
        workspace.selectedClaim.knownStatus &&
        event.input.evidenceObjectId.length > 0 &&
        event.input.evidenceObjectType.length > 0 &&
        event.input.relationType.length > 0 &&
        event.input.strength.length > 0
      )
    case "confirm-evidence-link":
      return (
        capabilities.confirmEvidenceLink.allowed &&
        workspace.selectedLink?.id === event.linkId &&
        workspace.selectedLink.lockVersion === event.lockVersion &&
        workspace.selectedLink.status === "SUGGESTED"
      )
    case "invalidate-evidence-link":
      return (
        capabilities.invalidateEvidenceLink.allowed &&
        workspace.selectedLink?.id === event.linkId &&
        workspace.selectedLink.lockVersion === event.lockVersion &&
        workspace.selectedLink.status === "ACTIVE" &&
        event.reason.trim().length > 0
      )
    case "run-claim-audit":
      return (
        capabilities.runClaimAudit.allowed &&
        workspace.selectedClaim?.id === event.claimId &&
        workspace.selectedClaim.knownStatus
      )
    case "expand-graph-node":
      return workspace.graph.nodes.some(
        (node) => node.id === event.nodeId && node.knownStatus,
      )
    case "run-export-readiness":
      return capabilities.runExportReadiness.allowed
    case "request-export-confirmation":
      return (
        capabilities.requestExportConfirmation.allowed &&
        workspace.export?.id === event.exportId &&
        workspace.approval?.id === event.approvalId &&
        workspace.approval.status === "PENDING" &&
        !workspace.approval.stale
      )
    case "create-repro-package":
      return capabilities.createReproPackage.allowed
    case "retry-job":
      return (
        capabilities.retryJob.allowed &&
        workspace.job?.id === event.jobId &&
        workspace.job.retryable
      )
    case "cancel-job":
      return (
        capabilities.cancelJob.allowed &&
        workspace.job?.id === event.jobId &&
        event.reason.trim().length > 0
      )
    case "download-repro-package":
      return (
        capabilities.downloadReproPackage.allowed &&
        workspace.package?.id === event.packageId &&
        !workspace.package.tampered
      )
  }
}

async function execute(
  projectId: string,
  workspace: EvidenceWorkspaceViewModel,
  event: EvidenceWorkspaceEvent,
) {
  switch (event.action) {
    case "create-evidence-link":
      return EvidenceGraphApi.createLink(
        event.input.claimId,
        {
          evidence_object_type: event.input.evidenceObjectType as never,
          evidence_object_id: event.input.evidenceObjectId,
          relation_type: event.input.relationType as never,
          strength: event.input.strength as never,
          explanation: event.input.explanation,
          suggestion: event.input.suggestion ?? false,
        },
        key(),
      )
    case "confirm-evidence-link":
      return EvidenceGraphApi.transitionLink(
        event.linkId,
        event.lockVersion,
        { status: "ACTIVE" },
        key(),
      )
    case "invalidate-evidence-link":
      return EvidenceGraphApi.transitionLink(
        event.linkId,
        event.lockVersion,
        { status: "INVALIDATED", reason: event.reason },
        key(),
      )
    case "run-claim-audit":
      return EvidenceGraphApi.createAudit(
        event.claimId,
        { request_ai_explanation: event.requestAiExplanation },
        key(),
      )
    case "run-export-readiness":
      return ExportsApi.readiness(projectId, exportInput(event.input), key())
    case "request-export-confirmation":
      return ApprovalsApi.approve(
        event.approvalId,
        {
          decision_reason: "Export readiness warnings reviewed and accepted.",
          item_decisions:
            workspace.approval?.items.map((item) => ({
              item_type: item.itemType,
              item_id: item.itemId,
              decision: "ACCEPT",
              reason: "Reviewed in the Evidence Workspace.",
            })) ?? [],
        },
        key(),
      )
    case "create-repro-package":
      return ExportsApi.createReproPackage(
        projectId,
        exportInput(event.input),
        key(),
      )
    case "retry-job":
      return JobsApi.retry(event.jobId, key())
    case "cancel-job":
      return JobsApi.cancel(event.jobId, event.reason, key())
    case "download-repro-package":
      return ExportsApi.download(event.packageId)
    case "expand-graph-node":
    case "refresh-graph":
    case "refresh":
      return null
  }
}

export function useEvidenceWorkspaceMutation(
  projectId: string,
  workspace: EvidenceWorkspaceViewModel | null,
  onSuccess?: (event: EvidenceWorkspaceEvent, result: unknown) => void,
) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: async (event: EvidenceWorkspaceEvent) => {
      if (!canExecuteEvidenceWorkspaceEvent(workspace, event))
        throw new Error("The event is not allowed by current server facts.")
      if (!workspace)
        throw new Error("The server workspace projection is unavailable.")
      return { event, result: await execute(projectId, workspace, event) }
    },
    onSuccess: async ({ event, result }) => {
      await client.invalidateQueries({
        queryKey: ["projects", projectId, "evidence-workspace"],
      })
      if (event.action === "run-export-readiness" && result) {
        const envelope = result as Awaited<
          ReturnType<typeof ExportsApi.readiness>
        >
        client.setQueriesData<EvidenceWorkspaceViewModel>(
          { queryKey: ["projects", projectId, "evidence-workspace"] },
          (current) =>
            current
              ? { ...current, readiness: mapReadiness(envelope.data) }
              : current,
        )
      }
      onSuccess?.(event, result)
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
