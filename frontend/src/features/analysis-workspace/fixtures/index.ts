import type { UiErrorViewModel } from "../../projects/model"
import type {
  AnalysisResultViewModel,
  AnalysisWorkspaceViewModel,
  FigureViewModel,
} from "../model"
import type { AnalysisWorkspaceWorkspaceProps } from "../ui/contracts"

const id = {
  project: "11111111-1111-4111-8111-111111111111",
  dataset: "22222222-2222-4222-8222-222222222222",
  version: "33333333-3333-4333-8333-333333333333",
  plan: "44444444-4444-4444-8444-444444444444",
  approval: "55555555-5555-4555-8555-555555555555",
  run: "66666666-6666-4666-8666-666666666666",
  result: "77777777-7777-4777-8777-777777777777",
  job: "88888888-8888-4888-8888-888888888888",
  figurePlan: "99999999-9999-4999-8999-999999999999",
  renderRun: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  figure: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
}

const allowed = (value: boolean, reason = "Action is not allowed.") => ({
  allowed: value,
  disabledReason: value ? null : reason,
})

const result = (
  type: string,
  payload: AnalysisResultViewModel["payload"],
  overrides: Partial<AnalysisResultViewModel> = {},
): AnalysisResultViewModel => ({
  status: type,
  knownStatus: true,
  tone: "success",
  id: id.result,
  runId: id.run,
  key: "primary",
  type,
  schemaVersion: "1.0",
  primary: true,
  payload,
  resultHash: "a".repeat(64),
  deterministic: true,
  interpretation: null,
  createdAt: "2026-08-04T10:00:00Z",
  ...overrides,
})

