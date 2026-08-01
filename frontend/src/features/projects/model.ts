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

export type ProjectListItemViewModel = {
  id: string
  name: string
  description: string | null
  stage: string
  status: string
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

export type MemberRoleOption = "EDITOR" | "REVIEWER" | "VIEWER"

export type MemberUpdateCommand = {
  role: MemberRoleOption | "OWNER"
  transferOwnership?: boolean
  previousOwnerRole?: MemberRoleOption
  reason?: string
}
