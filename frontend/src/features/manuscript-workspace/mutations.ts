import { useMutation, useQueryClient } from "@tanstack/react-query"

import { ArtifactsApi, JobsApi, ManuscriptsApi } from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import type { ManuscriptWorkspaceViewModel } from "./model"
import type { ManuscriptWorkspaceEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

export function canExecuteManuscriptWorkspaceEvent(
  workspace: ManuscriptWorkspaceViewModel | null,
  event: ManuscriptWorkspaceEvent,
) {
  if (event.action === "refresh") return true
  if (!workspace?.permissionsKnown) return false
  const c = workspace.capabilities
  switch (event.action) {
    case "upload-manuscript":
      return (
        c.uploadManuscript.allowed &&
        event.input.file.size > 0 &&
        event.input.file.name.toLowerCase().endsWith(".docx")
      )
    case "select-version":
      return workspace.versions.some(
        (version) =>
          version.id === event.input.versionId && version.knownStatus,
      )
    case "start-check":
      return (
        c.startCheck.allowed &&
        workspace.selectedVersion?.id === event.input.versionId &&
        workspace.selectedVersion.sourceHash.length === 64 &&
        event.input.checks.length > 0 &&
        event.input.checks.every((check) =>
          workspace.checkDefinitions.some(
            (definition) => definition.value === check && definition.allowed,
          ),
        )
      )
    case "retry-job":
      return (
        c.retryJob.allowed &&
        workspace.job?.id === event.input.jobId &&
        workspace.job.retryable
      )
    case "cancel-job":
      return (
        c.cancelJob.allowed &&
        workspace.job?.id === event.input.jobId &&
        event.input.reason.trim().length > 0
      )
    case "accept-issue":
      return (
        c.acceptIssue.allowed &&
        workspace.selectedIssue?.id === event.input.issueId &&
        workspace.selectedIssue.lockVersion === event.input.lockVersion
      )
    case "reject-issue":
      return (
        c.rejectIssue.allowed &&
        workspace.selectedIssue?.id === event.input.issueId &&
        workspace.selectedIssue.lockVersion === event.input.lockVersion &&
        event.input.reason.trim().length > 0
      )
    case "create-fix-plan": {
      const selected = workspace.issues.filter((issue) =>
        event.input.issueIds.includes(issue.id),
      )
      return (
        c.createFixPlan.allowed &&
        workspace.selectedVersion?.id === event.input.versionId &&
        selected.length === event.input.issueIds.length &&
        selected.every(
          (issue) =>
            issue.knownStatus &&
            issue.status === "ACCEPTED" &&
            issue.autoFixable &&
            !issue.highRisk,
        )
      )
    }
    case "preview-fix-plan":
      return (
        c.previewFixPlan.allowed &&
        workspace.transformation?.id === event.input.planId &&
        workspace.transformation.lockVersion === event.input.lockVersion &&
        workspace.transformation.inputArtifactHash ===
          workspace.selectedVersion?.sourceHash
      )
    case "request-fix-approval":
      return (
        c.requestFixApproval.allowed &&
        workspace.transformation?.id === event.input.planId &&
        Boolean(workspace.transformation.previewHash)
      )
    case "execute-fix-plan":
      return (
        c.executeFixPlan.allowed &&
        workspace.transformation?.id === event.input.planId &&
        workspace.transformation.approvalStatus === "APPROVED" &&
        !workspace.transformation.approvalStale &&
        workspace.transformation.inputArtifactHash ===
          workspace.selectedVersion?.sourceHash
      )
    case "start-revision-audit":
      return (
        c.startRevisionAudit.allowed &&
        event.input.beforeVersionId !== event.input.afterVersionId &&
        workspace.versions.some(
          (v) =>
            v.id === event.input.beforeVersionId &&
            v.knownStatus &&
            v.status === "AVAILABLE",
        ) &&
        workspace.versions.some(
          (v) =>
            v.id === event.input.afterVersionId &&
            v.knownStatus &&
            v.status === "AVAILABLE",
        ) &&
        workspace.revisionReferences.some(
          (option) =>
            option.value === event.input.beforeVersionId && option.allowed,
        ) &&
        workspace.revisionReferences.some(
          (option) =>
            option.value === event.input.afterVersionId && option.allowed,
        )
      )
    case "create-claim":
      return (
        c.createClaim.allowed &&
        workspace.claimTypeDefinitions.some(
          (option) => option.value === event.input.claimType && option.allowed,
        ) &&
        event.input.text.trim().length > 0 &&
        event.input.sourceObjectId.length > 0 &&
        Object.keys(event.input.sourceLocation).length > 0
      )
    case "update-claim":
      return (
        c.updateClaim.allowed &&
        workspace.claim?.id === event.input.claimId &&
        workspace.claim.lockVersion === event.input.lockVersion &&
        !workspace.claim.approvalStale &&
        (event.input.targetStatus === undefined ||
          workspace.claimStatusTransitions.some(
            (option) =>
              option.value === event.input.targetStatus && option.allowed,
          ))
      )
    case "request-claim-confirmation":
      return (
        c.requestClaimConfirmation.allowed &&
        workspace.claim?.id === event.input.claimId &&
        workspace.claim.status === "SUPPORTED" &&
        workspace.claim.sourceHash.length === 64 &&
        workspace.claim.textHash.length === 64
      )
    case "download-version":
      return (
        c.downloadVersion.allowed &&
        workspace.selectedVersion?.id === event.input.versionId &&
        workspace.selectedVersion.status === "AVAILABLE"
      )
  }
}

async function execute(projectId: string, event: ManuscriptWorkspaceEvent) {
  switch (event.action) {
    case "upload-manuscript":
      return uploadManuscript(projectId, event.input.file, event.input.title)
    case "start-check":
      return ManuscriptsApi.startCheck(
        event.input.versionId,
        {
          checks: [...event.input.checks] as never,
          use_project_literature: true,
          use_project_analysis_results: true,
          use_project_figures: true,
        },
        key(),
      )
    case "retry-job":
      return JobsApi.retry(event.input.jobId, key())
    case "cancel-job":
      return JobsApi.cancel(event.input.jobId, event.input.reason, key())
    case "accept-issue":
      return ManuscriptsApi.acceptIssue(
        event.input.issueId,
        event.input.lockVersion,
        event.input.reason ?? undefined,
      )
    case "reject-issue":
      return ManuscriptsApi.rejectIssue(
        event.input.issueId,
        event.input.lockVersion,
        event.input.reason,
      )
    case "create-fix-plan":
      return ManuscriptsApi.createFixPlan(
        event.input.versionId,
        [...event.input.issueIds],
        key(),
      )
    case "preview-fix-plan":
      return ManuscriptsApi.previewFixPlan(
        event.input.planId,
        event.input.lockVersion,
      )
    case "request-fix-approval":
      return ManuscriptsApi.requestFixApproval(event.input.planId, key())
    case "execute-fix-plan":
      return ManuscriptsApi.executeFixPlan(event.input.planId, key())
    case "start-revision-audit":
      return ManuscriptsApi.startRevisionAudit(
        projectId,
        {
          baseline_manuscript_version_id: event.input.beforeVersionId,
          candidate_manuscript_version_id: event.input.afterVersionId,
          referenced_result_ids: [],
        },
        key(),
      )
    case "create-claim":
      return ManuscriptsApi.createClaim(
        projectId,
        {
          claim_type: event.input.claimType as never,
          source_object_type: event.input.sourceObjectType as never,
          source_object_id: event.input.sourceObjectId,
          source_location: { ...event.input.sourceLocation },
          claim_text: event.input.text,
          scope_statement: event.input.scope,
          status: "NEEDS_EVIDENCE",
          confidence: "UNKNOWN",
        },
        key(),
      )
    case "update-claim":
      return ManuscriptsApi.updateClaim(
        event.input.claimId,
        {
          claim_text: event.input.text,
          scope_statement: event.input.scope,
          status: event.input.targetStatus,
        },
        event.input.lockVersion,
      )
    case "request-claim-confirmation":
      return ManuscriptsApi.requestClaimConfirmation(event.input.claimId, key())
    case "download-version":
      return ManuscriptsApi.download(event.input.versionId)
    case "select-version":
    case "refresh":
      return null
  }
}

async function sha256(file: File) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer())
  return [...new Uint8Array(digest)]
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("")
}

