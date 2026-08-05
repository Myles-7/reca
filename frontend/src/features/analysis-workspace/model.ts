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

export type AnalysisWorkspaceCapabilities = {
  permissionsKnown: boolean
  createPlan: ActionCapability
  updatePlan: ActionCapability
  validatePlan: ActionCapability
  requestPlanApproval: ActionCapability
  runAnalysis: ActionCapability
  invalidateRun: ActionCapability
  retryJob: ActionCapability
  cancelJob: ActionCapability
  createFigurePlan: ActionCapability
  renderFigure: ActionCapability
  requestFigureConfirmation: ActionCapability
  decideFigureConfirmation: ActionCapability
  downloadArtifact: ActionCapability
  requestSuggestion: ActionCapability
  requestInterpretation: ActionCapability
}

export type AnalysisMethod =
  | "DESCRIPTIVE_STATISTICS"
  | "PEARSON_CORRELATION"
  | "SPEARMAN_CORRELATION"
  | "INDEPENDENT_TWO_GROUP"
  | "PAIRED_TWO_GROUP"
  | "SIMPLE_LINEAR_REGRESSION"

export type SampleFilter =
  | { operator: "EQUALS"; columnId: string; value: string | number | boolean }
  | {
      operator: "IN"
      columnId: string
      values: readonly (string | number | boolean)[]
    }
  | { operator: "IS_NULL" | "IS_NOT_NULL"; columnId: string }
  | {
      operator: "NUMERIC_RANGE"
      columnId: string
      minimum: number | null
      maximum: number | null
      includeMinimum: boolean
      includeMaximum: boolean
    }

export type AnalysisPlanInput = {
  researchQuestionVersionId: string
  datasetVersionId: string
  analysisGoal: "DESCRIBE" | "CORRELATION" | "COMPARE_GROUPS" | "MODEL"
  method: AnalysisMethod
  dependentVariableIds: readonly string[]
  independentVariableIds: readonly string[]
  controlVariableIds: readonly string[]
  missingDataMode: "COMPLETE_CASE" | "PAIRWISE_COMPLETE"
  sampleFilter: SampleFilter | null
  confidenceLevel: number
  alternative: "TWO_SIDED" | "LESS" | "GREATER"
  varianceMode: "EQUAL" | "WELCH"
  independenceConfirmed: boolean
  pairingConfirmed: boolean
  pairIdColumnId: string | null
  assumptionConfirmations: readonly string[]
  acknowledgedQualityIssueIds: readonly string[]
  sensitiveColumnAcknowledgements: readonly string[]
}

export type DatasetContextViewModel = KnownFact & {
  datasetId: string
  datasetName: string
  versionId: string
  versionNumber: number
  dataHash: string
  schemaHash: string | null
  projectionHash: string | null
  available: boolean
}

export type ColumnContextViewModel = {
  id: string
  name: string
  confirmedType: string | null
  confirmationStatus: string
  confirmationKnown: boolean
  confirmed: boolean
  unit: string | null
  missingRatio: number | null
  qualityWarning: boolean
  sensitive: boolean
  displayValue: string
}

export type AssumptionCheckViewModel = KnownFact & {
  id: string
  code: string
  subjectKey: string
  explanation: string
  blocksApproval: boolean
  requiresConfirmation: boolean
  checkedAt: string
}

