import type { Loadable, UiErrorViewModel } from "../projects/model"

export type EvidenceWorkspaceView = "graph" | "claims" | "audits" | "exports"
export type KnownFact = { status: string; knownStatus: boolean }
export type ActionCapability = {
  allowed: boolean
  disabledReason: string | null
}
export type EvidenceScope =
  | "AVAILABLE"
  | "DENIED"
  | "MISSING"
  | "STALE"
  | "UNKNOWN"
export type EvidenceRisk = "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN"
export type EdgeSemantic =
  | "SUPPORT"
  | "CONTRADICT"
  | "QUALIFY"
  | "PROVENANCE"
  | "UNKNOWN"

export type EvidenceWorkspaceCapabilities = {
  permissionsKnown: boolean
  createEvidenceLink: ActionCapability
  confirmEvidenceLink: ActionCapability
  invalidateEvidenceLink: ActionCapability
  runClaimAudit: ActionCapability
  runExportReadiness: ActionCapability
  createReproPackage: ActionCapability
  requestExportConfirmation: ActionCapability
  retryJob: ActionCapability
  cancelJob: ActionCapability
  downloadReproPackage: ActionCapability
}

export type ClaimViewModel = KnownFact & {
  id: string
  projectId: string
  claimType: string
  text: string
  sourceObjectType: string
  sourceObjectId: string
  sourceHash: string
  textHash: string
  lockVersion: number
  stale: boolean
  allowedActions: ReadonlySet<string>
}

export type ClaimSummaryViewModel = KnownFact & {
  id: string
  label: string
  risk: EvidenceRisk
  stale: boolean
  invalidated: boolean
  allowedActions: ReadonlySet<string>
}

export type EvidenceReferenceViewModel = KnownFact & {
  objectType: string
  objectId: string
  projectId: string
  label: string
  sourceHash: string
  detailIntent: string
  scope: EvidenceScope
  stale: boolean
  invalidated: boolean
  limitations: readonly string[]
  allowedActions: ReadonlySet<string>
}

export type EvidenceLinkViewModel = KnownFact & {
  id: string
  projectId: string
  claimId: string
  relationType: string
  semantic: EdgeSemantic
  strength: string
  explanation: string | null
  lockVersion: number
  stale: boolean
  invalidated: boolean
  evidence: EvidenceReferenceViewModel
  allowedActions: ReadonlySet<string>
}

export type EvidenceGraphNodeViewModel = KnownFact & {
  id: string
  nodeType: string
  objectId: string
  label: string
  risk: EvidenceRisk
  scope: EvidenceScope
  invalidated: boolean
  stale: boolean
  sourceKind: "DOMAIN" | "STORED" | "DERIVED" | "UNKNOWN"
  detailIntent: string
  limitations: readonly string[]
  allowedActions: ReadonlySet<string>
  lane: string | null
  rank: number | null
}

export type EvidenceGraphEdgeViewModel = KnownFact & {
  id: string
  source: string
  target: string
  relationType: string
  strength: string | null
  semantic: EdgeSemantic
  risk: EvidenceRisk
  invalidated: boolean
  sourceKind: "STORED" | "DERIVED" | "UNKNOWN"
}

export type GraphCanvasNode = {
  id: string
  position: { x: number; y: number }
  data: EvidenceGraphNodeViewModel
  selectable: true
  draggable: true
  connectable: false
}

export type GraphCanvasEdge = {
  id: string
  source: string
  target: string
  data: EvidenceGraphEdgeViewModel
  selectable: true
  reconnectable: false
}

export type CompletenessItemViewModel = KnownFact & {
  code: string
  sourceObjectIds: readonly string[]
  limitations: readonly string[]
  missingActions: readonly string[]
  scientificQualityScore: null
}

export type ClaimCompletenessViewModel = {
  claimId: string
  ruleSetVersion: string
  items: readonly CompletenessItemViewModel[]
  limitations: readonly string[]
  isScientificQualityScore: false
}

export type ClaimAuditViewModel = KnownFact & {
  id: string
  projectId: string
  auditType: string
  targetObjectType: string | null
  targetObjectId: string | null
  jobId: string | null
  outcome: string | null
  outcomeKnown: boolean
  sourceSnapshotHash: string | null
  resultHash: string | null
  findings: readonly Readonly<Record<string, unknown>>[]
  limitations: readonly string[]
  degraded: boolean
  ruleSetVersion: string
  allowedActions: ReadonlySet<string>
}

export type ReadinessIssueViewModel = {
  code: string
  objectType: string
  objectId: string | null
  message: string
  blocking: boolean
}