const baseWorkspace: AnalysisWorkspaceViewModel = {
  projectId: id.project,
  dataset: {
    status: "AVAILABLE",
    knownStatus: true,
    tone: "success",
    datasetId: id.dataset,
    datasetName: "Learning outcomes study",
    versionId: id.version,
    versionNumber: 3,
    dataHash: "d".repeat(64),
    schemaHash: "e".repeat(64),
    projectionHash: "f".repeat(64),
    available: true,
  },
  columns: [
    {
      id: "12121212-1212-4212-8212-121212121212",
      name: "weekly_ai_assisted_learning_minutes",
      confirmedType: "NUMERIC",
      confirmationStatus: "CONFIRMED",
      confirmationKnown: true,
      confirmed: true,
      unit: "minutes/week",
      missingRatio: 0.015,
      qualityWarning: false,
      sensitive: false,
      displayValue: "weekly_ai_assisted_learning_minutes",
    },
    {
      id: "13131313-1313-4313-8313-131313131313",
      name: "final_learning_engagement_score",
      confirmedType: "NUMERIC",
      confirmationStatus: "CONFIRMED",
      confirmationKnown: true,
      confirmed: true,
      unit: "points",
      missingRatio: 0.02,
      qualityWarning: true,
      sensitive: false,
      displayValue: "final_learning_engagement_score",
    },
  ],
  qualityWarnings: ["final_learning_engagement_score: review required"],
  plan: {
    status: "APPROVED",
    knownStatus: true,
    tone: "success",
    id: id.plan,
    projectId: id.project,
    datasetVersionId: id.version,
    researchQuestionVersionId: "14141414-1414-4414-8414-141414141414",
    goal: "CORRELATION",
    method: "PEARSON_CORRELATION",
    input: {
      researchQuestionVersionId: "14141414-1414-4414-8414-141414141414",
      datasetVersionId: id.version,
      analysisGoal: "CORRELATION",
      method: "PEARSON_CORRELATION",
      dependentVariableIds: ["13131313-1313-4313-8313-131313131313"],
      independentVariableIds: ["12121212-1212-4212-8212-121212121212"],
      controlVariableIds: [],
      missingDataMode: "COMPLETE_CASE",
      sampleFilter: null,
      confidenceLevel: 0.95,
      alternative: "TWO_SIDED",
      varianceMode: "WELCH",
      independenceConfirmed: false,
      pairingConfirmed: false,
      pairIdColumnId: null,
      assumptionConfirmations: [],
      acknowledgedQualityIssueIds: [],
      sensitiveColumnAcknowledgements: [],
    },
    validationHash: "1".repeat(64),
    validationWarnings: ["OUTLIER_INFLUENCE requires review"],
    approvalId: id.approval,
    approvalPayloadHash: "2".repeat(64),
    approvalStale: false,
    lockVersion: 4,
    invalidationReason: null,
    checks: [
      {
        status: "PASSED",
        knownStatus: true,
        tone: "success",
        id: "15151515-1515-4515-8515-151515151515",
        code: "DATA_TYPE",
        subjectKey: "__plan__",
        explanation: "Declared columns are numeric.",
        blocksApproval: false,
        requiresConfirmation: false,
        checkedAt: "2026-08-04T09:00:00Z",
      },
    ],
    permissionsKnown: true,
    allowedActions: new Set(["analysis_plan.read", "analysis_plan.run"]),
  },
  approval: {
    status: "APPROVED",
    knownStatus: true,
    tone: "success",
    id: id.approval,
    targetId: id.plan,
    payloadHash: "2".repeat(64),
    expiresAt: null,
    expired: false,
    stale: false,
    decisionReason: "Reviewed against the validated Plan.",
    permissionsKnown: true,
    allowedActions: new Set(),
  },
  run: {
    status: "COMPLETED",
    knownStatus: true,
    tone: "success",
    id: id.run,
    projectId: id.project,
    planId: id.plan,
    datasetVersionId: id.version,
    approvalId: id.approval,
    runNumber: 2,
    jobId: id.job,
    effectiveN: 1248,
    inputHash: "3".repeat(64),
    parametersHash: "4".repeat(64),
    environmentHash: "5".repeat(64),
    environment: {
      python: "3.14.3",
      scipy: "1.17.1",
      statsmodels: "0.14.6",
    },
    resultCount: 1,
    errorCode: null,
    invalidationReason: null,
    permissionsKnown: true,
    allowedActions: new Set(["analysis_run.invalidate"]),
  },
  results: [
    result("CORRELATION", {
      coefficient: 0.4123456789012345,
      p_value: 0.0000031,
      confidence_interval: { lower: 0.36, upper: 0.46, level: 0.95 },
      effective_n: 1248,
      missing_n: 27,
      alternative: "two-sided",
    }),
  ],
  job: {
    status: "COMPLETED",
    knownStatus: true,
    tone: "success",
    id: id.job,
    kind: "ANALYSIS",
    accepted: true,
    progress: 100,
    currentStep: "finalized",
    retryable: false,
    errorCode: null,
  },
  figurePlan: null,
  renderRun: null,
  figure: null,
  suggestions: [
    {
      kind: "METHOD",
      availability: "DEGRADED",
      deterministic: false,
      text: null,
      reason: "No production suggestion provider is configured.",
    },
  ],
  capabilities: {
    permissionsKnown: true,
    createPlan: allowed(true),
    updatePlan: allowed(false),
    validatePlan: allowed(false),
    requestPlanApproval: allowed(false),
    runAnalysis: allowed(true),
    invalidateRun: allowed(true),
    retryJob: allowed(false),
    cancelJob: allowed(false),
    createFigurePlan: allowed(true),
    renderFigure: allowed(false, "No READY FigurePlan is selected."),
    requestFigureConfirmation: allowed(
      false,
      "No reviewable Figure is selected.",
    ),
    decideFigureConfirmation: allowed(
      false,
      "No pending Figure confirmation is selected.",
    ),
    downloadArtifact: allowed(false, "No available Figure is selected."),
    requestSuggestion: allowed(false, "Suggestion provider is not configured."),
    requestInterpretation: allowed(
      false,
      "Interpretation provider is not configured.",
    ),
  },
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
  integrationPending: [
    "Open Design UI implementation",
    "Production route integration",
  ],
}

const ready = (
  workspace: AnalysisWorkspaceViewModel,
): AnalysisWorkspaceWorkspaceProps => ({
  content: { state: "ready", data: workspace },
  pendingAction: null,
  mutationError: null,
  onRetry: () => undefined,
  onEvent: () => undefined,
  initialView: "plan",
  onViewChange: () => undefined,
})

