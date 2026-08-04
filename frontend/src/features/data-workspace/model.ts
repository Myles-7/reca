import type { SemanticTone } from "../projects/model"

export type KnownFact = {
  status: string
  knownStatus: boolean
  tone: SemanticTone
}

export type ActionCapability = {
  allowed: boolean
  disabledReason: string | null
}

export type DataWorkspaceCapabilities = {
  permissionsKnown: boolean
  uploadDataset: ActionCapability
  selectWorksheet: ActionCapability
  updateDatasetIdentity: ActionCapability
  updateColumn: ActionCapability
  runQuality: ActionCapability
  acknowledgeIssue: ActionCapability
  ignoreIssue: ActionCapability
  createPlan: ActionCapability
  updatePlan: ActionCapability
  previewPlan: ActionCapability
  requestApproval: ActionCapability
  executePlan: ActionCapability
  compareVersions: ActionCapability
  retryJob: ActionCapability
}

export type CleaningLiteralValue = string | number | boolean | null

export type CleaningRowSelector =
  | { type: "ALL_ROWS" }
  | { type: "ISSUE_ROWS"; issueIds: readonly string[] }
  | { type: "VALUE_EQUALS"; columnId: string; value: CleaningLiteralValue }
  | {
      type: "VALUE_IN"
      columnId: string
      values: readonly CleaningLiteralValue[]
    }
  | { type: "IS_NULL" | "IS_NOT_NULL"; columnId: string }
  | {
      type: "NUMERIC_RANGE"
      columnId: string
      minimum: number | null
      maximum: number | null
      includeMinimum: boolean
      includeMaximum: boolean
    }

type CleaningActionBase = {
  targetColumnIds: readonly string[]
  rowSelector: CleaningRowSelector
  reason: string
  sourceIssueIds: readonly string[]
}

export type CleaningActionInput =
  | (CleaningActionBase & {
      type: "MARK_MISSING"
      parameters: { replacement: null }
    })
  | (CleaningActionBase & {
      type: "REPLACE_VALUE"
      parameters: { replacement: CleaningLiteralValue }
    })
  | (CleaningActionBase & {
      type: "MAP_CATEGORY"
      parameters: { mapping: Readonly<Record<string, CleaningLiteralValue>> }
    })
  | (CleaningActionBase & {
      type: "CAST_TYPE"
      parameters: {
        targetType:
          | "STRING"
          | "INTEGER"
          | "NUMERIC"
          | "BOOLEAN"
          | "DATE"
          | "DATETIME"
        onInvalid: "FAIL" | "MARK_MISSING"
      }
    })
  | (CleaningActionBase & {
      type: "RENAME_COLUMN"
      parameters: { newName: string }
    })

export type DatasetListItemViewModel = KnownFact & {
  id: string
  name: string
  currentVersionId: string | null
  sourceType: string
  licenseStatus: string
  licenseWarning: string | null
  updatedAt: string
}

export type DatasetIdentityViewModel = KnownFact & {
  id: string
  projectId: string
  name: string
  description: string | null
  publisher: string | null
  sourcePlatform: string | null
  sourceIdentifier: string | null
  doi: string | null
  licenseName: string | null
  licenseStatus: string
  licenseWarning: string | null
  recommendedCitation: string | null
  knownLimitations: string | null
  currentVersionId: string | null
  lockVersion: number
}

export type WorksheetViewModel = {
  name: string
  ordinal: number
  visibility: "VISIBLE" | "HIDDEN" | "VERY_HIDDEN" | "UNKNOWN"
  estimatedRows: number
  estimatedColumns: number
  selected: boolean
  warnings: readonly string[]
}

export type DatasetVersionViewModel = KnownFact & {
  id: string
  datasetId: string
  versionNumber: number
  versionType: string
  fileFormat: string
  artifactId: string
  parentVersionId: string | null
  transformationId: string | null
  current: boolean
  original: boolean
  invalidated: boolean
  rowCount: number | null
  columnCount: number | null
  dataHash: string
  schemaHash: string | null
  projectionHash: string | null
  selectedWorksheetName: string | null
  worksheets: readonly WorksheetViewModel[]
  invalidationReason: string | null
  createdAt: string
}

export type DatasetColumnViewModel = {
  id: string
  sourceName: string
  displayName: string | null
  inferredType: string
  confirmedType: string | null
  semanticRole: string | null
  unit: string | null
  description: string | null
  confirmationStatus: string
  confirmationKnown: boolean
  uniqueCount: number | null
  missingRatio: number | null
  exampleValues: readonly string[]
  sensitiveCandidate: boolean
  sensitiveConfirmed: boolean
  inheritedFromColumnId: string | null
  lockVersion: number
}