export type ExportCandidateViewModel = KnownFact & {
  objectType: string
  objectId: string | null
  artifactId: string | null
  packagePath: string
  sha256: string | null
  exclusionReason: string | null
  licenseStatus: string
  sensitive: boolean
  redistribution: string
}

export type ExportReadinessViewModel = {
  auditId: string
  ready: boolean
  requiresConfirmation: boolean
  blockers: readonly ReadinessIssueViewModel[]
  warnings: readonly ReadinessIssueViewModel[]
  candidates: readonly ExportCandidateViewModel[]
  limitations: readonly string[]
  snapshotHash: string
  ruleSetVersion: string
}

export type ApprovalViewModel = KnownFact & {
  id: string
  projectId: string
  targetObjectType: string
  targetObjectId: string
  payloadHash: string
  stale: boolean
  expiresAt: string | null
  items: readonly {
    itemType: string
    itemId: string
    decision: string | null
    reason: string | null
  }[]
  allowedActions: ReadonlySet<string>
}

export type JobViewModel = KnownFact & {
  id: string
  projectId: string
  taskType: string
  resourceType: string
  resourceId: string
  progress: number
  retryable: boolean
  errorCode: string | null
}

export type ExportViewModel = KnownFact & {
  id: string
  projectId: string
  exportType: string
  scopeHash: string
  readinessAuditId: string | null
  approvalId: string | null
  jobId: string | null
  lockVersion: number
  errorCode: string | null
  allowedActions: ReadonlySet<string>
}

export type ManifestFileViewModel = {
  path: string
  size: number
  sha256: string
  type: string
  source: Readonly<Record<string, unknown>>
  licenseStatus: string
  sensitive: boolean
  redistribution: string
}

export type ManifestViewModel = {
  schemaVersion: string
  sha256: string
  files: readonly ManifestFileViewModel[]
  agentLogs: "NOT_AVAILABLE" | string
  limitations: readonly string[]
  runtimeDependencies: readonly Readonly<Record<string, unknown>>[]
  serviceImages: readonly Readonly<Record<string, unknown>>[]
}

export type ReproPackageViewModel = KnownFact & {
  id: string
  exportId: string
  projectId: string
  artifactId: string
  manifestArtifactId: string
  packageVersion: number
  schemaVersion: string
  containsSensitiveData: boolean
  containsRestrictedData: boolean
  fileCount: number
  totalSizeBytes: number
  sha256: string
  manifest: ManifestViewModel
  tampered: boolean
  allowedActions: ReadonlySet<string>
}

export type ReproPackageHistoryItemViewModel = {
  id: string
  exportId: string
  projectId: string
  artifactId: string
  manifestArtifactId: string
  packageVersion: number
  schemaVersion: string
  containsSensitiveData: boolean
  containsRestrictedData: boolean
  fileCount: number
  totalSizeBytes: number
  sha256: string
  createdAt: string
  selected: boolean
  allowedActions: ReadonlySet<string>
}

export type EvidenceScopeNotice = {
  scope: Exclude<EvidenceScope, "AVAILABLE">
  message: string
}

export type EvidenceWorkspaceViewModel = {
  projectId: string
  permissionsKnown: boolean
  graph: {
    nodes: readonly EvidenceGraphNodeViewModel[]
    edges: readonly EvidenceGraphEdgeViewModel[]
    canvasNodes: readonly GraphCanvasNode[]
    canvasEdges: readonly GraphCanvasEdge[]
    complete: boolean
    partial: boolean
    nextCursor: string | null
    degraded: boolean
    limitations: readonly string[]
  }
  claims: readonly ClaimSummaryViewModel[]
  selectedClaim: ClaimViewModel | null
  links: readonly EvidenceLinkViewModel[]
  selectedLink: EvidenceLinkViewModel | null
  selectedNode: EvidenceGraphNodeViewModel | null
  completeness: Readonly<Record<string, ClaimCompletenessViewModel>>
  audit: ClaimAuditViewModel | null
  auditJob: JobViewModel | null
  readiness: ExportReadinessViewModel | null
  export: ExportViewModel | null
  approval: ApprovalViewModel | null
  job: JobViewModel | null
  package: ReproPackageViewModel | null
  packageHistory: readonly ReproPackageHistoryItemViewModel[]
  packageHistoryPage: number
  packageHistoryHasNext: boolean
  scopeNotices: readonly EvidenceScopeNotice[]
  routeFallback: boolean
  capabilities: EvidenceWorkspaceCapabilities
}

export type EvidenceWorkspaceContent = Loadable<EvidenceWorkspaceViewModel>
export type EvidenceWorkspaceMutationError = UiErrorViewModel | null
