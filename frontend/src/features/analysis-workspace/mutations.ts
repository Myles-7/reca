import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  AnalysisApi,
  ApiError,
  ApprovalsApi,
  FiguresApi,
  JobsApi,
} from "@/api/adapter"
import type {
  AnalysisPlanCreate,
  AnalysisPlanUpdate,
  AnalysisMethod as ApiAnalysisMethod,
  FigurePlanCreate,
} from "@/api/generated/types.gen"

import { mapUiError } from "../projects/mappers"
import type {
  AnalysisPlanInput,
  AnalysisWorkspaceViewModel,
  FigurePlanInput,
  SampleFilter,
} from "./model"
import { analysisWorkspaceKeys } from "./queries"
import type { AnalysisWorkspaceEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()
const implementedMethods = new Set([
  "DESCRIPTIVE_STATISTICS",
  "PEARSON_CORRELATION",
  "SPEARMAN_CORRELATION",
  "INDEPENDENT_TWO_GROUP",
  "PAIRED_TWO_GROUP",
  "SIMPLE_LINEAR_REGRESSION",
])

function apiMethod(method: AnalysisPlanInput["method"]): ApiAnalysisMethod {
  if (!implementedMethods.has(method)) {
    throw new ApiError(
      409,
      "CONFLICT",
      "This analysis method is not available in the current backend.",
      "ANALYSIS_METHOD_UNAVAILABLE",
    )
  }
  return method as ApiAnalysisMethod
}

function apiFilter(filter: SampleFilter | null) {
  if (!filter) return null
  switch (filter.operator) {
    case "EQUALS":
      return {
        operator: "EQUALS" as const,
        column_id: filter.columnId,
        value: filter.value,
      }
    case "IN":
      return {
        operator: "IN" as const,
        column_id: filter.columnId,
        values: [...filter.values],
      }
    case "IS_NULL":
    case "IS_NOT_NULL":
      return { operator: filter.operator, column_id: filter.columnId }
    case "NUMERIC_RANGE":
      return {
        operator: "NUMERIC_RANGE" as const,
        column_id: filter.columnId,
        minimum: filter.minimum,
        maximum: filter.maximum,
        include_minimum: filter.includeMinimum,
        include_maximum: filter.includeMaximum,
      }
  }
}

function apiPlan(input: AnalysisPlanInput): AnalysisPlanCreate {
  return {
    research_question_version_id: input.researchQuestionVersionId,
    dataset_version_id: input.datasetVersionId,
    analysis_goal: input.analysisGoal,
    method: apiMethod(input.method),
    dependent_variable_ids: [...input.dependentVariableIds],
    independent_variable_ids: [...input.independentVariableIds],
    control_variable_ids: [...input.controlVariableIds],
    missing_data_policy: { mode: input.missingDataMode },
    sample_filter: apiFilter(input.sampleFilter),
    parameters: {
      confidence_level: input.confidenceLevel,
      alternative: input.alternative,
      variance_mode: input.varianceMode,
      independence_confirmed: input.independenceConfirmed,
      pairing_confirmed: input.pairingConfirmed,
      pair_id_column_id: input.pairIdColumnId,
      assumption_confirmations: input.assumptionConfirmations as never[],
      acknowledged_quality_issue_ids: [...input.acknowledgedQualityIssueIds],
      sensitive_column_acknowledgements: [
        ...input.sensitiveColumnAcknowledgements,
      ],
    },
  }
}

export function apiPlanUpdate(input: AnalysisPlanInput): AnalysisPlanUpdate {
  const plan = apiPlan(input)
  return {
    analysis_goal: plan.analysis_goal,
    method: plan.method,
    dependent_variable_ids: plan.dependent_variable_ids,
    independent_variable_ids: plan.independent_variable_ids,
    control_variable_ids: plan.control_variable_ids,
    missing_data_policy: plan.missing_data_policy,
    sample_filter: plan.sample_filter,
    parameters: plan.parameters,
  }
}

function validPlanInput(input: AnalysisPlanInput) {
  const ids = [
    ...input.dependentVariableIds,
    ...input.independentVariableIds,
    ...input.controlVariableIds,
  ]
  return (
    implementedMethods.has(input.method) &&
    ids.length > 0 &&
    ids.length <= 20 &&
    new Set(ids).size === ids.length &&
    input.confidenceLevel > 0 &&
    input.confidenceLevel < 1
  )
}

function datasetIsCurrent(workspace: AnalysisWorkspaceViewModel) {
  return (
    workspace.dataset?.knownStatus === true &&
    workspace.dataset.status === "AVAILABLE" &&
    workspace.dataset.available
  )
}

function declaredColumnsAreConfirmed(
  workspace: AnalysisWorkspaceViewModel,
  input: AnalysisPlanInput,
) {
  const declared = new Set([
    ...input.dependentVariableIds,
    ...input.independentVariableIds,
    ...input.controlVariableIds,
  ])
  if (input.pairIdColumnId) declared.add(input.pairIdColumnId)
  return [...declared].every((columnId) => {
    const column = workspace.columns.find((item) => item.id === columnId)
    return (
      column?.confirmationKnown === true &&
      column.confirmed &&
      (!column.sensitive ||
        input.sensitiveColumnAcknowledgements.includes(column.id))
    )
  })
}

function planApprovalIsCurrent(workspace: AnalysisWorkspaceViewModel) {
  const plan = workspace.plan
  const approval = workspace.approval
  return (
    plan?.knownStatus === true &&
    plan.status === "APPROVED" &&
    plan.validationHash !== null &&
    !plan.approvalStale &&
    approval?.knownStatus === true &&
    approval.status === "APPROVED" &&
    approval.id === plan.approvalId &&
    approval.targetId === plan.id &&
    !approval.expired &&
    !approval.stale &&
    plan.approvalPayloadHash !== null &&
    approval.payloadHash === plan.approvalPayloadHash
  )
}

function validFigureInput(
  workspace: AnalysisWorkspaceViewModel,
  input: FigurePlanInput,
) {
  const kind = input.parameters.kind
  return (
    datasetIsCurrent(workspace) &&
    workspace.dataset?.versionId === input.datasetVersionId &&
    typeof kind === "string" &&
    kind === input.chartType &&
    input.caption.trim().length > 0 &&
    (input.analysisRunId === null ||
      (workspace.run?.knownStatus === true &&
        workspace.run.status === "COMPLETED" &&
        workspace.run.id === input.analysisRunId &&
        workspace.run.datasetVersionId === input.datasetVersionId)) &&
    (input.analysisResultId === null ||
      (workspace.results.some(
        (result) =>
          result.knownStatus &&
          result.id === input.analysisResultId &&
          result.runId === input.analysisRunId,
      ) &&
        input.analysisRunId !== null))
  )
}

function apiFigurePlan(input: FigurePlanInput): FigurePlanCreate {
  return {
    dataset_version_id: input.datasetVersionId,
    analysis_run_id: input.analysisRunId,
    analysis_result_id: input.analysisResultId,
    chart_type: input.chartType,
    parameters: input.parameters as FigurePlanCreate["parameters"],
    caption: input.caption,
  }
}

export function canExecuteAnalysisWorkspaceEvent(
  workspace: AnalysisWorkspaceViewModel | null,
  event: AnalysisWorkspaceEvent,
) {
  if (!workspace?.capabilities.permissionsKnown) return false
  const capabilities = workspace.capabilities
  switch (event.action) {
    case "create-analysis-plan":
      return (
        capabilities.createPlan.allowed &&
        datasetIsCurrent(workspace) &&
        workspace.dataset?.versionId === event.input.datasetVersionId &&
        validPlanInput(event.input) &&
        declaredColumnsAreConfirmed(workspace, event.input)
      )
    case "update-analysis-plan": {
      if (
        !capabilities.updatePlan.allowed ||
        workspace.plan?.id !== event.input.planId ||
        workspace.plan.lockVersion !== event.input.lockVersion ||
        workspace.plan.knownStatus !== true ||
        workspace.plan.datasetVersionId !== event.input.plan.datasetVersionId ||
        workspace.plan.researchQuestionVersionId !==
          event.input.plan.researchQuestionVersionId
      ) {
        return false
      }
      return (
        datasetIsCurrent(workspace) &&
        validPlanInput(event.input.plan) &&
        declaredColumnsAreConfirmed(workspace, event.input.plan)
      )
    }
    case "validate-analysis-plan":
      return (
        capabilities.validatePlan.allowed &&
        workspace.plan?.knownStatus === true &&
        workspace.plan.id === event.input.planId &&
        datasetIsCurrent(workspace)
      )
    case "request-analysis-approval":
      return (
        capabilities.requestPlanApproval.allowed &&
        workspace.plan?.knownStatus === true &&
        workspace.plan.id === event.input.planId &&
        workspace.plan.status === "READY" &&
        workspace.plan.validationHash !== null &&
        !workspace.plan.approvalStale
      )
    case "run-analysis":
      return (
        capabilities.runAnalysis.allowed &&
        workspace.plan?.id === event.input.planId &&
        datasetIsCurrent(workspace) &&
        planApprovalIsCurrent(workspace)
      )
    case "invalidate-analysis-run":
      return (
        capabilities.invalidateRun.allowed &&
        workspace.run?.knownStatus === true &&
        workspace.run.id === event.input.runId &&
        event.input.reason.trim().length > 0
      )
    case "retry-job":
      return (
        capabilities.retryJob.allowed &&
        workspace.job?.knownStatus === true &&
        workspace.job.id === event.input.jobId &&
        workspace.job.status === "FAILED" &&
        workspace.job.retryable
      )
    case "cancel-job":
      return (
        capabilities.cancelJob.allowed &&
        workspace.job?.knownStatus === true &&
        workspace.job.id === event.input.jobId &&
        ["QUEUED", "RUNNING"].includes(workspace.job.status) &&
        event.input.reason.trim().length > 0
      )
    case "create-figure-plan":
      return (
        capabilities.createFigurePlan.allowed &&
        validFigureInput(workspace, event.input)
      )
    case "render-figure":
      return (
        capabilities.renderFigure.allowed &&
        workspace.figurePlan?.knownStatus === true &&
        workspace.figurePlan.id === event.input.figurePlanId &&
        workspace.figurePlan.status === "READY" &&
        workspace.figurePlan.datasetVersionId ===
          workspace.dataset?.versionId &&
        datasetIsCurrent(workspace)
      )
    case "request-figure-confirmation":
      return (
        capabilities.requestFigureConfirmation.allowed &&
        workspace.figure?.knownStatus === true &&
        workspace.figure.id === event.input.figureId &&
        ["READY", "NEEDS_REVIEW"].includes(workspace.figure.status) &&
        workspace.figure.datasetVersionId === workspace.dataset?.versionId &&
        !workspace.figure.approvalStale &&
        !workspace.figure.issues.some(
          (issue) =>
            !issue.knownStatus ||
            (issue.status === "OPEN" && issue.blocksConfirmation),
        )
      )
    case "decide-figure-confirmation":
      return (
        capabilities.decideFigureConfirmation.allowed &&
        workspace.figure?.knownStatus === true &&
        workspace.approval?.knownStatus === true &&
        workspace.approval.id === event.input.approvalId &&
        workspace.approval.targetId === workspace.figure.id &&
        workspace.figure.confirmationApprovalId === workspace.approval.id &&
        workspace.approval.status === "PENDING" &&
        !workspace.approval.expired &&
        !workspace.approval.stale &&
        !workspace.figure.approvalStale
      )
    case "download-artifact":
      return (
        capabilities.downloadArtifact.allowed &&
        workspace.figure?.knownStatus === true &&
        workspace.figure.id === event.input.figureId &&
        workspace.figure.status !== "INVALIDATED" &&
        workspace.readScopes.includes("artifact") &&
        workspace.figure.artifacts.some(
          (artifact) =>
            artifact.kind === event.input.format &&
            artifact.knownStatus &&
            artifact.status === "AVAILABLE" &&
            artifact.sha256 !== null &&
            artifact.downloadable &&
            !artifact.masked,
        )
      )
    case "request-suggestion":
      return capabilities.requestSuggestion.allowed
    case "request-interpretation":
      return capabilities.requestInterpretation.allowed
  }
}

async function execute(projectId: string, event: AnalysisWorkspaceEvent) {
  switch (event.action) {
    case "create-analysis-plan":
      return AnalysisApi.create(projectId, apiPlan(event.input))
    case "update-analysis-plan": {
      return AnalysisApi.update(
        event.input.planId,
        apiPlanUpdate(event.input.plan),
        event.input.lockVersion,
      )
    }
    case "validate-analysis-plan":
      return AnalysisApi.validate(event.input.planId, key())
    case "request-analysis-approval":
      return AnalysisApi.requestApproval(event.input.planId)
    case "run-analysis":
      return AnalysisApi.run(
        event.input.planId,
        { run_reason: event.input.reason },
        key(),
      )
    case "invalidate-analysis-run":
      return AnalysisApi.invalidate(event.input.runId, event.input.reason)
    case "retry-job":
      return JobsApi.retry(event.input.jobId, key())
    case "cancel-job":
      return JobsApi.cancel(event.input.jobId, event.input.reason, key())
    case "create-figure-plan":
      return FiguresApi.create(projectId, apiFigurePlan(event.input))
    case "render-figure":
      return FiguresApi.render(
        event.input.figurePlanId,
        { reason: event.input.reason },
        key(),
      )
    case "request-figure-confirmation":
      return FiguresApi.requestConfirmation(event.input.figureId)
    case "decide-figure-confirmation":
      return event.input.decision === "APPROVE"
        ? ApprovalsApi.approve(
            event.input.approvalId,
            { decision_reason: event.input.reason, item_decisions: [] },
            key(),
          )
        : ApprovalsApi.reject(
            event.input.approvalId,
            {
              decision_reason: event.input.reason ?? "Rejected after review.",
              item_decisions: [],
            },
            key(),
          )
    case "download-artifact":
      return FiguresApi.download(event.input.figureId, event.input.format)
    case "request-suggestion":
      if (event.input.kind === "FIGURE") {
        return FiguresApi.recommend(projectId, {
          dataset_version_id: event.input.datasetVersionId,
        })
      }
      throw new ApiError(
        503,
        "SERVER",
        "Method suggestion provider is not configured.",
        "EXTERNAL_CAPABILITY_UNAVAILABLE",
      )
    case "request-interpretation":
      throw new ApiError(
        503,
        "SERVER",
        "This transport is not available in M5 Stage 3.",
        "EXTERNAL_CAPABILITY_UNAVAILABLE",
      )
  }
}

export function useAnalysisWorkspaceMutation(
  projectId: string,
  workspace: AnalysisWorkspaceViewModel | null,
  onSuccess?: (
    event: AnalysisWorkspaceEvent,
    result: Awaited<ReturnType<typeof execute>>,
  ) => void,
) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (event: AnalysisWorkspaceEvent) => execute(projectId, event),
    onSuccess: async (result, event) => {
      await queryClient.invalidateQueries({
        queryKey: analysisWorkspaceKeys.workspace(projectId, {}),
        exact: false,
      })
      onSuccess?.(event, result)
    },
  })
  return {
    mutate: (event: AnalysisWorkspaceEvent) => {
      if (canExecuteAnalysisWorkspaceEvent(workspace, event)) {
        mutation.mutate(event)
      }
    },
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