async function uploadManuscript(
  projectId: string,
  file: File,
  title: string | null,
) {
  const digest = await sha256(file)
  const initiated = await ArtifactsApi.initiate(
    projectId,
    {
      artifact_type: "MANUSCRIPT_DOCX",
      filename: file.name,
      mime_type:
        file.type ||
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      size_bytes: file.size,
      sha256: digest,
      is_original: true,
    },
    key(),
  )
  await ArtifactsApi.transfer(initiated.data.upload_id, file)
  const completed = await ArtifactsApi.complete(
    projectId,
    initiated.data.upload_id,
    { sha256: digest, size_bytes: file.size },
    key(),
  )
  return ManuscriptsApi.create(projectId, {
    artifact_id: completed.data.id,
    title,
  })
}

export function useManuscriptWorkspaceMutation(
  projectId: string,
  workspace: ManuscriptWorkspaceViewModel | null,
  onSuccess?: (event: ManuscriptWorkspaceEvent, result: unknown) => void,
) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: async (event: ManuscriptWorkspaceEvent) => {
      if (!canExecuteManuscriptWorkspaceEvent(workspace, event))
        throw new Error("The event is not allowed by current server facts.")
      return { event, result: await execute(projectId, event) }
    },
    onSuccess: async ({ event, result }) => {
      await client.invalidateQueries({
        queryKey: ["projects", projectId, "manuscript-workspace"],
      })
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
