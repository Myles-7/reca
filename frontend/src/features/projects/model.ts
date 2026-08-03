export type SemanticTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "degraded"

export type UiErrorViewModel = {
  title: string
  message: string
  code: string
  requestId: string | null
  retryable: boolean
  forbidden: boolean
  notFound: boolean
  conflict: boolean
}

export type Loadable<T> =
  | { state: "loading"; label: string }
  | { state: "empty"; message: string }
  | { state: "error"; error: UiErrorViewModel }
  | { state: "ready"; data: T }

export type ProjectListItemViewModel = {
  id: string
  name: string
  description: string | null
  stage: string
  status: string
  knownStatus: boolean
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
  type: string
  updatedAt: string
  canUpdate: boolean
}

export type ProjectViewModel = ProjectListItemViewModel & {
  ownerId: string
  discipline: string | null
  researchDirection: string | null
  lockVersion: number
  canDelete: boolean
}

export type CapabilityViewModel = {
  key: string
  label: string
  availability: "AVAILABLE" | "NOT_AVAILABLE" | "DEGRADED"
  value: number | null
  tone: SemanticTone
}

export type OverviewViewModel = {
  stage: string
  foundationCounts: Array<{ label: string; value: number | null }>
  capabilities: CapabilityViewModel[]
  researchQuestion: null
  evidenceCompleteness: null
  pendingActionCount: number
}

export type WorkspacePermissions = {
  permissionsKnown: boolean
  actions: ReadonlySet<string>
  canManageMembers: boolean
  canUploadArtifact: boolean
  canRetryJob: boolean
  canCancelJob: boolean
}

export type MemberViewModel = {
  id: string
  userId: string
  displayName: string
  email: string
  role: string
  joinedAt: string
  removed: boolean
  isCurrentUser: boolean
  isOwner: boolean
}

export type ArtifactViewModel = {
  id: string
  filename: string
  kind: string
  origin: "ORIGINAL" | "DERIVED"
  status: string
  size: string
  sha256: string
  createdAt: string
  canDownload: boolean
  immutable: boolean
  tone: SemanticTone
}

export type ArtifactListViewModel = {
  artifacts: ArtifactViewModel[]
  permissionsKnown: boolean
  canUpload: boolean
}

export type JobViewModel = {
  id: string
  taskLabel: string
  status: string
  progress: number
  step: string | null
  retryable: boolean
  retryCount: number
  maxRetries: number
  error: string | null
  resultUrl: string | null
  createdAt: string
  active: boolean
  tone: SemanticTone
}

export type ApprovalViewModel = {
  id: string
  type: string
  target: string
  status: string
  requester: string
  requestedAt: string
  expiresAt: string | null
  payloadHash: string
  allowedActions: ReadonlySet<string>
  stale: boolean
  tone: SemanticTone
}

export type AuditViewModel = {
  id: string
  actor: string
  action: string
  target: string
  occurredAt: string
  requestId: string | null
  outcome: string
  summary: string | null
  tone: SemanticTone
}

export type JobStreamState = "idle" | "connected" | "degraded" | "stale"

export type ProjectTypeOption =
  | "THESIS"
  | "COURSE"
  | "INNOVATION"
  | "RESEARCH"
  | "DEMO"

export type ProjectCreateCommand = {
  name: string
  description: string | null
  discipline: string | null
  projectType: ProjectTypeOption
}

export type ProjectUpdateCommand = {
  name: string
  description: string | null
}

export type MemberRoleOption = "EDITOR" | "REVIEWER" | "VIEWER"

export type MemberAddCommand = {
  userId: string
  role: MemberRoleOption
}

export type MemberRoleChangeCommand = {
  memberId: string
  role: MemberRoleOption
}

export type MemberOwnershipTransferCommand = {
  memberId: string
  previousOwnerRole: MemberRoleOption
  reason: string
}

export type MemberUpdateCommand = {
  role: MemberRoleOption | "OWNER"
  transferOwnership?: boolean
  previousOwnerRole?: MemberRoleOption
  reason?: string
}

export type JobActionCommand = {
  jobId: string
  action: "retry" | "cancel"
}

export type ApprovalActionCommand = {
  approvalId: string
  action: "approve" | "reject" | "cancel"
  reason: string | null
}
