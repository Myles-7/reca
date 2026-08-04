import type { UiErrorViewModel } from "../../projects/model"
import type { DataWorkspaceViewModel } from "../model"
import type { DataWorkspaceWorkspaceProps } from "../ui/contracts"

const noop = () => undefined
const noEvent: DataWorkspaceWorkspaceProps["onEvent"] = () => undefined
const allowed = (value: boolean, reason: string) => ({
  allowed: value,
  disabledReason: value ? null : reason,
})
const actions = (...values: string[]) => new Set(values)

const readyData: DataWorkspaceViewModel = {
  projectId: "project-m4-design",
  datasets: [
    {
      id: "dataset-survey-2026",
      name: "Learning engagement survey 2026",
      currentVersionId: "version-cleaned-2",
      sourceType: "USER_UPLOAD",
      licenseStatus: "UNKNOWN",
      licenseWarning: "LICENSE_UNKNOWN",
      updatedAt: "2026-08-04T08:00:00Z",
      status: "ACTIVE",
      knownStatus: true,
      tone: "info",
    },
  ],
  dataset: {
    id: "dataset-survey-2026",
    projectId: "project-m4-design",
    name: "Learning engagement survey 2026",
    description: "De-identified classroom engagement observations.",
    publisher: "RECA demonstration team",
    sourcePlatform: null,
    sourceIdentifier: "survey-2026-cohort-a",
    doi: null,
    licenseName: null,
    licenseStatus: "UNKNOWN",
    licenseWarning: "LICENSE_UNKNOWN",
    recommendedCitation: null,
    knownLimitations:
      "Convenience sample; extreme values are review clues only.",
    currentVersionId: "version-cleaned-2",
    lockVersion: 3,
    status: "ACTIVE",
    knownStatus: true,
    tone: "info",
  },
  version: {
    id: "version-cleaned-2",
    datasetId: "dataset-survey-2026",
    versionNumber: 2,
    versionType: "CLEANED",
    fileFormat: "CSV",
    artifactId: "artifact-cleaned-2",
    parentVersionId: "version-original-1",
    transformationId: "transformation-2",
    current: true,
    original: false,
    invalidated: false,
    rowCount: 1248,
    columnCount: 8,
    dataHash: "4f".repeat(32),
    schemaHash: "5a".repeat(32),
    projectionHash: "6b".repeat(32),
    selectedWorksheetName: null,
    worksheets: [],
    invalidationReason: null,
    createdAt: "2026-08-04T07:30:00Z",
    status: "AVAILABLE",
    knownStatus: true,
    tone: "success",
  },
  versions: [],
  columns: [
    {
      id: "column-student-id-very-long-identifier-000000000000000001",
      sourceName: "student_number",
      displayName: "Student number",
      inferredType: "STRING",
      confirmedType: "STRING",
      semanticRole: "ID",
      unit: null,
      description: "Pseudonymous participant identifier.",
      confirmationStatus: "CONFIRMED",
      confirmationKnown: true,
      uniqueCount: 1248,
      missingRatio: 0,
      exampleValues: ["***", "***"],
      sensitiveCandidate: false,
      sensitiveConfirmed: true,
      inheritedFromColumnId: "column-student-id-original",
      lockVersion: 2,
    },
    {
      id: "column-score",
      sourceName: "engagement_score",
      displayName: "Engagement score",
      inferredType: "NUMERIC",
      confirmedType: null,
      semanticRole: "DEPENDENT_VARIABLE",
      unit: "points",
      description: null,
      confirmationStatus: "NEEDS_REVIEW",
      confirmationKnown: true,
      uniqueCount: 47,
      missingRatio: 0.0385,
      exampleValues: ["18", "22", "95"],
      sensitiveCandidate: false,
      sensitiveConfirmed: false,
      inheritedFromColumnId: "column-score-original",
      lockVersion: 1,
    },
  ],
  preview: {
    columns: ["student_number", "engagement_score"],
    rows: [
      { student_number: "***", engagement_score: "18" },
      { student_number: "***", engagement_score: "95" },
    ],
    returned: 2,
    totalRows: 1248,
    truncated: true,
    masked: true,
  },
  qualityRun: {
    id: "quality-run-2",
    versionId: "version-cleaned-2",
    rulesetId: "RECA_P0_DEFAULT",
    rulesetVersion: "1.0.0",
    rulesetHash: "7c".repeat(32),
    issueCount: 3,
    highIssueCount: 0,
    jobId: "job-quality-2",
    errorCode: null,
    degraded: false,
    permissionsKnown: true,
    allowedActions: actions("data_quality_run.read"),
    status: "COMPLETED",
    knownStatus: true,
    tone: "success",
  },
  issues: [
    {
      id: "issue-missing-score",
      ruleCode: "missing_value",
      issueType: "MISSING_VALUE",
      severity: "MEDIUM",
      columnId: "column-score",
      affectedRowCount: 48,
      description: "Some engagement score cells are missing.",
      clueOnly: false,
      sensitiveCandidate: false,
      sensitiveConfirmed: false,
      exampleSummary: ["row 18", "row 42"],
      requiresApproval: false,
      permissionsKnown: true,
      allowedActions: actions(
        "data_quality_issue.acknowledge",
        "data_quality_issue.ignore",
      ),
      status: "OPEN",
      knownStatus: true,
      tone: "info",
    },
    {
      id: "issue-extreme-score",
      ruleCode: "extreme_value_iqr",
      issueType: "EXTREME_VALUE",
      severity: "LOW",
      columnId: "column-score",
      affectedRowCount: 5,
      description: "A small set of values are extreme-value clues for review.",
      clueOnly: true,
      sensitiveCandidate: false,
      sensitiveConfirmed: false,
      exampleSummary: ["95", "97"],
      requiresApproval: false,
      permissionsKnown: true,
      allowedActions: actions("data_quality_issue.acknowledge"),
      status: "OPEN",
      knownStatus: true,
      tone: "info",
    },
    {
      id: "issue-sensitive-student-number",
      ruleCode: "possible_sensitive_field",
      issueType: "POSSIBLE_SENSITIVE_FIELD",
      severity: "MEDIUM",
      columnId: "column-student-id-very-long-identifier-000000000000000001",
      affectedRowCount: 1248,
      description: "The field name matches a sensitive-data candidate pattern.",
      clueOnly: false,
      sensitiveCandidate: true,
      sensitiveConfirmed: false,
      exampleSummary: ["[MASKED]"],
      requiresApproval: false,
      permissionsKnown: true,
      allowedActions: actions("data_quality_issue.acknowledge"),
      status: "OPEN",
      knownStatus: true,
      tone: "info",
    },
  ],
  plan: {
    id: "cleaning-plan-2",
    versionId: "version-original-1",
    title: "Normalize category labels and missing score codes",
    rationale: "Apply only deterministic, reviewed actions.",
    actionCount: 2,
    actions: [
      { type: "MAP_CATEGORY", reason: "Normalize labels", targetCount: 1 },
      { type: "MARK_MISSING", reason: "Recognize N/A", targetCount: 1 },
    ],
    editorActions: [
      {
        type: "MAP_CATEGORY",
        targetColumnIds: ["column-arm"],
        rowSelector: { type: "ALL_ROWS" },
        reason: "Normalize labels",
        sourceIssueIds: [],
        parameters: { mapping: { Control: "control", Treatment: "treatment" } },
      },
      {
        type: "MARK_MISSING",
        targetColumnIds: ["column-score"],
        rowSelector: { type: "ALL_ROWS" },
        reason: "Recognize N/A",
        sourceIssueIds: ["issue-missing-score"],
        parameters: { replacement: null },
      },
    ],
    actionsEditable: true,
    actionsDisabledReason: null,
    preview: {
      hash: "8d".repeat(32),
      affectedRows: 52,
      affectedColumns: 2,
      rowCountBefore: 1248,
      rowCountAfter: 1248,
      warnings: [],
      risk: "MEDIUM",
      readyForApproval: true,
    },
    approvalRecordId: "approval-plan-2",
    approvalPayloadHash: "9e".repeat(32),
    transformationId: "transformation-2",
    jobId: "job-transform-2",
    lockVersion: 4,
    permissionsKnown: true,
    allowedActions: actions(),
    status: "COMPLETED",
    knownStatus: true,
    tone: "success",
  },
  approval: {
    id: "approval-plan-2",
    expiresAt: "2026-08-05T08:00:00Z",
    expired: false,
    stale: false,
    decisionReason: "Preview and impact reviewed.",
    permissionsKnown: true,
    allowedActions: actions(),
    status: "APPROVED",
    knownStatus: true,
    tone: "success",
  },
  transformation: {
    id: "transformation-2",
    sourceVersionId: "version-original-1",
    targetVersionId: "version-cleaned-2",
    outputArtifactId: "artifact-cleaned-2",
    affectedRows: 52,
    affectedColumns: 2,
    errorCode: null,
    status: "COMPLETED",
    knownStatus: true,
    tone: "success",
  },
  job: {
    id: "job-transform-2",
    accepted: true,
    queued: false,
    running: false,
    completed: true,
    failed: false,
    retryable: false,
    progress: 100,
    currentStep: "Promotion complete",
    errorCode: null,
    status: "COMPLETED",
    knownStatus: true,
    tone: "success",
  },
  comparison: {
    baseVersionId: "version-original-1",
    targetVersionId: "version-cleaned-2",
    rowDelta: 0,
    columnDelta: 0,
    missingBefore: 64,
    missingAfter: 48,
    affectedRows: 52,
    affectedColumns: 2,
    actionTypes: ["MAP_CATEGORY", "MARK_MISSING"],
    parentVersionId: "version-original-1",
    transformationId: "transformation-2",
    outputArtifactId: "artifact-cleaned-2",
  },
  capabilities: {
    permissionsKnown: true,
    uploadDataset: allowed(true, ""),
    selectWorksheet: allowed(
      false,
      "The selected version is already AVAILABLE.",
    ),
    updateDatasetIdentity: allowed(true, ""),
    updateColumn: allowed(true, ""),
    runQuality: allowed(true, ""),
    acknowledgeIssue: allowed(true, ""),
    ignoreIssue: allowed(true, ""),
    createPlan: allowed(true, ""),
    updatePlan: allowed(false, "Completed plans are immutable."),
    previewPlan: allowed(false, "Completed plans cannot be previewed again."),
    requestApproval: allowed(false, "The plan already has a decision."),
    executePlan: allowed(false, "The transformation is complete."),
    compareVersions: allowed(true, ""),
    retryJob: allowed(false, "Completed Jobs cannot be retried."),
  },
  integrationPending: [],
}