export type AnalysisPlanViewModel = KnownFact & {
  id: string
  projectId: string
  datasetVersionId: string
  researchQuestionVersionId: string
  goal: string
  method: string
  input: AnalysisPlanInput
  validationHash: string | null
  validationWarnings: readonly string[]
  approvalId: string | null
  approvalPayloadHash: string | null
  approvalStale: boolean
  lockVersion: number
  invalidationReason: string | null
  checks: readonly AssumptionCheckViewModel[]
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type ApprovalViewModel = KnownFact & {
  id: string
  targetId: string
  payloadHash: string
  expiresAt: string | null
  expired: boolean
  stale: boolean
  decisionReason: string | null
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type JobViewModel = KnownFact & {
  id: string
  kind: "ANALYSIS" | "FIGURE" | "OTHER"
  accepted: boolean
  progress: number
  currentStep: string | null
  retryable: boolean
  errorCode: string | null
}

export type ArtifactReferenceViewModel = KnownFact & {
  id: string
  kind: "PNG" | "SVG" | "PDF" | "CODE" | "LOG" | "OTHER"
  label: string
  sha256: string | null
  downloadable: boolean
  masked: boolean
}

export type AnalysisRunViewModel = KnownFact & {
  id: string
  projectId: string
  planId: string
  datasetVersionId: string
  approvalId: string
  runNumber: number
  jobId: string | null
  effectiveN: number | null
  inputHash: string
  parametersHash: string
  environmentHash: string | null
  environment: Readonly<Record<string, string>>
  resultCount: number
  errorCode: string | null
  invalidationReason: string | null
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type ResultValue =
  | string
  | number
  | boolean
  | null
  | readonly ResultValue[]
  | { readonly [key: string]: ResultValue }

export type AnalysisResultViewModel = KnownFact & {
  id: string
  runId: string
  key: string
  type: string
  schemaVersion: string
  primary: boolean
  payload: Readonly<Record<string, ResultValue>>
  resultHash: string
  deterministic: true
  interpretation: null
  createdAt: string
}

export type FigureChartType =
  | "SCATTER"
  | "GROUP_COMPARISON"
  | "HISTOGRAM"
  | "BOXPLOT"
  | "CORRELATION_MATRIX"

export type FigurePlanInput = {
  datasetVersionId: string
  analysisRunId: string | null
  analysisResultId: string | null
  chartType: FigureChartType
  parameters: Readonly<Record<string, ResultValue>>
  caption: string
}

export type FigurePlanViewModel = KnownFact & {
  id: string
  projectId: string
  datasetVersionId: string
  analysisRunId: string | null
  analysisResultId: string | null
  chartType: FigureChartType
  caption: string
  parameters: Readonly<Record<string, ResultValue>>
  planHash: string
  lockVersion: number
  invalidationReason: string | null
  transportAvailable: true
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type FigureRenderRunViewModel = KnownFact & {
  id: string
  projectId: string
  figurePlanId: string
  datasetVersionId: string
  jobId: string | null
  figureId: string | null
  renderNumber: number
  inputHash: string
  parametersHash: string
  environmentHash: string | null
  errorCode: string | null
  retryable: boolean
  transportAvailable: true
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type FigureValidationIssueViewModel = KnownFact & {
  id: string
  issueType: string
  severity: "ERROR" | "WARNING" | "INFO"
  message: string
  blocksConfirmation: boolean
}

export type FigureViewModel = KnownFact & {
  id: string
  projectId: string
  figurePlanId: string
  renderRunId: string
  datasetVersionId: string
  analysisRunId: string | null
  analysisResultId: string | null
  versionNumber: number
  chartType: FigureChartType
  caption: string
  aggregateHash: string
  confirmationApprovalId: string | null
  approvalStale: boolean
  invalidationReason: string | null
  issues: readonly FigureValidationIssueViewModel[]
  artifacts: readonly ArtifactReferenceViewModel[]
  transportAvailable: true
  permissionsKnown: boolean
  allowedActions: ReadonlySet<string>
}

export type SuggestionViewModel = {
  kind: "METHOD" | "FIGURE" | "INTERPRETATION"
  availability: "DEGRADED" | "UNAVAILABLE"
  deterministic: false
  text: string | null
  reason: string
}

export type AnalysisWorkspaceViewModel = {
  projectId: string
  dataset: DatasetContextViewModel | null
  columns: readonly ColumnContextViewModel[]
  qualityWarnings: readonly string[]
  plan: AnalysisPlanViewModel | null
  approval: ApprovalViewModel | null
  run: AnalysisRunViewModel | null
  results: readonly AnalysisResultViewModel[]
  job: JobViewModel | null
  figurePlan: FigurePlanViewModel | null
  renderRun: FigureRenderRunViewModel | null
  figure: FigureViewModel | null
  suggestions: readonly SuggestionViewModel[]
  capabilities: AnalysisWorkspaceCapabilities
  readScopes: readonly string[]
  integrationPending: readonly string[]
}
