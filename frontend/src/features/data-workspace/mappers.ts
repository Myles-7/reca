import type {
  ApprovalPublic,
  CleaningPlanDto,
  DataQualityIssueDto,
  DataQualityRunDto,
  DatasetColumnDto,
  DatasetDto,
  DatasetPreviewDto,
  DatasetVersionDto,
  DataTransformationDto,
  JobPublic,
  ProjectPublic,
  VersionComparisonDto,
} from "@/api/adapter"

import type {
  ActionCapability,
  ApprovalViewModel,
  CleaningActionInput,
  CleaningLiteralValue,
  CleaningPlanViewModel,
  CleaningRowSelector,
  DatasetColumnViewModel,
  DatasetIdentityViewModel,
  DatasetListItemViewModel,
  DatasetPreviewViewModel,
  DatasetVersionViewModel,
  DataWorkspaceCapabilities,
  DataWorkspaceViewModel,
  JobStateViewModel,
  KnownFact,
  QualityIssueViewModel,
  QualityRunViewModel,
  TransformationViewModel,
  VersionComparisonViewModel,
} from "./model"

const datasetStatuses = new Set(["ACTIVE", "ARCHIVED", "DELETED"])
const versionStatuses = new Set([
  "CREATING",
  "AVAILABLE",
  "FAILED",
  "INVALIDATED",
])
const runStatuses = new Set([
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "FAILED",
  "INVALIDATED",
])
const issueStatuses = new Set([
  "OPEN",
  "ACKNOWLEDGED",
  "IGNORED",
  "RESOLVED",
  "INVALIDATED",
])
const planStatuses = new Set([
  "DRAFT",
  "NEEDS_INPUT",
  "READY",
  "NEEDS_APPROVAL",
  "APPROVED",
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "REJECTED",
  "FAILED",
  "INVALIDATED",
])
const transformationStatuses = new Set([
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "FAILED",
])
const approvalStatuses = new Set([
  "PENDING",
  "APPROVED",
  "REJECTED",
  "CANCELLED",
  "EXPIRED",
  "SUPERSEDED",
])
const jobStatuses = new Set([
  "DRAFT",
  "QUEUED",
  "RUNNING",
  "NEEDS_REVIEW",
  "COMPLETED",
  "FAILED",
  "CANCEL_REQUESTED",
  "CANCELLED",
  "DISPATCH_FAILED",
])
const confirmationStatuses = new Set([
  "UNCONFIRMED",
  "INFERRED",
  "NEEDS_REVIEW",
  "CONFIRMED",
])

function fact(status: string, known: boolean): KnownFact {
  return {
    status,
    knownStatus: known,
    tone: !known
      ? "degraded"
      : status === "COMPLETED" ||
          status === "AVAILABLE" ||
          status === "APPROVED"
        ? "success"
        : status === "FAILED" ||
            status === "REJECTED" ||
            status === "INVALIDATED" ||
            status === "EXPIRED"
          ? "danger"
          : status === "NEEDS_INPUT" ||
              status === "NEEDS_APPROVAL" ||
              status === "NEEDS_REVIEW"
            ? "warning"
            : "info",
  }
}

function capability(allowed: boolean, reason: string): ActionCapability {
  return { allowed, disabledReason: allowed ? null : reason }
}

function actions(value: readonly string[] | undefined) {
  return Array.isArray(value) ? new Set(value) : new Set<string>()
}

export function mapDatasetListItem(dto: DatasetDto): DatasetListItemViewModel {
  return {
    ...fact(dto.status, datasetStatuses.has(dto.status)),
    id: dto.id,
    name: dto.name,
    currentVersionId: dto.current_version_id,
    sourceType: dto.source_type,
    licenseStatus: dto.license_status,
    licenseWarning: dto.license_warning,
    updatedAt: dto.updated_at,
  }
}

export function mapDataset(dto: DatasetDto): DatasetIdentityViewModel {
  return {
    ...fact(dto.status, datasetStatuses.has(dto.status)),
    id: dto.id,
    projectId: dto.project_id,
    name: dto.name,
    description: dto.description,
    publisher: dto.publisher,
    sourcePlatform: dto.source_platform,
    sourceIdentifier: dto.source_identifier,
    doi: dto.doi,
    licenseName: dto.license_name,
    licenseStatus: dto.license_status,
    licenseWarning: dto.license_warning,
    recommendedCitation: dto.recommended_citation,
    knownLimitations: dto.known_limitations?.join("\n") ?? null,
    currentVersionId: dto.current_version_id,
    lockVersion: dto.lock_version,
  }
}