const baseProps: DataWorkspaceWorkspaceProps = {
  content: { state: "ready", data: readyData },
  pendingAction: null,
  mutationError: null,
  onRetry: noop,
  onEvent: noEvent,
}

const error = (
  code: string,
  options: Partial<UiErrorViewModel> = {},
): UiErrorViewModel => ({
  title: code,
  message: "The data workspace could not load this contract fixture.",
  code,
  requestId: `request-${code.toLowerCase()}`,
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
  ...options,
})

const readyFixture = (
  data: DataWorkspaceViewModel,
): DataWorkspaceWorkspaceProps => ({
  ...baseProps,
  content: { state: "ready", data },
})

const withStatus = <K extends keyof DataWorkspaceViewModel>(
  key: K,
  value: DataWorkspaceViewModel[K],
) => readyFixture({ ...readyData, [key]: value })

export const dataWorkspaceReadyFixture = baseProps
export const dataWorkspaceLoadingFixture = {
  ...baseProps,
  content: { state: "loading", label: "Loading data workspace" },
} satisfies DataWorkspaceWorkspaceProps
export const dataWorkspaceEmptyFixture = readyFixture({
  ...readyData,
  datasets: [],
  dataset: null,
  version: null,
  versions: [],
  columns: [],
  preview: null,
  qualityRun: null,
  issues: [],
  plan: null,
  approval: null,
  transformation: null,
  job: null,
  comparison: null,
  capabilities: {
    ...readyData.capabilities,
    uploadDataset: allowed(true, ""),
    selectWorksheet: allowed(
      false,
      "Upload a workbook before selecting a worksheet.",
    ),
    updateDatasetIdentity: allowed(false, "No Dataset exists yet."),
    updateColumn: allowed(false, "No DatasetVersion exists yet."),
    runQuality: allowed(false, "No AVAILABLE DatasetVersion exists yet."),
    acknowledgeIssue: allowed(false, "No quality Issue is selected."),
    ignoreIssue: allowed(false, "No quality Issue is selected."),
    createPlan: allowed(false, "No AVAILABLE DatasetVersion exists yet."),
    updatePlan: allowed(false, "No CleaningPlan exists yet."),
    previewPlan: allowed(false, "No CleaningPlan exists yet."),
    requestApproval: allowed(false, "No CleaningPlan exists yet."),
    executePlan: allowed(false, "No approved CleaningPlan exists yet."),
    compareVersions: allowed(
      false,
      "At least two DatasetVersions are required.",
    ),
    retryJob: allowed(false, "No failed Job exists."),
  },
})
export const dataWorkspaceErrorFixture = {
  ...baseProps,
  content: { state: "error", error: error("DATA_WORKSPACE_LOAD_FAILED") },
} satisfies DataWorkspaceWorkspaceProps
export const dataWorkspaceForbiddenFixture = {
  ...baseProps,
  content: {
    state: "error",
    error: error("RESOURCE_NOT_FOUND", {
      retryable: false,
      forbidden: true,
      notFound: true,
    }),
  },
} satisfies DataWorkspaceWorkspaceProps
export const dataWorkspaceReadOnlyFixture = readyFixture({
  ...readyData,
  capabilities: Object.fromEntries(
    Object.keys(readyData.capabilities).map((key) =>
      key === "permissionsKnown"
        ? [key, true]
        : [key, allowed(false, "Read-only role.")],
    ),
  ) as DataWorkspaceViewModel["capabilities"],
})
export const dataWorkspacePermissionsUnknownFixture = readyFixture({
  ...readyData,
  capabilities: Object.fromEntries(
    Object.keys(readyData.capabilities).map((key) =>
      key === "permissionsKnown"
        ? [key, false]
        : [key, allowed(false, "Permissions are unknown.")],
    ),
  ) as DataWorkspaceViewModel["capabilities"],
})
export const dataWorkspaceUploadPendingFixture = {
  ...baseProps,
  pendingAction: "upload-dataset",
} satisfies DataWorkspaceWorkspaceProps
export const dataWorkspaceUploadFailureFixture = {
  ...baseProps,
  mutationError: error("INVALID_WORKBOOK", { retryable: false }),
} satisfies DataWorkspaceWorkspaceProps
export const dataWorkspaceXlsxFixture = readyFixture({
  ...readyData,
  version: {
    ...readyData.version!,
    id: "version-workbook",
    fileFormat: "XLSX",
    status: "CREATING",
    tone: "info",
    current: false,
    selectedWorksheetName: null,
    worksheets: [
      {
        name: "Survey",
        ordinal: 1,
        visibility: "VISIBLE",
        estimatedRows: 1248,
        estimatedColumns: 8,
        selected: false,
        warnings: [],
      },
      {
        name: "Archive",
        ordinal: 2,
        visibility: "HIDDEN",
        estimatedRows: 418,
        estimatedColumns: 8,
        selected: false,
        warnings: ["HIDDEN_WORKSHEET"],
      },
    ],
  },
  capabilities: {
    ...readyData.capabilities,
    selectWorksheet: allowed(true, ""),
    updateColumn: allowed(
      false,
      "Select a worksheet before confirming columns.",
    ),
    runQuality: allowed(false, "Quality requires an AVAILABLE DatasetVersion."),
    createPlan: allowed(
      false,
      "Plan creation requires an AVAILABLE DatasetVersion.",
    ),
    compareVersions: allowed(
      false,
      "The workbook version is not AVAILABLE yet.",
    ),
  },
})
export const dataWorkspaceInvalidatedFixture = withStatus("version", {
  ...readyData.version!,
  id: "version-invalidated",
  status: "INVALIDATED",
  tone: "danger",
  current: false,
  invalidated: true,
  invalidationReason: "Source correction required",
})
export const dataWorkspaceQualityQueuedFixture = withStatus("qualityRun", {
  ...readyData.qualityRun!,
  status: "QUEUED",
  tone: "info",
  issueCount: 0,
  highIssueCount: 0,
})
export const dataWorkspaceQualityRunningFixture = withStatus("qualityRun", {
  ...readyData.qualityRun!,
  status: "RUNNING",
  tone: "info",
  issueCount: 0,
  highIssueCount: 0,
})
export const dataWorkspaceQualityFailedFixture = withStatus("qualityRun", {
  ...readyData.qualityRun!,
  status: "FAILED",
  tone: "danger",
  degraded: true,
  errorCode: "DATASET_HASH_MISMATCH",
})
export const dataWorkspaceQualityUnknownFixture = withStatus("qualityRun", {
  ...readyData.qualityRun!,
  status: "FUTURE_QUALITY_STATE",
  knownStatus: false,
  tone: "degraded",
  degraded: true,
  permissionsKnown: false,
  allowedActions: actions(),
})
export const dataWorkspacePlanDraftFixture = readyFixture({
  ...readyData,
  plan: {
    ...readyData.plan!,
    versionId: readyData.version!.id,
    status: "DRAFT",
    tone: "info",
    preview: null,
    approvalRecordId: null,
    transformationId: null,
    jobId: null,
    allowedActions: actions("cleaning_plan.update", "cleaning_plan.preview"),
  },
  approval: null,
  transformation: null,
  job: null,
  capabilities: {
    ...readyData.capabilities,
    updatePlan: allowed(true, ""),
    previewPlan: allowed(true, ""),
    requestApproval: allowed(false, "A READY Preview is required."),
    executePlan: allowed(false, "An effective Approval is required."),
  },
})
export const dataWorkspacePlanNeedsInputFixture = readyFixture({
  ...readyData,
  plan: {
    ...readyData.plan!,
    versionId: readyData.version!.id,
    status: "NEEDS_INPUT",
    tone: "warning",
    preview: null,
    approvalRecordId: null,
    allowedActions: actions("cleaning_plan.update", "cleaning_plan.preview"),
  },
  approval: null,
  transformation: null,
  job: null,
  capabilities: {
    ...readyData.capabilities,
    updatePlan: allowed(true, ""),
    previewPlan: allowed(true, ""),
    requestApproval: allowed(false, "Resolve Plan input before Approval."),
    executePlan: allowed(false, "An effective Approval is required."),
  },
})
export const dataWorkspacePlanReadyFixture = readyFixture({
  ...readyData,
  plan: {
    ...readyData.plan!,
    versionId: readyData.version!.id,
    status: "READY",
    tone: "info",
    approvalRecordId: null,
    transformationId: null,
    jobId: null,
    allowedActions: actions("cleaning_plan.request_approval"),
  },
  approval: null,
  transformation: null,
  job: null,
  capabilities: {
    ...readyData.capabilities,
    updatePlan: allowed(
      false,
      "READY plans are immutable until state changes.",
    ),
    previewPlan: allowed(false, "The current Preview is already READY."),
    requestApproval: allowed(true, ""),
    executePlan: allowed(false, "An effective Approval is required."),
  },
})
export const dataWorkspaceApprovalPendingFixture = readyFixture({
  ...readyData,
  plan: {
    ...readyData.plan!,
    versionId: readyData.version!.id,
    status: "NEEDS_APPROVAL",
    tone: "warning",
    transformationId: null,
    jobId: null,
    allowedActions: actions(),
  },
  approval: {
    ...readyData.approval!,
    status: "PENDING",
    tone: "warning",
    decisionReason: null,
  },
  transformation: null,
  job: null,
  capabilities: {
    ...readyData.capabilities,
    updatePlan: allowed(false, "Approval is pending."),
    previewPlan: allowed(false, "Approval is pending."),
    requestApproval: allowed(false, "Approval is already pending."),
    executePlan: allowed(false, "Approval has not been granted."),
  },
})
export const dataWorkspaceApprovalRejectedFixture = readyFixture({
  ...readyData,
  plan: {
    ...readyData.plan!,
    versionId: readyData.version!.id,
    status: "REJECTED",
    tone: "danger",
    transformationId: null,
    jobId: null,
    allowedActions: actions(),
  },
  approval: {
    ...readyData.approval!,
    status: "REJECTED",
    tone: "danger",
    decisionReason: "Impact was not acceptable.",
  },
  transformation: null,
  job: null,
  capabilities: {
    ...readyData.capabilities,
    updatePlan: allowed(
      false,
      "Rejected plans cannot be edited in this state.",
    ),
    previewPlan: allowed(
      false,
      "Rejected plans cannot be previewed in this state.",
    ),
    requestApproval: allowed(false, "The Approval was rejected."),
    executePlan: allowed(false, "Rejected plans cannot execute."),
  },
})
export const dataWorkspaceApprovalStaleFixture = readyFixture({
  ...readyData,
  plan: {
    ...readyData.plan!,
    versionId: readyData.version!.id,
    status: "APPROVED",
    tone: "success",
    transformationId: null,
    jobId: null,
    allowedActions: actions("cleaning_plan.execute"),
  },
  approval: {
    ...readyData.approval!,
    status: "STALE",
    tone: "danger",
    stale: true,
  },
  transformation: null,
  job: null,
  capabilities: {
    ...readyData.capabilities,
    updatePlan: allowed(false, "Approved plans are immutable."),
    previewPlan: allowed(false, "Approved plans cannot be previewed again."),
    requestApproval: allowed(false, "The plan already has an Approval."),
    executePlan: allowed(false, "The Approval payload is stale."),
  },
})
export const dataWorkspaceConflictFixture = {
  ...baseProps,
  mutationError: error("RESOURCE_VERSION_CONFLICT", {
    retryable: false,
    conflict: true,
  }),
} satisfies DataWorkspaceWorkspaceProps
export const dataWorkspaceTransformQueuedFixture = readyFixture({
  ...readyData,
  transformation: {
    ...readyData.transformation!,
    status: "QUEUED",
    tone: "info",
    targetVersionId: null,
    outputArtifactId: null,
  },
  job: {
    ...readyData.job!,
    status: "QUEUED",
    tone: "info",
    queued: true,
    completed: false,
    progress: 0,
  },
})
export const dataWorkspaceTransformRunningFixture = readyFixture({
  ...readyData,
  transformation: {
    ...readyData.transformation!,
    status: "RUNNING",
    tone: "info",
    targetVersionId: null,
    outputArtifactId: null,
  },
  job: {
    ...readyData.job!,
    status: "RUNNING",
    tone: "info",
    running: true,
    completed: false,
    progress: 46,
    currentStep: "Validating staged output",
  },
})
export const dataWorkspaceTransformFailedFixture = readyFixture({
  ...readyData,
  transformation: {
    ...readyData.transformation!,
    status: "FAILED",
    tone: "danger",
    targetVersionId: null,
    outputArtifactId: null,
    errorCode: "TRANSFORMATION_PARAMETERS_STALE",
  },
  job: {
    ...readyData.job!,
    status: "FAILED",
    tone: "danger",
    failed: true,
    completed: false,
    retryable: true,
    errorCode: "TRANSFORMATION_PARAMETERS_STALE",
  },
  capabilities: { ...readyData.capabilities, retryJob: allowed(true, "") },
})
export const dataWorkspaceFutureEnumFixture = readyFixture({
  ...readyData,
  version: {
    ...readyData.version!,
    status: "FUTURE_VERSION_STATE",
    knownStatus: false,
    tone: "degraded",
    current: false,
  },
  plan: {
    ...readyData.plan!,
    status: "FUTURE_PLAN_STATE",
    knownStatus: false,
    tone: "degraded",
    permissionsKnown: false,
    allowedActions: actions(),
  },
  job: {
    ...readyData.job!,
    status: "FUTURE_JOB_STATE",
    knownStatus: false,
    tone: "degraded",
    retryable: false,
  },
  capabilities:
    dataWorkspacePermissionsUnknownFixture.content.state === "ready"
      ? dataWorkspacePermissionsUnknownFixture.content.data.capabilities
      : readyData.capabilities,
})
export const dataWorkspaceLongContentFixture = readyFixture({
  ...readyData,
  dataset: {
    ...readyData.dataset!,
    name: "Longitudinal multidisciplinary student engagement measurement workbook with harmonized classroom observation metadata",
    knownLimitations:
      "This intentionally long fixture verifies that filenames, identifiers, column labels, license warnings, lineage hashes, descriptions and action reasons wrap without obscuring adjacent controls.",
  },
  columns: Array.from({ length: 18 }, (_, index) => ({
    ...readyData.columns[index % readyData.columns.length],
    id: `column-${index}-${"x".repeat(42)}`,
    sourceName: `extremely_long_imported_column_name_for_measurement_wave_${index + 1}`,
    displayName: `Long display label for measurement wave ${index + 1}`,
  })),
})