const workspace = (
  overrides: Partial<AnalysisWorkspaceViewModel>,
): AnalysisWorkspaceViewModel => ({ ...baseWorkspace, ...overrides })

export const analysisWorkspaceReadyFixture = ready(baseWorkspace)
export const analysisWorkspaceLoadingFixture: AnalysisWorkspaceWorkspaceProps =
  {
    ...ready(baseWorkspace),
    content: { state: "loading", label: "Loading analysis workspace" },
  }
export const analysisWorkspaceEmptyFixture = ready(
  workspace({
    dataset: null,
    columns: [],
    qualityWarnings: [],
    plan: null,
    approval: null,
    run: null,
    results: [],
    job: null,
  }),
)

const error = (code: string, forbidden = false): UiErrorViewModel => ({
  title: forbidden ? "Access unavailable" : "Workspace unavailable",
  message: "The server did not disclose this resource.",
  code,
  requestId: "request-stage3",
  retryable: false,
  forbidden,
  notFound: code === "RESOURCE_NOT_FOUND",
  conflict: false,
})

export const analysisWorkspaceErrorFixture: AnalysisWorkspaceWorkspaceProps = {
  ...ready(baseWorkspace),
  content: { state: "error", error: error("SERVICE_UNAVAILABLE") },
}
export const analysisWorkspaceForbiddenFixture: AnalysisWorkspaceWorkspaceProps =
  {
    ...ready(baseWorkspace),
    content: { state: "error", error: error("RESOURCE_NOT_FOUND", true) },
  }
export const analysisWorkspaceReadOnlyFixture = ready(
  workspace({
    capabilities: Object.fromEntries(
      Object.entries(baseWorkspace.capabilities).map(([key, value]) => [
        key,
        typeof value === "boolean"
          ? value
          : allowed(false, "Read-only access."),
      ]),
    ) as AnalysisWorkspaceViewModel["capabilities"],
  }),
)
export const analysisWorkspacePermissionsUnknownFixture = ready(
  workspace({
    capabilities: {
      ...baseWorkspace.capabilities,
      permissionsKnown: false,
      createPlan: allowed(false, "Permissions are unknown."),
      runAnalysis: allowed(false, "Permissions are unknown."),
      invalidateRun: allowed(false, "Permissions are unknown."),
    },
  }),
)
export const analysisWorkspaceDegradedFixture = ready(
  workspace({
    suggestions: [
      {
        kind: "METHOD",
        availability: "DEGRADED",
        deterministic: false,
        text: null,
        reason:
          "Provider unavailable; deterministic analysis remains available.",
      },
    ],
  }),
)
export const analysisWorkspaceUnknownFixture = ready(
  workspace({
    plan: baseWorkspace.plan
      ? {
          ...baseWorkspace.plan,
          status: "FUTURE_ANALYSIS_PLAN_STATE",
          knownStatus: false,
          tone: "degraded",
          permissionsKnown: false,
          allowedActions: new Set(),
        }
      : null,
    capabilities: {
      ...baseWorkspace.capabilities,
      permissionsKnown: false,
      runAnalysis: allowed(false, "Status or permissions are unknown."),
    },
  }),
)

export const analysisWorkspaceUnconfirmedColumnsFixture = ready(
  workspace({
    columns: baseWorkspace.columns.map((column, index) =>
      index === 0
        ? {
            ...column,
            confirmationStatus: "UNCONFIRMED",
            confirmed: false,
            qualityWarning: true,
          }
        : column,
    ),
  }),
)
export const analysisWorkspaceSensitiveAckFixture = ready(
  workspace({
    columns: baseWorkspace.columns.map((column, index) =>
      index === 0
        ? { ...column, sensitive: true, displayValue: "[MASKED]" }
        : column,
    ),
    qualityWarnings: ["Sensitive acknowledgement required"],
  }),
)

