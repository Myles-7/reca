export type KnownFact = {
  status: string
  knownStatus: boolean
}

export type ActionCapability = {
  allowed: boolean
  disabledReason: string | null
}

export type ContractOption = {
  value: string
  label: string
  allowed: boolean
  disabledReason: string | null
}

export type RevisionReferenceOption = ContractOption & {
  sourceHash: string
  versionNumber: number
}

export type ManuscriptWorkspaceCapabilities = {
  permissionsKnown: boolean
  uploadManuscript: ActionCapability
  startCheck: ActionCapability
  retryJob: ActionCapability
  cancelJob: ActionCapability
  acceptIssue: ActionCapability
  rejectIssue: ActionCapability
  createFixPlan: ActionCapability
  previewFixPlan: ActionCapability
  requestFixApproval: ActionCapability
  executeFixPlan: ActionCapability
  startRevisionAudit: ActionCapability
  createClaim: ActionCapability
  updateClaim: ActionCapability
  requestClaimConfirmation: ActionCapability
  downloadVersion: ActionCapability
}

export type ManuscriptViewModel = KnownFact & {
  id: string
  projectId: string
  title: string
  currentVersionId: string | null
  lockVersion: number
  allowedActions: ReadonlySet<string>
}

export type ManuscriptVersionViewModel = KnownFact & {
  id: string
  manuscriptId: string
  projectId: string
  versionNumber: number
  parentVersionId: string | null
  artifactId: string
  versionType: string
  sourceTransformationId: string | null
  sourceHash: string
  parseConfidence: string | null
  unsupportedFeatures: readonly string[]
  invalidationReason: string | null
  allowedActions: ReadonlySet<string>
}

export type JobViewModel = KnownFact & {
  id: string
  projectId: string
  resourceType: string
  resourceId: string
  progress: number
  retryable: boolean
  errorCode: string | null
}

export type CheckRunViewModel = KnownFact & {
  id: string
  projectId: string
  versionId: string
  jobId: string | null
  sourceHash: string
  issueCount: number
  highIssueCount: number
  degradation: Readonly<Record<string, unknown>> | null
  lowConfidence: boolean
  errorCode: string | null
  allowedActions: ReadonlySet<string>
}

export type EvidenceViewModel = {
  id: string
  type: string
  objectType: string
  objectId: string | null
  excerpt: string | null
  hash: string
  metadata: Readonly<Record<string, unknown>> | null
  readScope: "AVAILABLE" | "DENIED" | "MISSING" | "STALE" | "UNKNOWN"
}

export type IssueViewModel = KnownFact & {
  id: string
  projectId: string
  checkRunId: string
  versionId: string
  issueType: string
  severity: string
  locator: Readonly<Record<string, unknown>>
  excerpt: string | null
  reason: string
  suggestion: string | null
  findingHash: string
  confidence: string
  deterministic: boolean
  highRisk: boolean
  autoFixable: boolean
  lockVersion: number
  evidence: readonly EvidenceViewModel[]
  allowedActions: ReadonlySet<string>
}

export type TransformationViewModel = KnownFact & {
  id: string
  projectId: string
  inputVersionId: string
  issueIds: readonly string[]
  inputArtifactHash: string
  preview: Readonly<Record<string, unknown>> | null
  previewHash: string | null
  approvalId: string | null
  approvalStatus: string | null
  approvalKnown: boolean
  approvalStale: boolean
  outputVersionId: string | null
  payloadHash: string
  lockVersion: number
  jobId: string | null
  errorCode: string | null
  allowedActions: ReadonlySet<string>
}

export type RevisionFindingViewModel = {
  code: string
  knownCode: boolean
  severity: "HIGH" | "MEDIUM" | "LOW" | "INFO" | "UNKNOWN"
  locator: Readonly<Record<string, unknown>> | null
  detail: Readonly<Record<string, unknown>>
}

export type RevisionAuditViewModel = KnownFact & {
  id: string
  projectId: string
  manuscriptId: string
  beforeVersionId: string
  afterVersionId: string
  beforeSourceHash: string
  afterSourceHash: string
  resultHash: string | null
  findings: readonly RevisionFindingViewModel[]
  limitations: readonly string[]
  jobId: string | null
  errorCode: string | null
  allowedActions: ReadonlySet<string>
}

export type ClaimViewModel = KnownFact & {
  id: string
  projectId: string
  claimType: string
  text: string
  normalizedClaim: string
  scopeStatement: string | null
  sourceObjectType: string
  sourceObjectId: string
  sourceLocation: Readonly<Record<string, unknown>>
  sourceHash: string
  textHash: string
  confidence: string
  approvalId: string | null
  approvalStatus: string | null
  approvalKnown: boolean
  approvalStale: boolean
  lockVersion: number
  readOnly: boolean
  allowedActions: ReadonlySet<string>
}

export type ManuscriptWorkspaceViewModel = {
  projectId: string
  permissionsKnown: boolean
  discoveryState: "NONE" | "ACTIVE" | "ARCHIVED" | "INVALIDATED" | string
  discoveryKnown: boolean
  manuscript: ManuscriptViewModel | null
  versions: readonly ManuscriptVersionViewModel[]
  selectedVersion: ManuscriptVersionViewModel | null
  checkRun: CheckRunViewModel | null
  issues: readonly IssueViewModel[]
  selectedIssue: IssueViewModel | null
  transformation: TransformationViewModel | null
  revisionAudit: RevisionAuditViewModel | null
  claim: ClaimViewModel | null
  job: JobViewModel | null
  checkDefinitions: readonly ContractOption[]
  revisionReferences: readonly RevisionReferenceOption[]
  claimTypeDefinitions: readonly ContractOption[]
  claimStatusTransitions: readonly ContractOption[]
  degraded: boolean
  capabilities: ManuscriptWorkspaceCapabilities
}