export type DatasetPreviewViewModel = {
  columns: readonly string[]
  rows: readonly Record<string, string>[]
  returned: number
  totalRows: number | null
  truncated: boolean
  masked: boolean
}

export type QualityRunViewModel = KnownFact & {
  id: string
  versionId: string
  rulesetId: string
  rulesetVersion: string
  rulesetHash: string
  issueCount: number
  highIssueCount: number
  jobId: string | null
  errorCode: string | null
  degraded: boolean
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type QualityIssueViewModel = KnownFact & {
  id: string
  ruleCode: string
  issueType: string
  severity: string
  columnId: string | null
  affectedRowCount: number | null
  description: string
  clueOnly: boolean
  sensitiveCandidate: boolean
  sensitiveConfirmed: boolean
  exampleSummary: readonly string[]
  requiresApproval: boolean
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type CleaningPlanViewModel = KnownFact & {
  id: string
  versionId: string
  title: string
  rationale: string | null
  actionCount: number
  actions: readonly { type: string; reason: string; targetCount: number }[]
  editorActions: readonly CleaningActionInput[]
  actionsEditable: boolean
  actionsDisabledReason: string | null
  preview: null | {
    hash: string
    affectedRows: number
    affectedColumns: number
    rowCountBefore: number | null
    rowCountAfter: number | null
    warnings: readonly string[]
    risk: string
    readyForApproval: boolean
  }
  approvalRecordId: string | null
  approvalPayloadHash: string | null
  transformationId: string | null
  jobId: string | null
  lockVersion: number
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type ApprovalViewModel = KnownFact & {
  id: string
  expiresAt: string | null
  expired: boolean
  stale: boolean
  decisionReason: string | null
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type TransformationViewModel = KnownFact & {
  id: string
  sourceVersionId: string
  targetVersionId: string | null
  outputArtifactId: string | null
  affectedRows: number | null
  affectedColumns: number | null
  errorCode: string | null
}

export type JobStateViewModel = KnownFact & {
  id: string
  accepted: boolean
  queued: boolean
  running: boolean
  completed: boolean
  failed: boolean
  retryable: boolean
  progress: number
  currentStep: string | null
  errorCode: string | null
}

export type VersionComparisonViewModel = {
  baseVersionId: string
  targetVersionId: string
  rowDelta: number
  columnDelta: number
  missingBefore: number
  missingAfter: number
  affectedRows: number | null
  affectedColumns: number | null
  actionTypes: readonly string[]
  parentVersionId: string | null
  transformationId: string | null
  outputArtifactId: string | null
}

export type DataWorkspaceViewModel = {
  projectId: string
  datasets: readonly DatasetListItemViewModel[]
  dataset: DatasetIdentityViewModel | null
  version: DatasetVersionViewModel | null
  versions: readonly DatasetVersionViewModel[]
  columns: readonly DatasetColumnViewModel[]
  preview: DatasetPreviewViewModel | null
  qualityRun: QualityRunViewModel | null
  issues: readonly QualityIssueViewModel[]
  plan: CleaningPlanViewModel | null
  approval: ApprovalViewModel | null
  transformation: TransformationViewModel | null
  job: JobStateViewModel | null
  comparison: VersionComparisonViewModel | null
  capabilities: DataWorkspaceCapabilities
  integrationPending: readonly string[]
}

export function dataWorkspaceHref(
  projectId: string,
  selection: {
    datasetId?: string
    versionId?: string
    qualityRunId?: string
    planId?: string
    approvalId?: string
    jobId?: string
    compareWithVersionId?: string
    view?: "data" | "columns" | "quality" | "cleaning" | "versions"
  } = {},
) {
  const params = new URLSearchParams()
  if (selection.datasetId) params.set("dataset", selection.datasetId)
  if (selection.versionId) params.set("version", selection.versionId)
  if (selection.qualityRunId) params.set("qualityRun", selection.qualityRunId)
  if (selection.planId) params.set("plan", selection.planId)
  if (selection.approvalId) params.set("approval", selection.approvalId)
  if (selection.jobId) params.set("job", selection.jobId)
  if (selection.compareWithVersionId)
    params.set("compareWith", selection.compareWithVersionId)
  if (selection.view) params.set("view", selection.view)
  const query = params.toString()
  return `/projects/${projectId}/data${query ? `?${query}` : ""}`
}