function planStatus(status: string, stale = false) {
  return ready(
    workspace({
      plan: baseWorkspace.plan
        ? {
            ...baseWorkspace.plan,
            status,
            knownStatus: status !== "FUTURE_ANALYSIS_PLAN_STATE",
            tone: ["REJECTED", "INVALIDATED"].includes(status)
              ? "danger"
              : ["NEEDS_INPUT", "NEEDS_APPROVAL"].includes(status)
                ? "warning"
                : "info",
            approvalStale: stale,
          }
        : null,
    }),
  )
}

export const analysisWorkspacePlanDraftFixture = planStatus("DRAFT")
export const analysisWorkspacePlanNeedsInputFixture = planStatus("NEEDS_INPUT")
export const analysisWorkspacePlanReadyFixture = planStatus("READY")
export const analysisWorkspacePlanPendingApprovalFixture = ready(
  workspace({
    plan: baseWorkspace.plan
      ? {
          ...baseWorkspace.plan,
          status: "NEEDS_APPROVAL",
          tone: "warning",
        }
      : null,
    approval: baseWorkspace.approval
      ? {
          ...baseWorkspace.approval,
          status: "PENDING",
          tone: "warning",
          decisionReason: null,
        }
      : null,
    capabilities: {
      ...baseWorkspace.capabilities,
      requestPlanApproval: allowed(false, "Approval is already pending."),
      runAnalysis: allowed(false, "Current approval is still pending."),
    },
  }),
)
export const analysisWorkspacePlanApprovedFixture = planStatus("APPROVED")
export const analysisWorkspacePlanRejectedFixture = planStatus("REJECTED")
export const analysisWorkspacePlanStaleFixture = planStatus("APPROVED", true)
export const analysisWorkspacePlanInvalidatedFixture = planStatus("INVALIDATED")

function checkStatus(status: string, blocksApproval: boolean) {
  return ready(
    workspace({
      plan: baseWorkspace.plan
        ? {
            ...baseWorkspace.plan,
            checks: baseWorkspace.plan.checks.map((check) => ({
              ...check,
              status,
              tone:
                status === "FAILED"
                  ? "danger"
                  : status === "PASSED"
                    ? "success"
                    : "warning",
              blocksApproval,
              requiresConfirmation: status === "REQUIRES_USER_CONFIRMATION",
            })),
          }
        : null,
    }),
  )
}

export const analysisWorkspaceAssumptionPassFixture = checkStatus(
  "PASSED",
  false,
)
export const analysisWorkspaceAssumptionWarningFixture = checkStatus(
  "WARNING",
  false,
)
export const analysisWorkspaceAssumptionFailFixture = checkStatus(
  "FAILED",
  true,
)
export const analysisWorkspaceAssumptionConfirmFixture = checkStatus(
  "REQUIRES_USER_CONFIRMATION",
  true,
)

function runStatus(
  status: string,
  retryable: boolean,
  errorCode: string | null,
) {
  return ready(
    workspace({
      run: baseWorkspace.run
        ? {
            ...baseWorkspace.run,
            status,
            tone: status === "FAILED" ? "danger" : "info",
            errorCode,
          }
        : null,
      job: baseWorkspace.job
        ? { ...baseWorkspace.job, status, retryable, errorCode }
        : null,
      results: status === "COMPLETED" ? baseWorkspace.results : [],
    }),
  )
}

export const analysisWorkspaceQueuedFixture = runStatus("QUEUED", true, null)
export const analysisWorkspaceRunningFixture = runStatus("RUNNING", true, null)
export const analysisWorkspaceCompletedFixture = runStatus(
  "COMPLETED",
  false,
  null,
)
export const analysisWorkspaceFailedRetryableFixture = runStatus(
  "FAILED",
  true,
  "WORKER_INTERRUPTED",
)
export const analysisWorkspaceFailedFinalFixture = runStatus(
  "FAILED",
  false,
  "EXTERNAL_OUTPUT_INVALID",
)
export const analysisWorkspaceInvalidatedFixture = runStatus(
  "INVALIDATED",
  false,
  null,
)

