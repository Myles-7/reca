import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  invalidateProjectApprovals,
  invalidateProjectArtifacts,
  invalidateProjectDetail,
  invalidateProjectJobs,
  invalidateProjectLifecycle,
  invalidateProjectMembers,
} from "./cache"
import {
  approvalCommands,
  downloadArtifact,
  jobCommands,
  memberCommands,
  projectCommands,
  uploadArtifact,
} from "./controller"
import { mapUiError } from "./mappers"
import type {
  ApprovalActionCommand,
  ApprovalViewModel,
  ArtifactListViewModel,
  JobActionCommand,
  JobViewModel,
  MemberAddCommand,
  MemberOwnershipTransferCommand,
  MemberRoleChangeCommand,
  MemberUpdateCommand,
  MemberViewModel,
  ProjectUpdateCommand,
  ProjectViewModel,
  UiErrorViewModel,
  WorkspacePermissions,
} from "./model"

type ProjectCommandPort = {
  archive: (projectId: string) => Promise<unknown>
  restore: (projectId: string) => Promise<unknown>
  update: (
    projectId: string,
    input: ProjectUpdateCommand,
    lockVersion: number,
  ) => Promise<unknown>
}

type MemberCommandPort = {
  add: (
    projectId: string,
    input: { user_id: string; role: MemberAddCommand["role"] },
  ) => Promise<unknown>
  update: (
    projectId: string,
    memberId: string,
    input: MemberUpdateCommand,
  ) => Promise<unknown>
  remove: (projectId: string, memberId: string) => Promise<unknown>
}

type ArtifactCommandPort = {
  upload: (
    projectId: string,
    file: File,
    artifactType: "OTHER",
  ) => Promise<unknown>
  download: (artifactId: string) => Promise<string>
}

type JobCommandPort = {
  retry: (jobId: string) => Promise<unknown>
  cancel: (jobId: string, reason: string) => Promise<unknown>
}

type ApprovalCommandPort = {
  approve: (approvalId: string, reason: string | null) => Promise<unknown>
  reject: (approvalId: string, reason: string) => Promise<unknown>
  cancel: (approvalId: string) => Promise<unknown>
}

export type MemberMutationCommand =
  | { action: "add"; input: MemberAddCommand }
  | { action: "change-role"; input: MemberRoleChangeCommand }
  | {
      action: "transfer-ownership"
      input: MemberOwnershipTransferCommand
    }
  | { action: "remove"; memberId: string }

export function canExecuteProjectAction(
  project: ProjectViewModel | null,
  action: "update" | "lifecycle",
): boolean {
  if (!project || !project.knownStatus || !project.permissionsKnown)
    return false
  return action === "update" ? project.canUpdate : project.canDelete
}

export function canExecuteMemberMutation(
  permissions: WorkspacePermissions | null,
): boolean {
  return permissions?.permissionsKnown === true && permissions.canManageMembers
}

export function canExecuteMemberCommand(
  members: readonly MemberViewModel[],
  permissions: WorkspacePermissions | null,
  command: MemberMutationCommand,
): boolean {
  if (!canExecuteMemberMutation(permissions)) return false
  if (command.action === "add") return command.input.userId.trim().length > 0
  const memberId =
    command.action === "remove" ? command.memberId : command.input.memberId
  const member = members.find((candidate) => candidate.id === memberId)
  return Boolean(member && !member.isOwner && !member.removed)
}

export function canExecuteArtifactUpload(
  workspace: ArtifactListViewModel | null,
): boolean {
  return workspace?.permissionsKnown === true && workspace.canUpload
}

export function canExecuteArtifactDownload(
  workspace: ArtifactListViewModel | null,
  artifactId: string,
): boolean {
  return (
    workspace?.artifacts.some(
      (artifact) => artifact.id === artifactId && artifact.canDownload,
    ) === true
  )
}

export function canExecuteJobAction(
  jobs: readonly JobViewModel[],
  permissions: WorkspacePermissions | null,
  command: JobActionCommand,
): boolean {
  if (permissions?.permissionsKnown !== true) return false
  const job = jobs.find((candidate) => candidate.id === command.jobId)
  if (!job) return false
  return command.action === "retry"
    ? permissions.canRetryJob && job.retryable
    : permissions.canCancelJob && job.active
}

export function canExecuteApprovalAction(
  approvals: readonly ApprovalViewModel[],
  command: ApprovalActionCommand,
): boolean {
  const approval = approvals.find(
    (candidate) => candidate.id === command.approvalId,
  )
  if (!approval || approval.stale) return false
  return approval.allowedActions.has(`approval.${command.action}`)
}

