import type {
  ApprovalActionCommand,
  ApprovalViewModel,
  ArtifactViewModel,
  AuditViewModel,
  JobActionCommand,
  JobStreamState,
  JobViewModel,
  Loadable,
  MemberAddCommand,
  MemberOwnershipTransferCommand,
  MemberRoleChangeCommand,
  MemberViewModel,
  OverviewViewModel,
  ProjectUpdateCommand,
  ProjectViewModel,
  UiErrorViewModel,
  WorkspacePermissions,
} from "../model"

export type ProjectUpdateEvent = ProjectUpdateCommand
export type MemberAddEvent = MemberAddCommand
export type MemberRoleChangeEvent = MemberRoleChangeCommand
export type MemberOwnershipTransferEvent = MemberOwnershipTransferCommand
export type JobActionEvent = JobActionCommand
export type ApprovalActionEvent = ApprovalActionCommand

export type ProjectHeaderProps = {
  project: ProjectViewModel
  lifecyclePending: boolean
  lifecycleError: UiErrorViewModel | null
  updatePending: boolean
  updateError: UiErrorViewModel | null
  onArchive: () => void
  onRestore: () => void
  onUpdate: (event: ProjectUpdateEvent) => void
}

export type ProjectLifecycleControlProps = {
  action: "archive" | "restore"
  pending: boolean
  error: UiErrorViewModel | null
  onAction: () => void
}

export type EditProjectDialogProps = {
  project: ProjectViewModel
  open: boolean
  pending: boolean
  error: UiErrorViewModel | null
  onOpenChange: (open: boolean) => void
  onUpdate: (event: ProjectUpdateEvent) => void
}

export type OverviewPanelProps = {
  content: Loadable<OverviewViewModel>
  loadError: UiErrorViewModel | null
  onRetry: () => void
}

export type MembersPanelData = {
  members: MemberViewModel[]
  permissions: WorkspacePermissions
}

export type MembersPanelProps = {
  content: Loadable<MembersPanelData>
  submitting: boolean
  loadError: UiErrorViewModel | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onAddMember: (event: MemberAddEvent) => void
  onChangeRole: (event: MemberRoleChangeEvent) => void
  onTransferOwnership: (event: MemberOwnershipTransferEvent) => void
  onRemoveMember: (memberId: string) => void
}

export type ArtifactsPanelProps = {
  content: Loadable<ArtifactViewModel[]>
  permissionsKnown: boolean
  canUpload: boolean
  uploading: boolean
  loadError: UiErrorViewModel | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onUpload: (file: File) => void
  onDownload: (artifactId: string) => void
}

export type JobsPanelProps = {
  content: Loadable<JobViewModel[]>
  permissions: WorkspacePermissions | null
  streamState: JobStreamState
  submittingJobId: string | null
  loadError: UiErrorViewModel | null
  mutationError: UiErrorViewModel | null
  onRetryLoad: () => void
  onAction: (event: JobActionEvent) => void
}

export type ApprovalsPanelProps = {
  content: Loadable<ApprovalViewModel[]>
  submittingApprovalId: string | null
  loadError: UiErrorViewModel | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onAction: (event: ApprovalActionEvent) => void
}

export type AuditPanelProps = {
  content: Loadable<AuditViewModel[]>
  loadError: UiErrorViewModel | null
  onRetry: () => void
}

export type ProjectWorkspaceReadyView = {
  header: ProjectHeaderProps
  overview: OverviewPanelProps
  members: MembersPanelProps
  artifacts: ArtifactsPanelProps
  jobs: JobsPanelProps
  approvals: ApprovalsPanelProps
  audit: AuditPanelProps
}

export type ProjectWorkspaceViewProps = Loadable<ProjectWorkspaceReadyView>