export const analysisWorkspaceJobRetryAllowedFixture = ready(
  workspace({
    run: baseWorkspace.run
      ? {
          ...baseWorkspace.run,
          status: "FAILED",
          tone: "danger",
          errorCode: "WORKER_INTERRUPTED",
        }
      : null,
    job: baseWorkspace.job
      ? {
          ...baseWorkspace.job,
          status: "FAILED",
          tone: "danger",
          retryable: true,
          errorCode: "WORKER_INTERRUPTED",
        }
      : null,
    results: [],
    capabilities: {
      ...baseWorkspace.capabilities,
      retryJob: allowed(true),
      cancelJob: allowed(false, "Failed Jobs cannot be cancelled."),
    },
  }),
)

export const analysisWorkspaceJobCancelAllowedFixture = ready(
  workspace({
    run: baseWorkspace.run
      ? { ...baseWorkspace.run, status: "RUNNING", tone: "info" }
      : null,
    job: baseWorkspace.job
      ? {
          ...baseWorkspace.job,
          status: "RUNNING",
          tone: "info",
          progress: 38,
          currentStep: "computing",
          retryable: false,
        }
      : null,
    results: [],
    capabilities: {
      ...baseWorkspace.capabilities,
      retryJob: allowed(false, "Running Jobs cannot be retried."),
      cancelJob: allowed(true),
    },
  }),
)