export function mutationUiError(error: unknown): UiErrorViewModel | null {
  return error ? mapUiError(error) : null
}

export function executeProjectLifecycle(
  projectId: string,
  restore: boolean,
  commands: ProjectCommandPort = projectCommands,
) {
  return restore ? commands.restore(projectId) : commands.archive(projectId)
}

export function executeProjectUpdate(
  projectId: string,
  input: ProjectUpdateCommand,
  lockVersion: number,
  commands: ProjectCommandPort = projectCommands,
) {
  return commands.update(projectId, input, lockVersion)
}

export function executeMemberMutation(
  projectId: string,
  command: MemberMutationCommand,
  commands: MemberCommandPort = memberCommands,
) {
  if (command.action === "add") {
    return commands.add(projectId, {
      user_id: command.input.userId,
      role: command.input.role,
    })
  }
  if (command.action === "change-role") {
    return commands.update(projectId, command.input.memberId, {
      role: command.input.role,
    })
  }
  if (command.action === "transfer-ownership") {
    return commands.update(projectId, command.input.memberId, {
      role: "OWNER",
      transferOwnership: true,
      previousOwnerRole: command.input.previousOwnerRole,
      reason: command.input.reason,
    })
  }
  return commands.remove(projectId, command.memberId)
}

export function executeArtifactUpload(
  projectId: string,
  file: File,
  commands: ArtifactCommandPort = {
    upload: uploadArtifact,
    download: downloadArtifact,
  },
) {
  return commands.upload(projectId, file, "OTHER")
}

export function getArtifactDownloadUrl(
  artifactId: string,
  commands: ArtifactCommandPort = {
    upload: uploadArtifact,
    download: downloadArtifact,
  },
) {
  return commands.download(artifactId)
}

export function executeJobAction(
  command: JobActionCommand,
  commands: JobCommandPort = jobCommands,
) {
  return command.action === "retry"
    ? commands.retry(command.jobId)
    : commands.cancel(command.jobId, "Cancelled from project workspace")
}

export function executeApprovalAction(
  command: ApprovalActionCommand,
  commands: ApprovalCommandPort = approvalCommands,
) {
  if (command.action === "approve") {
    return commands.approve(command.approvalId, command.reason)
  }
  if (command.action === "reject") {
    return commands.reject(
      command.approvalId,
      command.reason ?? "Rejected from project workspace",
    )
  }
  return commands.cancel(command.approvalId)
}

export function useProjectLifecycleMutation(
  projectId: string,
  restore: boolean,
) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: () => executeProjectLifecycle(projectId, restore),
    onSuccess: () => invalidateProjectLifecycle(queryClient, projectId),
  })
  return {
    mutate: () => mutation.mutate(),
    isPending: mutation.isPending,
    uiError: mutationUiError(mutation.error),
  }
}

export function useProjectUpdateMutation(
  projectId: string,
  lockVersion: number,
  onSuccess: () => void,
) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (input: ProjectUpdateCommand) =>
      executeProjectUpdate(projectId, input, lockVersion),
    onSuccess: async () => {
      await invalidateProjectDetail(queryClient, projectId)
      onSuccess()
    },
  })
  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    uiError: mutationUiError(mutation.error),
  }
}

export function useMemberMutation(projectId: string) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (command: MemberMutationCommand) =>
      executeMemberMutation(projectId, command),
    onSuccess: () => invalidateProjectMembers(queryClient, projectId),
  })
  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    uiError: mutationUiError(mutation.error),
  }
}

export function useArtifactUploadMutation(projectId: string) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (file: File) => executeArtifactUpload(projectId, file),
    onSuccess: () => invalidateProjectArtifacts(queryClient, projectId),
  })
  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    uiError: mutationUiError(mutation.error),
  }
}

export function useJobActionMutation(projectId: string) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (command: JobActionCommand) => executeJobAction(command),
    onSuccess: () => invalidateProjectJobs(queryClient, projectId),
  })
  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    submittingJobId: mutation.isPending
      ? (mutation.variables?.jobId ?? null)
      : null,
    uiError: mutationUiError(mutation.error),
  }
}

export function useApprovalActionMutation(projectId: string) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (command: ApprovalActionCommand) =>
      executeApprovalAction(command),
    onSuccess: () => invalidateProjectApprovals(queryClient, projectId),
  })
  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    submittingApprovalId: mutation.isPending
      ? (mutation.variables?.approvalId ?? null)
      : null,
    uiError: mutationUiError(mutation.error),
  }
}