export function mapDatasetVersion(
  dto: DatasetVersionDto,
  currentVersionId: string | null,
): DatasetVersionViewModel {
  return {
    ...fact(dto.status, versionStatuses.has(dto.status)),
    id: dto.id,
    datasetId: dto.dataset_id,
    versionNumber: dto.version_number,
    versionType: dto.version_type,
    fileFormat: dto.file_format,
    artifactId: dto.artifact_id,
    parentVersionId: dto.parent_version_id,
    transformationId: dto.transformation_id,
    current: dto.id === currentVersionId && dto.status === "AVAILABLE",
    original: dto.version_type === "ORIGINAL",
    invalidated: dto.status === "INVALIDATED",
    rowCount: dto.row_count,
    columnCount: dto.column_count,
    dataHash: dto.data_hash,
    schemaHash: dto.schema_hash,
    projectionHash: dto.projection_hash,
    selectedWorksheetName: dto.selected_worksheet_name,
    worksheets: (dto.worksheet_manifest ?? []).map((sheet) => ({
      name: sheet.name,
      ordinal: sheet.ordinal,
      visibility:
        sheet.visibility === "VISIBLE" ||
        sheet.visibility === "HIDDEN" ||
        sheet.visibility === "VERY_HIDDEN"
          ? sheet.visibility
          : "UNKNOWN",
      estimatedRows: sheet.estimated_rows,
      estimatedColumns: sheet.estimated_columns,
      selected: sheet.name === dto.selected_worksheet_name,
      warnings: sheet.warnings ?? [],
    })),
    invalidationReason: dto.invalidation_reason,
    createdAt: dto.created_at,
  }
}

export function mapDatasetColumn(
  dto: DatasetColumnDto,
): DatasetColumnViewModel {
  const examples = (dto.example_values ?? [])
    .slice(0, 5)
    .map((value) => (dto.is_sensitive ? "***" : String(value ?? "")))
  return {
    id: dto.id,
    sourceName: dto.source_name,
    displayName: dto.display_name,
    inferredType: dto.inferred_type,
    confirmedType: dto.confirmed_type,
    semanticRole: dto.semantic_role,
    unit: dto.unit,
    description: dto.description,
    confirmationStatus: dto.confirmation_status,
    confirmationKnown: confirmationStatuses.has(dto.confirmation_status),
    uniqueCount: dto.unique_count,
    missingRatio: dto.missing_ratio,
    exampleValues: examples,
    sensitiveCandidate:
      dto.is_sensitive && dto.confirmation_status !== "CONFIRMED",
    sensitiveConfirmed:
      dto.is_sensitive && dto.confirmation_status === "CONFIRMED",
    inheritedFromColumnId: dto.inherited_from_column_id,
    lockVersion: dto.lock_version,
  }
}

export function mapDatasetPreview(
  dto: DatasetPreviewDto,
): DatasetPreviewViewModel {
  return {
    columns: dto.columns,
    rows: dto.rows.map((row) =>
      Object.fromEntries(
        Object.entries(row).map(([key, value]) => [key, String(value ?? "")]),
      ),
    ),
    returned: dto.returned,
    totalRows: dto.total_rows,
    truncated: dto.truncated,
    masked: dto.rows.some((row) => Object.values(row).includes("***")),
  }
}

export function mapQualityRun(dto: DataQualityRunDto): QualityRunViewModel {
  const allowedActions = actions(dto.allowed_actions)
  const knownStatus = runStatuses.has(dto.status)
  return {
    ...fact(dto.status, knownStatus),
    id: dto.id,
    versionId: dto.dataset_version_id,
    rulesetId: dto.ruleset_id,
    rulesetVersion: dto.ruleset_version,
    rulesetHash: dto.ruleset_hash,
    issueCount: dto.issue_count,
    highIssueCount: dto.high_issue_count,
    jobId: dto.job_id,
    errorCode: dto.error_code,
    degraded: !knownStatus || dto.error_code !== null,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions,
  }
}