export const analysisWorkspaceDescriptiveFixture = ready(
  workspace({
    results: [
      result("DESCRIPTIVE_NUMERIC", {
        column_name: "weekly_ai_assisted_learning_minutes",
        n: 1248,
        missing_n: 27,
        mean: 43.12345678901234,
        standard_deviation: 12.5,
        q1: 35,
        median: 42,
        q3: 51,
      }),
      result(
        "DESCRIPTIVE_CATEGORICAL",
        {
          column_name: "study_group_with_an_exceptionally_long_label",
          n: 12,
          missing_n: 1,
          categories: {
            control: { count: 7, proportion: 0.5833333333333334 },
            intervention: { count: 5, proportion: 0.4166666666666667 },
          },
        },
        { id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc", primary: false },
      ),
    ],
  }),
)
export const analysisWorkspaceCorrelationSignificantFixture =
  analysisWorkspaceReadyFixture
export const analysisWorkspaceCorrelationNonSignificantFixture = ready(
  workspace({
    results: [
      result("CORRELATION", {
        coefficient: 0.0123456789012345,
        p_value: 0.671,
        confidence_interval: { lower: -0.04, upper: 0.06, level: 0.95 },
        effective_n: 50000,
        missing_n: 0,
      }),
    ],
  }),
)
export const analysisWorkspaceGroupComparisonFixture = ready(
  workspace({
    results: [
      result("GROUP_COMPARISON", {
        groups: [
          { label: "control", n: 612, mean: 42.125 },
          { label: "intervention", n: 636, mean: 47.875 },
        ],
        mean_difference: -5.75,
        statistic: -4.041451884327381,
        df: 4.959183673469389,
        p_value: 0.01007694334798886,
        confidence_interval: {
          lower: -7.981711481338788,
          upper: -3.5182885186612123,
          level: 0.95,
        },
        effect_size: { name: "cohen_d", value: -0.4310889132455348 },
      }),
    ],
  }),
)
export const analysisWorkspaceRegressionFixture = ready(
  workspace({
    results: [
      result("REGRESSION", {
        effective_n: 1248,
        intercept: {
          coefficient: 1.2,
          standard_error: 0.5416025603090636,
          p_value: 0.11350247494979655,
          confidence_interval: {
            lower: -0.5236210669877759,
            upper: 2.923621066987776,
            level: 0.95,
          },
        },
        slope: {
          coefficient: 2,
          standard_error: 0.16329931618554513,
          p_value: 0.001172216444716885,
          confidence_interval: {
            lower: 1.480308694549956,
            upper: 2.519691305450044,
            level: 0.95,
          },
        },
        r_squared: 0.9803921568627452,
      }),
    ],
  }),
)

const figurePlan = {
  status: "READY",
  knownStatus: true,
  tone: "success" as const,
  id: id.figurePlan,
  projectId: id.project,
  datasetVersionId: id.version,
  analysisRunId: id.run,
  analysisResultId: id.result,
  chartType: "SCATTER" as const,
  caption:
    "Association between weekly AI-assisted learning time and engagement score",
  parameters: {
    kind: "SCATTER",
    x_column_id: "12121212-1212-4212-8212-121212121212",
    y_column_id: "13131313-1313-4313-8313-131313131313",
    x_label: "Weekly AI-assisted learning time",
    y_label: "Final learning engagement score",
    x_unit: "minutes/week",
    y_unit: "points",
    dpi: 144,
  },
  planHash: "8".repeat(64),
  lockVersion: 1,
  invalidationReason: null,
  transportAvailable: true as const,
  permissionsKnown: true,
  allowedActions: new Set(["figure_plan.read", "figure_plan.render"]),
}

const renderRun = (status: string) => ({
  status,
  knownStatus: true,
  tone: status === "FAILED" ? ("danger" as const) : ("info" as const),
  id: id.renderRun,
  projectId: id.project,
  figurePlanId: id.figurePlan,
  datasetVersionId: id.version,
  jobId: id.job,
  figureId: status === "COMPLETED" ? id.figure : null,
  renderNumber: 1,
  inputHash: "7".repeat(64),
  parametersHash: "8".repeat(64),
  environmentHash: status === "COMPLETED" ? "6".repeat(64) : null,
  errorCode: status === "FAILED" ? "FIGURE_RENDER_FAILED" : null,
  retryable: status === "FAILED",
  transportAvailable: true as const,
  permissionsKnown: true,
  allowedActions: new Set(
    status === "FAILED"
      ? ["figure_render_run.retry"]
      : status === "RUNNING"
        ? ["figure_render_run.cancel"]
        : [],
  ),
})

const figure = (status: string, issue = false): FigureViewModel => ({
  status,
  knownStatus: true,
  tone: status === "INVALIDATED" || status === "FAILED" ? "danger" : "info",
  id: id.figure,
  projectId: id.project,
  figurePlanId: id.figurePlan,
  renderRunId: id.renderRun,
  datasetVersionId: id.version,
  analysisRunId: id.run,
  analysisResultId: id.result,
  versionNumber: 1,
  chartType: "SCATTER",
  caption:
    "Association between weekly AI-assisted learning time and engagement score",
  aggregateHash: "9".repeat(64),
  confirmationApprovalId: status === "CONFIRMED" ? id.approval : null,
  approvalStale: false,
  invalidationReason:
    status === "INVALIDATED" ? "Upstream AnalysisRun invalidated." : null,
  issues: issue
    ? [
        {
          status: "OPEN",
          knownStatus: true,
          tone: "warning",
          id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
          issueType: "MISSING_UNIT",
          severity: "WARNING",
          message: "The y-axis unit requires explicit review.",
          blocksConfirmation: false,
        },
      ]
    : [],
  artifacts: [
    ["PNG", "Publication PNG"],
    ["SVG", "Vector SVG"],
    ["PDF", "Print PDF"],
    ["CODE", "System template code"],
  ].map(([kind, label], index) => ({
    status: "AVAILABLE",
    knownStatus: true,
    tone: "success",
    id: `eeeeeeee-eeee-4eee-8ee${index}-eeeeeeeeeee${index}`,
    kind: kind as "PNG" | "SVG" | "PDF" | "CODE",
    label,
    sha256: String(index + 1).repeat(64),
    downloadable: status !== "INVALIDATED",
    masked: false,
  })),
  transportAvailable: true,
  permissionsKnown: true,
  allowedActions: new Set(
    status === "INVALIDATED"
      ? ["figure.read"]
      : ["figure.read", "figure.request_confirmation", "figure.download"],
  ),
})

function figureState(status: string, issue = false) {
  return ready(
    workspace({
      figurePlan,
      renderRun: renderRun("COMPLETED"),
      figure: figure(status, issue),
      capabilities: {
        ...baseWorkspace.capabilities,
        renderFigure: allowed(true),
        requestFigureConfirmation: allowed(status !== "INVALIDATED"),
        downloadArtifact: allowed(status !== "INVALIDATED"),
      },
    }),
  )
}

export const analysisWorkspaceFigureDraftFixture = figureState("DRAFT")
export const analysisWorkspaceFigureRenderingFixture = ready(
  workspace({
    figurePlan,
    renderRun: renderRun("RUNNING"),
    figure: null,
  }),
)
export const analysisWorkspaceFigureReadyFixture = figureState("READY")
export const analysisWorkspaceFigureNeedsReviewFixture = figureState(
  "NEEDS_REVIEW",
  true,
)
export const analysisWorkspaceFigureConfirmedFixture = figureState("CONFIRMED")
export const analysisWorkspaceFigureFailedFixture = ready(
  workspace({
    figurePlan,
    renderRun: renderRun("FAILED"),
    figure: null,
  }),
)
export const analysisWorkspaceFigureInvalidatedFixture =
  figureState("INVALIDATED")

export const analysisWorkspaceFigureApprovalDecisionFixture = ready(
  workspace({
    figurePlan,
    renderRun: renderRun("COMPLETED"),
    figure: {
      ...figure("NEEDS_REVIEW", true),
      confirmationApprovalId: id.approval,
    },
    approval: baseWorkspace.approval
      ? {
          ...baseWorkspace.approval,
          status: "PENDING",
          tone: "warning",
          targetId: id.figure,
          decisionReason: null,
          allowedActions: new Set(["approval.decide"]),
        }
      : null,
    capabilities: {
      ...baseWorkspace.capabilities,
      requestFigureConfirmation: allowed(
        false,
        "Figure confirmation is already pending.",
      ),
      decideFigureConfirmation: allowed(true),
      downloadArtifact: allowed(true),
    },
  }),
)

export const analysisWorkspaceFigureJobCancelAllowedFixture = ready(
  workspace({
    figurePlan,
    renderRun: renderRun("RUNNING"),
    figure: null,
    job: baseWorkspace.job
      ? {
          ...baseWorkspace.job,
          status: "RUNNING",
          tone: "info",
          kind: "FIGURE",
          progress: 42,
          currentStep: "rendering-svg",
          retryable: false,
        }
      : null,
    capabilities: {
      ...baseWorkspace.capabilities,
      cancelJob: allowed(true),
      retryJob: allowed(false, "Running Jobs cannot be retried."),
    },
  }),
)

export const analysisWorkspaceMaskedArtifactFixture = ready(
  workspace({
    figurePlan,
    renderRun: renderRun("COMPLETED"),
    figure: {
      ...figure("READY"),
      artifacts: figure("READY").artifacts.map((artifact, index) =>
        index === 0
          ? { ...artifact, masked: true, downloadable: false }
          : artifact,
      ),
    },
    capabilities: {
      ...baseWorkspace.capabilities,
      downloadArtifact: allowed(false, "Artifact content is masked."),
    },
  }),
)

export const analysisWorkspaceDownloadScopeDeniedFixture = ready(
  workspace({
    figurePlan,
    renderRun: renderRun("COMPLETED"),
    figure: {
      ...figure("READY"),
      artifacts: figure("READY").artifacts.map((artifact) => ({
        ...artifact,
        downloadable: false,
      })),
    },
    readScopes: baseWorkspace.readScopes.filter(
      (scope) => scope !== "artifact",
    ),
    capabilities: {
      ...baseWorkspace.capabilities,
      downloadArtifact: allowed(false, "Artifact read scope is unavailable."),
    },
  }),
)

export const analysisWorkspaceMutationConflictFixture: AnalysisWorkspaceWorkspaceProps =
  {
    ...ready(baseWorkspace),
    mutationError: {
      title: "Workspace changed",
      message: "Refresh the current server state before retrying this action.",
      code: "LOCK_VERSION_MISMATCH",
      requestId: "request-stage4-conflict",
      retryable: false,
      forbidden: false,
      notFound: false,
      conflict: true,
    },
  }

export const analysisWorkspaceLongContentFixture = ready(
  workspace({
    qualityWarnings: [
      "A very long quality warning that must wrap without exposing a sensitive sample value or changing the scientific fact represented by the server.",
    ],
  }),
)

export const analysisWorkspaceFixtureCatalog = [
  ["ready", analysisWorkspaceReadyFixture],
  ["loading", analysisWorkspaceLoadingFixture],
  ["empty", analysisWorkspaceEmptyFixture],
  ["error", analysisWorkspaceErrorFixture],
  ["forbidden", analysisWorkspaceForbiddenFixture],
  ["read-only", analysisWorkspaceReadOnlyFixture],
  ["permissions-unknown", analysisWorkspacePermissionsUnknownFixture],
  ["degraded", analysisWorkspaceDegradedFixture],
  ["unknown", analysisWorkspaceUnknownFixture],
  ["unconfirmed-columns", analysisWorkspaceUnconfirmedColumnsFixture],
  ["quality-warnings", analysisWorkspaceReadyFixture],
  ["sensitive-ack-required", analysisWorkspaceSensitiveAckFixture],
  ["plan-draft", analysisWorkspacePlanDraftFixture],
  ["plan-needs-input", analysisWorkspacePlanNeedsInputFixture],
  ["plan-ready", analysisWorkspacePlanReadyFixture],
  ["plan-pending-approval", analysisWorkspacePlanPendingApprovalFixture],
  ["plan-approved", analysisWorkspacePlanApprovedFixture],
  ["plan-rejected", analysisWorkspacePlanRejectedFixture],
  ["plan-stale", analysisWorkspacePlanStaleFixture],
  ["plan-invalidated", analysisWorkspacePlanInvalidatedFixture],
  ["assumption-pass", analysisWorkspaceAssumptionPassFixture],
  ["assumption-warning", analysisWorkspaceAssumptionWarningFixture],
  ["assumption-fail", analysisWorkspaceAssumptionFailFixture],
  ["assumption-confirm", analysisWorkspaceAssumptionConfirmFixture],
  ["analysis-queued", analysisWorkspaceQueuedFixture],
  ["analysis-running", analysisWorkspaceRunningFixture],
  ["analysis-completed", analysisWorkspaceCompletedFixture],
  ["analysis-failed-retryable", analysisWorkspaceFailedRetryableFixture],
  ["analysis-failed-final", analysisWorkspaceFailedFinalFixture],
  ["analysis-invalidated", analysisWorkspaceInvalidatedFixture],
  ["job-retry-allowed", analysisWorkspaceJobRetryAllowedFixture],
  ["job-cancel-allowed", analysisWorkspaceJobCancelAllowedFixture],
  ["descriptive", analysisWorkspaceDescriptiveFixture],
  ["correlation-significant", analysisWorkspaceCorrelationSignificantFixture],
  [
    "correlation-non-significant",
    analysisWorkspaceCorrelationNonSignificantFixture,
  ],
  ["group-comparison", analysisWorkspaceGroupComparisonFixture],
  ["regression", analysisWorkspaceRegressionFixture],
  ["figure-draft", analysisWorkspaceFigureDraftFixture],
  ["figure-rendering", analysisWorkspaceFigureRenderingFixture],
  ["figure-ready", analysisWorkspaceFigureReadyFixture],
  ["figure-needs-review", analysisWorkspaceFigureNeedsReviewFixture],
  ["figure-confirmed", analysisWorkspaceFigureConfirmedFixture],
  ["figure-failed", analysisWorkspaceFigureFailedFixture],
  ["figure-invalidated", analysisWorkspaceFigureInvalidatedFixture],
  ["figure-approval-decision", analysisWorkspaceFigureApprovalDecisionFixture],
  ["figure-job-cancel-allowed", analysisWorkspaceFigureJobCancelAllowedFixture],
  ["masked-artifact", analysisWorkspaceMaskedArtifactFixture],
  ["download-scope-denied", analysisWorkspaceDownloadScopeDeniedFixture],
  ["mutation-conflict", analysisWorkspaceMutationConflictFixture],
  ["long-content", analysisWorkspaceLongContentFixture],
  ["desktop-light", analysisWorkspaceReadyFixture],
  ["tablet-dark", analysisWorkspaceReadyFixture],
  ["mobile-light", analysisWorkspaceReadyFixture],
] as const