export const dataWorkspaceFixtures = [
  ["ready", "Ready", dataWorkspaceReadyFixture],
  ["loading", "Loading", dataWorkspaceLoadingFixture],
  ["empty", "Empty", dataWorkspaceEmptyFixture],
  ["error", "Error", dataWorkspaceErrorFixture],
  ["forbidden", "Forbidden / no disclosure", dataWorkspaceForbiddenFixture],
  ["read-only", "Read only", dataWorkspaceReadOnlyFixture],
  [
    "permissions-unknown",
    "Permissions unknown",
    dataWorkspacePermissionsUnknownFixture,
  ],
  ["upload-pending", "Upload pending", dataWorkspaceUploadPendingFixture],
  ["upload-failure", "Upload failure", dataWorkspaceUploadFailureFixture],
  ["xlsx-worksheets", "XLSX worksheets", dataWorkspaceXlsxFixture],
  ["invalidated", "Invalidated version", dataWorkspaceInvalidatedFixture],
  ["quality-queued", "Quality queued", dataWorkspaceQualityQueuedFixture],
  ["quality-running", "Quality running", dataWorkspaceQualityRunningFixture],
  ["quality-failed", "Quality failed", dataWorkspaceQualityFailedFixture],
  ["quality-unknown", "Quality unknown", dataWorkspaceQualityUnknownFixture],
  ["plan-draft", "Plan draft", dataWorkspacePlanDraftFixture],
  ["plan-needs-input", "Plan needs input", dataWorkspacePlanNeedsInputFixture],
  ["plan-ready", "Plan Preview ready", dataWorkspacePlanReadyFixture],
  ["approval-pending", "Approval pending", dataWorkspaceApprovalPendingFixture],
  [
    "approval-rejected",
    "Approval rejected",
    dataWorkspaceApprovalRejectedFixture,
  ],
  ["approval-stale", "Approval stale", dataWorkspaceApprovalStaleFixture],
  ["conflict", "If-Match conflict", dataWorkspaceConflictFixture],
  [
    "transform-queued",
    "Transformation queued",
    dataWorkspaceTransformQueuedFixture,
  ],
  [
    "transform-running",
    "Transformation running",
    dataWorkspaceTransformRunningFixture,
  ],
  [
    "transform-failed",
    "Transformation failed",
    dataWorkspaceTransformFailedFixture,
  ],
  ["future-enums", "Future enums fail closed", dataWorkspaceFutureEnumFixture],
  ["long-content", "Long content", dataWorkspaceLongContentFixture],
  ["desktop-light", "Desktop light", dataWorkspaceReadyFixture],
  ["tablet-dark", "Tablet dark", dataWorkspaceReadyFixture],
  ["mobile-light", "Mobile light", dataWorkspaceReadyFixture],
].map(([id, label, props]) => ({
  id,
  label,
  behavior: `M4 ${label} contract fixture.`,
  props,
})) as ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: DataWorkspaceWorkspaceProps
}>