export function mapQualityIssue(
  dto: DataQualityIssueDto,
): QualityIssueViewModel {
  const allowedActions = actions(dto.allowed_actions)
  const clueOnly = [
    "EXTREME_VALUE",
    "SUSPICIOUS_UNIT",
    "GROUP_IMBALANCE",
  ].includes(dto.issue_type)
  const examples = Array.isArray(dto.evidence.examples)
    ? dto.evidence.examples.slice(0, 5).map((value) => String(value))
    : []
  const sensitiveCandidate = dto.issue_type === "POSSIBLE_SENSITIVE_FIELD"
  return {
    ...fact(dto.status, issueStatuses.has(dto.status)),
    id: dto.id,
    ruleCode: dto.rule_code,
    issueType: dto.issue_type,
    severity: dto.severity,
    columnId: dto.column_id,
    affectedRowCount: dto.affected_row_count,
    description: dto.description,
    clueOnly,
    sensitiveCandidate,
    sensitiveConfirmed: false,
    exampleSummary: sensitiveCandidate
      ? examples.map(() => "[MASKED]")
      : examples,
    requiresApproval: dto.requires_approval,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions,
  }
}

function numeric(value: unknown): number | null {
  return typeof value === "number" ? value : null
}

function objectValue(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function literalValue(value: unknown): CleaningLiteralValue | undefined {
  return value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
    ? value
    : undefined
}

function stringArray(
  value: unknown,
  maximum: number,
): readonly string[] | null {
  if (
    !Array.isArray(value) ||
    value.length > maximum ||
    value.some((item) => typeof item !== "string")
  ) {
    return null
  }
  const values = value as string[]
  return new Set(values).size === values.length ? values : null
}

function mapRowSelector(value: unknown): CleaningRowSelector | null {
  if (value === undefined || value === null) return { type: "ALL_ROWS" }
  const selector = objectValue(value)
  if (!selector || typeof selector.selector_type !== "string") return null
  switch (selector.selector_type) {
    case "ALL_ROWS":
      return { type: "ALL_ROWS" }
    case "ISSUE_ROWS": {
      const issueIds = stringArray(selector.issue_ids, 50)
      return issueIds && issueIds.length > 0
        ? { type: "ISSUE_ROWS", issueIds }
        : null
    }
    case "VALUE_EQUALS": {
      const value = literalValue(selector.value)
      return typeof selector.column_id === "string" && value !== undefined
        ? { type: "VALUE_EQUALS", columnId: selector.column_id, value }
        : null
    }
    case "VALUE_IN": {
      const values = Array.isArray(selector.values)
        ? selector.values.map(literalValue)
        : []
      return typeof selector.column_id === "string" &&
        values.length > 0 &&
        values.length <= 100 &&
        values.every((item) => item !== undefined)
        ? {
            type: "VALUE_IN",
            columnId: selector.column_id,
            values: values as CleaningLiteralValue[],
          }
        : null
    }
    case "IS_NULL":
    case "IS_NOT_NULL":
      return typeof selector.column_id === "string"
        ? { type: selector.selector_type, columnId: selector.column_id }
        : null
    case "NUMERIC_RANGE": {
      const minimum =
        selector.minimum === null ? null : numeric(selector.minimum)
      const maximum =
        selector.maximum === null ? null : numeric(selector.maximum)
      if (
        typeof selector.column_id !== "string" ||
        (minimum === null && maximum === null) ||
        (minimum !== null && maximum !== null && minimum > maximum)
      ) {
        return null
      }
      return {
        type: "NUMERIC_RANGE",
        columnId: selector.column_id,
        minimum,
        maximum,
        includeMinimum: selector.include_minimum !== false,
        includeMaximum: selector.include_maximum !== false,
      }
    }
    default:
      return null
  }
}

function mapCleaningAction(value: unknown): CleaningActionInput | null {
  const action = objectValue(value)
  if (!action || typeof action.action_type !== "string") return null
  const targetColumnIds = stringArray(action.target_columns, 20)
  const sourceIssueIds = stringArray(action.source_issue_ids ?? [], 50)
  const rowSelector = mapRowSelector(action.row_selector)
  const parameters = objectValue(action.parameters)
  if (
    !targetColumnIds ||
    targetColumnIds.length === 0 ||
    !sourceIssueIds ||
    !rowSelector ||
    typeof action.reason !== "string" ||
    !action.reason.trim() ||
    !parameters
  ) {
    return null
  }
  const base = {
    targetColumnIds,
    rowSelector,
    reason: action.reason,
    sourceIssueIds,
  }
  switch (action.action_type) {
    case "MARK_MISSING":
      return {
        ...base,
        type: "MARK_MISSING",
        parameters: { replacement: null },
      }
    case "REPLACE_VALUE": {
      const replacement = literalValue(parameters.replacement)
      return replacement !== undefined
        ? { ...base, type: "REPLACE_VALUE", parameters: { replacement } }
        : null
    }
    case "MAP_CATEGORY": {
      const rawMapping = objectValue(parameters.mapping)
      if (!rawMapping || targetColumnIds.length !== 1) return null
      const entries = Object.entries(rawMapping)
      const mapping = Object.fromEntries(
        entries.map(([key, item]) => [key, literalValue(item)]),
      )
      return entries.length > 0 &&
        entries.length <= 100 &&
        entries.every(([key]) => key.length > 0 && key.length <= 256) &&
        Object.values(mapping).every((item) => item !== undefined)
        ? {
            ...base,
            type: "MAP_CATEGORY",
            parameters: {
              mapping: mapping as Record<string, CleaningLiteralValue>,
            },
          }
        : null
    }
    case "CAST_TYPE": {
      const targetTypes = new Set([
        "STRING",
        "INTEGER",
        "NUMERIC",
        "BOOLEAN",
        "DATE",
        "DATETIME",
      ])
      const onInvalid = parameters.on_invalid ?? "FAIL"
      return typeof parameters.target_type === "string" &&
        targetTypes.has(parameters.target_type) &&
        (onInvalid === "FAIL" || onInvalid === "MARK_MISSING")
        ? {
            ...base,
            type: "CAST_TYPE",
            parameters: {
              targetType: parameters.target_type as
                | "STRING"
                | "INTEGER"
                | "NUMERIC"
                | "BOOLEAN"
                | "DATE"
                | "DATETIME",
              onInvalid,
            },
          }
        : null
    }
    case "RENAME_COLUMN":
      return targetColumnIds.length === 1 &&
        rowSelector.type === "ALL_ROWS" &&
        typeof parameters.new_name === "string" &&
        parameters.new_name.trim().length > 0 &&
        parameters.new_name.length <= 255
        ? {
            ...base,
            type: "RENAME_COLUMN",
            parameters: { newName: parameters.new_name },
          }
        : null
    default:
      return null
  }
}

export function mapCleaningPlan(dto: CleaningPlanDto): CleaningPlanViewModel {
  const allowedActions = actions(dto.allowed_actions)
  const preview = dto.preview_summary
  const editorActions = dto.actions.map(mapCleaningAction)
  const actionsEditable = editorActions.every(
    (action): action is CleaningActionInput => action !== null,
  )
  return {
    ...fact(dto.status, planStatuses.has(dto.status)),
    id: dto.id,
    versionId: dto.dataset_version_id,
    title: dto.title,
    rationale: dto.rationale,
    actionCount: dto.actions.length,
    actions: dto.actions.map((action) => ({
      type:
        typeof action.action_type === "string" ? action.action_type : "UNKNOWN",
      reason: typeof action.reason === "string" ? action.reason : "",
      targetCount: Array.isArray(action.target_columns)
        ? action.target_columns.length
        : 0,
    })),
    editorActions: actionsEditable ? editorActions : [],
    actionsEditable,
    actionsDisabledReason: actionsEditable
      ? null
      : "At least one persisted action does not match the M4 typed whitelist.",
    preview:
      preview && dto.preview_hash
        ? {
            hash: dto.preview_hash,
            affectedRows:
              numeric(preview.affected_row_count) ??
              dto.affected_row_count ??
              0,
            affectedColumns:
              numeric(preview.affected_column_count) ??
              dto.affected_column_count ??
              0,
            rowCountBefore: numeric(preview.row_count_before),
            rowCountAfter: numeric(preview.row_count_after),
            warnings: Array.isArray(preview.warnings)
              ? preview.warnings.map(String)
              : [],
            risk: typeof preview.risk === "string" ? preview.risk : "UNKNOWN",
            readyForApproval: preview.ready_for_approval === true,
          }
        : null,
    approvalRecordId: dto.approval_record_id,
    approvalPayloadHash: dto.payload_hash,
    transformationId: dto.transformation_id,
    jobId: dto.job_id,
    lockVersion: dto.lock_version,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions,
  }
}

export function mapApproval(
  dto: ApprovalPublic,
  plan: CleaningPlanViewModel | null,
): ApprovalViewModel {
  const allowedActions = actions(dto.allowed_actions)
  const expired =
    dto.status === "EXPIRED" ||
    (dto.expires_at ? Date.parse(dto.expires_at) <= Date.now() : false)
  const stale =
    dto.status === "SUPERSEDED" ||
    (plan !== null &&
      plan.approvalPayloadHash !== null &&
      plan.approvalPayloadHash !== dto.payload_hash)
  return {
    ...fact(
      stale ? "STALE" : expired ? "EXPIRED" : dto.status,
      stale || approvalStatuses.has(dto.status),
    ),
    id: dto.id,
    expiresAt: dto.expires_at,
    expired,
    stale,
    decisionReason: dto.decision?.reason ?? null,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions,
  }
}

export function mapTransformation(
  dto: DataTransformationDto,
): TransformationViewModel {
  return {
    ...fact(dto.status, transformationStatuses.has(dto.status)),
    id: dto.id,
    sourceVersionId: dto.source_dataset_version_id,
    targetVersionId: dto.target_dataset_version_id,
    outputArtifactId: dto.output_artifact_id,
    affectedRows: dto.affected_row_count,
    affectedColumns: dto.affected_column_count,
    errorCode: dto.error_code,
  }
}

export function mapJob(dto: JobPublic): JobStateViewModel {
  const knownStatus = jobStatuses.has(dto.status)
  return {
    ...fact(dto.status, knownStatus),
    id: dto.id,
    accepted: knownStatus && dto.status !== "DRAFT",
    queued: dto.status === "QUEUED",
    running: dto.status === "RUNNING",
    completed: dto.status === "COMPLETED",
    failed: dto.status === "FAILED" || dto.status === "DISPATCH_FAILED",
    retryable:
      knownStatus &&
      dto.retryable &&
      ["FAILED", "DISPATCH_FAILED", "CANCELLED"].includes(dto.status),
    progress: dto.progress_percent,
    currentStep: dto.current_step,
    errorCode: dto.error?.code ?? null,
  }
}

export function mapComparison(
  dto: VersionComparisonDto,
): VersionComparisonViewModel {
  return {
    baseVersionId: dto.base_version_id,
    targetVersionId: dto.target_version_id,
    rowDelta: dto.row_count.delta,
    columnDelta: dto.column_count.delta,
    missingBefore: dto.missing_cells.before,
    missingAfter: dto.missing_cells.after,
    affectedRows: dto.affected_row_count,
    affectedColumns: dto.affected_column_count,
    actionTypes: dto.actions.map((action) =>
      String(action.action_type ?? "UNKNOWN"),
    ),
    parentVersionId: dto.lineage.parent_version_id,
    transformationId: dto.lineage.transformation_id,
    outputArtifactId: dto.lineage.output_artifact_id,
  }
}

function projectActions(
  project: ProjectPublic | null,
): ReadonlySet<string> | null {
  return project && Array.isArray(project.allowed_actions)
    ? new Set(project.allowed_actions)
    : null
}

export function mapCapabilities(input: {
  project: ProjectPublic | null
  dataset: DatasetDto | null
  version: DatasetVersionViewModel | null
  run: QualityRunViewModel | null
  issues: readonly QualityIssueViewModel[]
  plan: CleaningPlanViewModel | null
  approval: ApprovalViewModel | null
  job: JobStateViewModel | null
}): DataWorkspaceCapabilities {
  const projectAllowed = projectActions(input.project)
  const permissionsKnown = projectAllowed !== null
  const projectHas = (action: string) =>
    permissionsKnown && projectAllowed.has(action)
  const currentAvailable =
    input.version?.current === true && input.version.status === "AVAILABLE"
  const planHas = (action: string) =>
    input.plan?.permissionsKnown === true &&
    input.plan.allowedActions.has(action)
  const issueHas = (action: string) =>
    input.issues.some(
      (issue) => issue.permissionsKnown && issue.allowedActions.has(action),
    )
  return {
    permissionsKnown,
    uploadDataset: capability(
      projectHas("dataset.upload"),
      permissionsKnown
        ? "The server did not allow dataset upload."
        : "Dataset permissions are unknown.",
    ),
    selectWorksheet: capability(
      projectHas("dataset.upload") && input.version?.status === "CREATING",
      "Worksheet selection is available only for a CREATING workbook version.",
    ),
    updateDatasetIdentity: capability(
      input.dataset?.permissions?.can_update === true,
      input.dataset?.permissions
        ? "The server did not allow identity updates."
        : "Dataset permissions are unknown.",
    ),
    updateColumn: capability(
      input.dataset?.permissions?.can_confirm_columns === true &&
        input.version?.knownStatus === true,
      "Column confirmation is unavailable for this version or role.",
    ),
    runQuality: capability(
      projectHas("dataset.quality.run") && currentAvailable,
      "Quality runs require the current AVAILABLE version and server permission.",
    ),
    acknowledgeIssue: capability(
      issueHas("data_quality_issue.acknowledge"),
      "No selected issue allows acknowledgement.",
    ),
    ignoreIssue: capability(
      issueHas("data_quality_issue.ignore"),
      "No selected issue allows ignore.",
    ),
    createPlan: capability(
      projectHas("dataset.cleaning.plan") && currentAvailable,
      "Plan creation requires the current AVAILABLE version and server permission.",
    ),
    updatePlan: capability(
      planHas("cleaning_plan.update"),
      input.plan?.permissionsKnown
        ? "The current plan state is immutable."
        : "Plan permissions are unknown.",
    ),
    previewPlan: capability(
      planHas("cleaning_plan.preview"),
      "The server did not allow Preview for this plan state.",
    ),
    requestApproval: capability(
      planHas("cleaning_plan.request_approval"),
      "A complete READY Preview is required before Approval.",
    ),
    executePlan: capability(
      planHas("cleaning_plan.execute") &&
        input.approval?.status === "APPROVED" &&
        !input.approval.stale &&
        !input.approval.expired,
      "Execution requires an effective APPROVED Approval matching the current Plan payload.",
    ),
    compareVersions: capability(
      input.dataset !== null &&
        input.version?.knownStatus === true &&
        input.version.parentVersionId !== null,
      "Version comparison requires a known selected DatasetVersion with a formal parent.",
    ),
    retryJob: capability(
      input.job?.knownStatus === true && input.job.retryable,
      "This Job is not retryable or its status is unknown.",
    ),
  }
}

export function mapDataWorkspace(input: {
  projectId: string
  project: ProjectPublic | null
  datasets: readonly DatasetDto[]
  dataset: DatasetDto | null
  version: DatasetVersionDto | null
  versions: readonly DatasetVersionDto[]
  columns: readonly DatasetColumnDto[]
  preview: DatasetPreviewDto | null
  run: DataQualityRunDto | null
  issues: readonly DataQualityIssueDto[]
  plan: CleaningPlanDto | null
  approval: ApprovalPublic | null
  transformation: DataTransformationDto | null
  job: JobPublic | null
  comparison: VersionComparisonDto | null
}): DataWorkspaceViewModel {
  const dataset = input.dataset ? mapDataset(input.dataset) : null
  const version = input.version
    ? mapDatasetVersion(input.version, dataset?.currentVersionId ?? null)
    : null
  const issues = input.issues.map(mapQualityIssue)
  const run = input.run ? mapQualityRun(input.run) : null
  const plan = input.plan ? mapCleaningPlan(input.plan) : null
  const approval = input.approval ? mapApproval(input.approval, plan) : null
  const job = input.job ? mapJob(input.job) : null
  return {
    projectId: input.projectId,
    datasets: input.datasets.map(mapDatasetListItem),
    dataset,
    version,
    versions: input.versions.map((item) =>
      mapDatasetVersion(item, dataset?.currentVersionId ?? null),
    ),
    columns: input.columns.map(mapDatasetColumn),
    preview: input.preview ? mapDatasetPreview(input.preview) : null,
    qualityRun: run,
    issues,
    plan,
    approval,
    transformation: input.transformation
      ? mapTransformation(input.transformation)
      : null,
    job,
    comparison: input.comparison ? mapComparison(input.comparison) : null,
    capabilities: mapCapabilities({
      project: input.project,
      dataset: input.dataset,
      version,
      run,
      issues,
      plan,
      approval,
      job,
    }),
    integrationPending: [],
  }
}
