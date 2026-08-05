import type {
  AnalysisPlanPublic,
  AnalysisResultPublic,
  AnalysisRunPublic,
  ApprovalPublic,
  DatasetColumnDto,
  DatasetDto,
  DatasetVersionDto,
  FigurePlanPublic,
  FigurePublic,
  FigureRecommendationPublic,
  FigureRenderRunPublic,
  JobPublic,
  ProjectPublic,
} from "@/api/adapter"

import type {
  ActionCapability,
  AnalysisPlanInput,
  AnalysisPlanViewModel,
  AnalysisResultViewModel,
  AnalysisRunViewModel,
  AnalysisWorkspaceCapabilities,
  AnalysisWorkspaceViewModel,
  ApprovalViewModel,
  ColumnContextViewModel,
  DatasetContextViewModel,
  FigurePlanViewModel,
  FigureRenderRunViewModel,
  FigureValidationIssueViewModel,
  FigureViewModel,
  JobViewModel,
  KnownFact,
  ResultValue,
  SampleFilter,
} from "./model"

const planStatuses = new Set([
  "DRAFT",
  "VALIDATING",
  "NEEDS_INPUT",
  "READY",
  "NEEDS_APPROVAL",
  "APPROVED",
  "REJECTED",
  "INVALIDATED",
])
const runStatuses = new Set([
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "FAILED",
  "CANCEL_REQUESTED",
  "CANCELLED",
  "INVALIDATED",
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
const resultTypes = new Set([
  "DESCRIPTIVE_NUMERIC",
  "DESCRIPTIVE_CATEGORICAL",
  "CORRELATION",
  "GROUP_COMPARISON",
  "REGRESSION",
])
const confirmationStatuses = new Set([
  "UNCONFIRMED",
  "INFERRED",
  "NEEDS_REVIEW",
  "CONFIRMED",
])
const figurePlanStatuses = new Set([
  "DRAFT",
  "READY",
  "INVALIDATED",
  "ARCHIVED",
])
const figureRunStatuses = new Set([
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "FAILED",
  "CANCEL_REQUESTED",
  "CANCELLED",
  "INVALIDATED",
])
const figureStatuses = new Set([
  "DRAFT",
  "READY",
  "NEEDS_REVIEW",
  "CONFIRMED",
  "INVALIDATED",
  "ARCHIVED",
])

function fact(status: string, knownStatus: boolean): KnownFact {
  return {
    status,
    knownStatus,
    tone: !knownStatus
      ? "degraded"
      : ["APPROVED", "COMPLETED", "CONFIRMED", "AVAILABLE", "PASSED"].includes(
            status,
          )
        ? "success"
        : ["FAILED", "REJECTED", "INVALIDATED", "EXPIRED"].includes(status)
          ? "danger"
          : [
                "NEEDS_INPUT",
                "NEEDS_APPROVAL",
                "REQUIRES_USER_CONFIRMATION",
                "WARNING",
              ].includes(status)
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

function objectValue(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

function stringArray(value: unknown): readonly string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string")
    ? value
    : []
}

function mapFilter(value: unknown): SampleFilter | null {
  const filter = objectValue(value)
  if (!filter || typeof filter.operator !== "string") return null
  if (
    (filter.operator === "EQUALS" ||
      filter.operator === "IS_NULL" ||
      filter.operator === "IS_NOT_NULL") &&
    typeof filter.column_id === "string"
  ) {
    if (filter.operator !== "EQUALS") {
      return { operator: filter.operator, columnId: filter.column_id }
    }
    if (
      typeof filter.value === "string" ||
      typeof filter.value === "number" ||
      typeof filter.value === "boolean"
    ) {
      return {
        operator: "EQUALS",
        columnId: filter.column_id,
        value: filter.value,
      }
    }
  }
  if (
    filter.operator === "IN" &&
    typeof filter.column_id === "string" &&
    Array.isArray(filter.values) &&
    filter.values.every((item) =>
      ["string", "number", "boolean"].includes(typeof item),
    )
  ) {
    return {
      operator: "IN",
      columnId: filter.column_id,
      values: filter.values as (string | number | boolean)[],
    }
  }
  if (
    filter.operator === "NUMERIC_RANGE" &&
    typeof filter.column_id === "string"
  ) {
    return {
      operator: "NUMERIC_RANGE",
      columnId: filter.column_id,
      minimum: typeof filter.minimum === "number" ? filter.minimum : null,
      maximum: typeof filter.maximum === "number" ? filter.maximum : null,
      includeMinimum: filter.include_minimum !== false,
      includeMaximum: filter.include_maximum !== false,
    }
  }
  return null
}

function planInput(dto: AnalysisPlanPublic): AnalysisPlanInput {
  const missing = objectValue(dto.missing_data_policy)
  const parameters = objectValue(dto.parameters)
  return {
    researchQuestionVersionId: dto.research_question_version_id,
    datasetVersionId: dto.dataset_version_id,
    analysisGoal: dto.analysis_goal,
    method: dto.method,
    dependentVariableIds: dto.dependent_variable_ids,
    independentVariableIds: dto.independent_variable_ids,
    controlVariableIds: dto.control_variable_ids,
    missingDataMode:
      missing?.mode === "PAIRWISE_COMPLETE"
        ? "PAIRWISE_COMPLETE"
        : "COMPLETE_CASE",
    sampleFilter: mapFilter(dto.sample_filter),
    confidenceLevel:
      typeof parameters?.confidence_level === "number"
        ? parameters.confidence_level
        : 0.95,
    alternative:
      parameters?.alternative === "LESS" ||
      parameters?.alternative === "GREATER"
        ? parameters.alternative
        : "TWO_SIDED",
    varianceMode: parameters?.variance_mode === "EQUAL" ? "EQUAL" : "WELCH",
    independenceConfirmed: parameters?.independence_confirmed === true,
    pairingConfirmed: parameters?.pairing_confirmed === true,
    pairIdColumnId:
      typeof parameters?.pair_id_column_id === "string"
        ? parameters.pair_id_column_id
        : null,
    assumptionConfirmations: stringArray(parameters?.assumption_confirmations),
    acknowledgedQualityIssueIds: stringArray(
      parameters?.acknowledged_quality_issue_ids,
    ),
    sensitiveColumnAcknowledgements: stringArray(
      parameters?.sensitive_column_acknowledgements,
    ),
  }
}

export function mapAnalysisPlan(
  dto: AnalysisPlanPublic,
): AnalysisPlanViewModel {
  const allowedActions = actions(dto.allowed_actions)
  return {
    ...fact(dto.status, planStatuses.has(dto.status)),
    id: dto.id,
    projectId: dto.project_id,
    datasetVersionId: dto.dataset_version_id,
    researchQuestionVersionId: dto.research_question_version_id,
    goal: dto.analysis_goal,
    method: dto.method,
    input: planInput(dto),
    validationHash: dto.validation_hash,
    validationWarnings: dto.validation_warnings,
    approvalId: dto.approval_record_id,
    approvalPayloadHash: dto.payload_hash,
    approvalStale: dto.approval_stale,
    lockVersion: dto.lock_version,
    invalidationReason: dto.invalidation_reason,
    checks: dto.checks.map((check) => ({
      ...fact(
        check.status,
        [
          "PASSED",
          "FAILED",
          "WARNING",
          "NOT_APPLICABLE",
          "REQUIRES_USER_CONFIRMATION",
          "UNKNOWN",
        ].includes(check.status),
      ),
      id: check.id,
      code: check.check_code,
      subjectKey: check.subject_key,
      explanation: check.explanation,
      blocksApproval: check.blocks_approval,
      requiresConfirmation: check.status === "REQUIRES_USER_CONFIRMATION",
      checkedAt: check.checked_at,
    })),
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions,
  }
}

export function mapAnalysisRun(dto: AnalysisRunPublic): AnalysisRunViewModel {
  return {
    ...fact(dto.status, runStatuses.has(dto.status)),
    id: dto.id,
    projectId: dto.project_id,
    planId: dto.analysis_plan_id,
    datasetVersionId: dto.dataset_version_id,
    approvalId: dto.approval_record_id,
    runNumber: dto.run_number,
    jobId: dto.job_id,
    effectiveN: dto.effective_n,
    inputHash: dto.input_hash,
    parametersHash: dto.parameters_hash,
    environmentHash: dto.environment_hash,
    environment: Object.fromEntries(
      Object.entries(dto.environment_snapshot ?? {}).flatMap(([key, value]) =>
        typeof value === "string" ? [[key, value]] : [],
      ),
    ),
    resultCount: dto.result_count,
    errorCode: dto.error_code,
    invalidationReason: dto.invalidation_reason,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions: actions(dto.allowed_actions),
  }
}

function resultValue(value: unknown): ResultValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value
  }
  if (Array.isArray(value)) return value.map(resultValue)
  const object = objectValue(value)
  return object
    ? Object.fromEntries(
        Object.entries(object).map(([key, item]) => [key, resultValue(item)]),
      )
    : null
}

export function mapAnalysisResult(
  dto: AnalysisResultPublic,
  runStatus: string,
): AnalysisResultViewModel {
  return {
    ...fact(
      runStatus === "INVALIDATED" ? "INVALIDATED" : dto.result_type,
      resultTypes.has(dto.result_type) &&
        ["COMPLETED", "INVALIDATED"].includes(runStatus),
    ),
    id: dto.id,
    runId: dto.analysis_run_id,
    key: dto.result_key,
    type: dto.result_type,
    schemaVersion: dto.schema_version,
    primary: dto.is_primary,
    payload: Object.fromEntries(
      Object.entries(dto.payload).map(([key, value]) => [
        key,
        resultValue(value),
      ]),
    ),
    resultHash: dto.result_hash,
    deterministic: true,
    interpretation: null,
    createdAt: dto.created_at,
  }
}

export function mapFigurePlan(dto: FigurePlanPublic): FigurePlanViewModel {
  return {
    ...fact(dto.status, figurePlanStatuses.has(dto.status)),
    id: dto.id,
    projectId: dto.project_id,
    datasetVersionId: dto.dataset_version_id,
    analysisRunId: dto.analysis_run_id,
    analysisResultId: dto.analysis_result_id,
    chartType: dto.chart_type,
    caption: dto.caption,
    parameters: Object.fromEntries(
      Object.entries(dto.parameters).map(([key, value]) => [
        key,
        resultValue(value),
      ]),
    ),
    planHash: dto.plan_hash,
    lockVersion: dto.lock_version,
    invalidationReason: dto.invalidation_reason,
    transportAvailable: true,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions: actions(dto.allowed_actions),
  }
}

export function mapFigureRenderRun(
  dto: FigureRenderRunPublic,
): FigureRenderRunViewModel {
  const allowedActions = actions(dto.allowed_actions)
  return {
    ...fact(dto.status, figureRunStatuses.has(dto.status)),
    id: dto.id,
    projectId: dto.project_id,
    figurePlanId: dto.figure_plan_id,
    datasetVersionId: dto.dataset_version_id,
    jobId: dto.job_id,
    figureId: dto.figure_id,
    renderNumber: dto.render_number,
    inputHash: dto.input_hash,
    parametersHash: dto.parameters_hash,
    environmentHash: dto.environment_hash,
    errorCode: dto.error_code,
    retryable: allowedActions.has("figure_render_run.retry"),
    transportAvailable: true,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions,
  }
}

function mapFigureIssue(
  dto: FigurePublic["validation_issues"][number],
): FigureValidationIssueViewModel {
  return {
    ...fact(
      dto.status,
      ["OPEN", "ACKNOWLEDGED", "RESOLVED", "INVALIDATED"].includes(dto.status),
    ),
    id: dto.id,
    issueType: dto.issue_type,
    severity: dto.severity,
    message: dto.message,
    blocksConfirmation: dto.blocks_confirmation,
  }
}

export function mapFigure(dto: FigurePublic): FigureViewModel {
  const allowedActions = actions(dto.allowed_actions)
  const artifactKinds = new Set(["PNG", "SVG", "PDF", "CODE"])
  return {
    ...fact(dto.status, figureStatuses.has(dto.status)),
    id: dto.id,
    projectId: dto.project_id,
    figurePlanId: dto.figure_plan_id,
    renderRunId: dto.figure_render_run_id,
    datasetVersionId: dto.dataset_version_id,
    analysisRunId: dto.analysis_run_id,
    analysisResultId: dto.analysis_result_id,
    versionNumber: dto.version_number,
    chartType: dto.chart_type,
    caption: dto.caption,
    aggregateHash: dto.figure_hash,
    confirmationApprovalId: dto.approval_record_id,
    approvalStale: dto.approval_stale,
    invalidationReason: dto.invalidation_reason,
    issues: dto.validation_issues.map(mapFigureIssue),
    artifacts: dto.artifacts.map((artifact) => ({
      ...fact(
        artifact.status,
        ["AVAILABLE", "FAILED"].includes(artifact.status),
      ),
      id: artifact.id,
      kind: artifactKinds.has(artifact.format)
        ? (artifact.format as "PNG" | "SVG" | "PDF" | "CODE")
        : "OTHER",
      label: `${artifact.format} Artifact`,
      sha256: artifact.sha256,
      downloadable: artifact.downloadable,
      masked: false,
    })),
    transportAvailable: true,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions,
  }
}

export function mapApproval(
  dto: ApprovalPublic,
  stale: boolean,
): ApprovalViewModel {
  return {
    ...fact(dto.status, approvalStatuses.has(dto.status)),
    id: dto.id,
    targetId: dto.target_object_id,
    payloadHash: dto.payload_hash,
    expiresAt: dto.expires_at,
    expired: dto.status === "EXPIRED",
    stale,
    decisionReason: dto.decision?.reason ?? null,
    permissionsKnown: Array.isArray(dto.allowed_actions),
    allowedActions: actions(dto.allowed_actions),
  }
}

export function mapJob(dto: JobPublic): JobViewModel {
  return {
    ...fact(dto.status, jobStatuses.has(dto.status)),
    id: dto.id,
    kind:
      dto.task_type === "ANALYSIS_RUN"
        ? "ANALYSIS"
        : dto.resource_type === "figure_render_run"
          ? "FIGURE"
          : "OTHER",
    accepted: true,
    progress: dto.progress_percent,
    currentStep: dto.current_step,
    retryable: dto.retryable,
    errorCode: dto.error?.code ?? null,
  }
}

export function mapDatasetContext(
  dataset: DatasetDto,
  version: DatasetVersionDto,
): DatasetContextViewModel {
  return {
    ...fact(
      version.status,
      ["AVAILABLE", "INVALIDATED"].includes(version.status),
    ),
    datasetId: dataset.id,
    datasetName: dataset.name,
    versionId: version.id,
    versionNumber: version.version_number,
    dataHash: version.data_hash,
    schemaHash: version.schema_hash,
    projectionHash: version.projection_hash,
    available: version.status === "AVAILABLE",
  }
}

export function mapColumn(dto: DatasetColumnDto): ColumnContextViewModel {
  const sensitive = dto.is_sensitive
  return {
    id: dto.id,
    name: dto.display_name ?? dto.source_name,
    confirmedType: dto.confirmed_type,
    confirmationStatus: dto.confirmation_status,
    confirmationKnown: confirmationStatuses.has(dto.confirmation_status),
    confirmed: dto.confirmation_status === "CONFIRMED",
    unit: dto.unit,
    missingRatio: dto.missing_ratio,
    qualityWarning:
      dto.confirmation_status !== "CONFIRMED" ||
      (dto.missing_ratio !== null && dto.missing_ratio > 0),
    sensitive,
    displayValue: sensitive
      ? "[MASKED]"
      : (dto.display_name ?? dto.source_name),
  }
}

export function mapCapabilities(input: {
  project: ProjectPublic
  plan: AnalysisPlanViewModel | null
  run: AnalysisRunViewModel | null
  job: JobViewModel | null
  figurePlan: FigurePlanViewModel | null
  renderRun: FigureRenderRunViewModel | null
  figure: FigureViewModel | null
  approval: ApprovalViewModel | null
}): AnalysisWorkspaceCapabilities {
  const projectActions = actions(input.project.allowed_actions)
  const permissionsKnown = Array.isArray(input.project.allowed_actions)
  const planAction = (action: string) =>
    permissionsKnown && input.plan?.permissionsKnown === true
      ? input.plan.allowedActions.has(action)
      : false
  return {
    permissionsKnown,
    createPlan: capability(
      permissionsKnown && projectActions.has("analysis.create"),
      permissionsKnown ? "Action is not allowed." : "Permissions are unknown.",
    ),
    updatePlan: capability(
      planAction("analysis_plan.update"),
      "Plan cannot be edited.",
    ),
    validatePlan: capability(
      planAction("analysis_plan.validate"),
      "Plan cannot be validated.",
    ),
    requestPlanApproval: capability(
      planAction("analysis_plan.request_approval") &&
        !input.plan?.approvalStale,
      "Plan is not ready for approval.",
    ),
    runAnalysis: capability(
      planAction("analysis_plan.run") && !input.plan?.approvalStale,
      "A current approved Plan is required.",
    ),
    invalidateRun: capability(
      input.run?.permissionsKnown === true &&
        input.run.allowedActions.has("analysis_run.invalidate"),
      "Run cannot be invalidated.",
    ),
    retryJob: capability(
      permissionsKnown &&
        projectActions.has("job.retry") &&
        input.job?.retryable === true,
      "Job retry is not available.",
    ),
    cancelJob: capability(
      permissionsKnown &&
        projectActions.has("job.cancel") &&
        input.job !== null &&
        ["QUEUED", "RUNNING"].includes(input.job.status),
      "Job cancellation is not available.",
    ),
    createFigurePlan: capability(
      permissionsKnown && projectActions.has("figure.create"),
      permissionsKnown
        ? "Figure creation is not allowed."
        : "Permissions are unknown.",
    ),
    renderFigure: capability(
      input.figurePlan?.permissionsKnown === true &&
        input.figurePlan.allowedActions.has("figure_plan.render"),
      "FigurePlan is not ready to render.",
    ),
    requestFigureConfirmation: capability(
      input.figure?.permissionsKnown === true &&
        input.figure.allowedActions.has("figure.request_confirmation") &&
        !input.figure.approvalStale,
      "Figure is not eligible for confirmation.",
    ),
    decideFigureConfirmation: capability(
      input.approval?.permissionsKnown === true &&
        input.approval.allowedActions.has("approval.decide") &&
        !input.approval.stale,
      "A current pending confirmation Approval is required.",
    ),
    downloadArtifact: capability(
      input.figure?.permissionsKnown === true &&
        input.figure.allowedActions.has("figure.download"),
      "Figure Artifacts are not downloadable.",
    ),
    requestSuggestion: capability(
      false,
      "Suggestion provider is not configured.",
    ),
    requestInterpretation: capability(
      false,
      "Interpretation provider is not configured.",
    ),
  }
}

export function mapAnalysisWorkspace(input: {
  projectId: string
  project: ProjectPublic
  dataset: DatasetDto | null
  version: DatasetVersionDto | null
  columns: readonly DatasetColumnDto[]
  plan: AnalysisPlanPublic | null
  approval: ApprovalPublic | null
  run: AnalysisRunPublic | null
  results: readonly AnalysisResultPublic[]
  job: JobPublic | null
  figurePlan: FigurePlanPublic | null
  renderRun: FigureRenderRunPublic | null
  figure: FigurePublic | null
  figureRecommendation: FigureRecommendationPublic | null
}): AnalysisWorkspaceViewModel {
  const plan = input.plan ? mapAnalysisPlan(input.plan) : null
  const run = input.run ? mapAnalysisRun(input.run) : null
  const job = input.job ? mapJob(input.job) : null
  const figurePlan = input.figurePlan ? mapFigurePlan(input.figurePlan) : null
  const renderRun = input.renderRun ? mapFigureRenderRun(input.renderRun) : null
  const figure = input.figure ? mapFigure(input.figure) : null
  const approval =
    input.approval && (plan || figure)
      ? mapApproval(
          input.approval,
          figure?.approvalStale ?? plan?.approvalStale ?? false,
        )
      : null
  const columns = input.columns.map(mapColumn)
  return {
    projectId: input.projectId,
    dataset:
      input.dataset && input.version
        ? mapDatasetContext(input.dataset, input.version)
        : null,
    columns,
    qualityWarnings: columns
      .filter((column) => column.qualityWarning)
      .map((column) => `${column.displayValue}: review required`),
    plan,
    approval,
    run,
    results: input.results.map((result) =>
      mapAnalysisResult(result, run?.status ?? "UNKNOWN"),
    ),
    job,
    figurePlan,
    renderRun,
    figure,
    suggestions: [
      {
        kind: "METHOD",
        availability: "DEGRADED",
        deterministic: false,
        text: null,
        reason: "No production suggestion provider is configured.",
      },
      {
        kind: "FIGURE",
        availability:
          input.figureRecommendation?.status === "DEGRADED"
            ? "DEGRADED"
            : "UNAVAILABLE",
        deterministic: false,
        text: null,
        reason:
          input.figureRecommendation?.reason ??
          "Figure recommendation is unavailable.",
      },
    ],
    capabilities: mapCapabilities({
      project: input.project,
      plan,
      run,
      job,
      figurePlan,
      renderRun,
      figure,
      approval,
    }),
    readScopes: [
      "dataset",
      "analysis-plan",
      "analysis-run",
      "analysis-result",
      "figure-plan",
      "figure-render-run",
      "figure",
      "artifact",
    ],
    integrationPending: [],
  }
}
