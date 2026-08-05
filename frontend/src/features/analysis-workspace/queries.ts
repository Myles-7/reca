import { useQuery } from "@tanstack/react-query"

import {
  AnalysisApi,
  ApiError,
  ApprovalsApi,
  DatasetsApi,
  FiguresApi,
  JobsApi,
  ProjectsApi,
} from "@/api/adapter"

import { mapAnalysisWorkspace } from "./mappers"

export type AnalysisWorkspaceSelection = {
  datasetId?: string
  versionId?: string
  analysisPlanId?: string
  analysisRunId?: string
  analysisResultId?: string
  approvalId?: string
  jobId?: string
  figurePlanId?: string
  figureId?: string
  renderRunId?: string
}

export const analysisWorkspaceKeys = {
  workspace: (projectId: string, selection: AnalysisWorkspaceSelection) =>
    ["projects", projectId, "analysis-workspace", selection] as const,
}

function mismatch(label: string): never {
  throw new ApiError(
    404,
    "NOT_FOUND",
    `${label} is unavailable in this project.`,
    "ANALYSIS_WORKSPACE_ROUTE_MISMATCH",
  )
}

export async function loadAnalysisWorkspace(
  projectId: string,
  selection: AnalysisWorkspaceSelection,
) {
  const projectEnvelope = await ProjectsApi.get(projectId)
  const figureEnvelope = selection.figureId
    ? await FiguresApi.get(selection.figureId)
    : null
  const figure = figureEnvelope?.data ?? null
  if (figure && figure.project_id !== projectId) mismatch("Figure")
  const renderRunEnvelope = selection.renderRunId
    ? await FiguresApi.getRenderRun(selection.renderRunId)
    : figure
      ? await FiguresApi.getRenderRun(figure.figure_render_run_id)
      : null
  const renderRun = renderRunEnvelope?.data ?? null
  if (renderRun && renderRun.project_id !== projectId)
    mismatch("FigureRenderRun")
  if (figure && renderRun && figure.figure_render_run_id !== renderRun.id)
    mismatch("FigureRenderRun")
  const figurePlanEnvelope = selection.figurePlanId
    ? await FiguresApi.getPlan(selection.figurePlanId)
    : renderRun
      ? await FiguresApi.getPlan(renderRun.figure_plan_id)
      : figure
        ? await FiguresApi.getPlan(figure.figure_plan_id)
        : null
  const figurePlan = figurePlanEnvelope?.data ?? null
  if (figurePlan && figurePlan.project_id !== projectId) mismatch("FigurePlan")
  if (renderRun && figurePlan && renderRun.figure_plan_id !== figurePlan.id)
    mismatch("FigurePlan")

  const planEnvelope = selection.analysisPlanId
    ? await AnalysisApi.getPlan(selection.analysisPlanId)
    : null
  const analysisRunId =
    selection.analysisRunId ??
    figure?.analysis_run_id ??
    figurePlan?.analysis_run_id
  const runEnvelope = analysisRunId
    ? await AnalysisApi.getRun(analysisRunId)
    : null
  const plan = planEnvelope?.data ?? null
  const run = runEnvelope?.data ?? null
  if (plan && plan.project_id !== projectId) mismatch("AnalysisPlan")
  if (run && run.project_id !== projectId) mismatch("AnalysisRun")
  if (plan && run && run.analysis_plan_id !== plan.id) mismatch("AnalysisRun")

  const resolvedPlanEnvelope =
    !plan && run
      ? await AnalysisApi.getPlan(run.analysis_plan_id)
      : planEnvelope
  const resolvedPlan = resolvedPlanEnvelope?.data ?? null
  if (resolvedPlan && resolvedPlan.project_id !== projectId)
    mismatch("AnalysisPlan")

  const versionId =
    selection.versionId ??
    run?.dataset_version_id ??
    resolvedPlan?.dataset_version_id ??
    figure?.dataset_version_id ??
    figurePlan?.dataset_version_id ??
    renderRun?.dataset_version_id
  const versionEnvelope = versionId
    ? await DatasetsApi.version(versionId)
    : null
  const version = versionEnvelope?.data ?? null
  if (version && version.project_id !== projectId) mismatch("DatasetVersion")
  if (
    version &&
    resolvedPlan &&
    resolvedPlan.dataset_version_id !== version.id
  ) {
    mismatch("DatasetVersion")
  }
  const datasetId = selection.datasetId ?? version?.dataset_id
  const datasetEnvelope = datasetId ? await DatasetsApi.get(datasetId) : null
  const dataset = datasetEnvelope?.data ?? null
  if (dataset && dataset.project_id !== projectId) mismatch("Dataset")
  if (dataset && version && version.dataset_id !== dataset.id)
    mismatch("Dataset")

  const approvalId =
    selection.approvalId ??
    figure?.approval_record_id ??
    resolvedPlan?.approval_record_id
  const jobId = selection.jobId ?? renderRun?.job_id ?? run?.job_id
  const [
    columnsEnvelope,
    resultsEnvelope,
    approvalEnvelope,
    jobEnvelope,
    recommendationEnvelope,
  ] = await Promise.all([
    version ? DatasetsApi.columns(version.id) : null,
    run && run.status !== "QUEUED" && run.status !== "RUNNING"
      ? AnalysisApi.getResults(run.id)
      : null,
    approvalId ? ApprovalsApi.get(approvalId) : null,
    jobId ? JobsApi.get(jobId) : null,
    version
      ? FiguresApi.recommend(projectId, {
          dataset_version_id: version.id,
          analysis_run_id: run?.id,
        })
      : null,
  ])
  const approval = approvalEnvelope?.data ?? null
  const job = jobEnvelope?.data ?? null
  if (approval && approval.project_id !== projectId) mismatch("Approval")
  if (approval) {
    const validPlanApproval =
      resolvedPlan &&
      approval.target_object_type === "analysis_plan" &&
      approval.target_object_id === resolvedPlan.id
    const validFigureApproval =
      figure &&
      approval.target_object_type === "figure" &&
      approval.target_object_id === figure.id
    if (!validPlanApproval && !validFigureApproval) mismatch("Approval")
  }
  if (job && job.project_id !== projectId) mismatch("Job")
  if (
    job &&
    !(
      (run &&
        job.resource_type === "analysis_run" &&
        job.resource_id === run.id) ||
      (renderRun &&
        job.resource_type === "figure_render_run" &&
        job.resource_id === renderRun.id)
    )
  ) {
    mismatch("Job")
  }
  const results = resultsEnvelope?.data.results ?? []
  if (
    selection.analysisResultId &&
    !results.some((result) => result.id === selection.analysisResultId)
  ) {
    mismatch("AnalysisResult")
  }

  return mapAnalysisWorkspace({
    projectId,
    project: projectEnvelope.data,
    dataset,
    version,
    columns: columnsEnvelope?.data ?? [],
    plan: resolvedPlan,
    approval,
    run,
    results,
    job,
    figurePlan,
    renderRun,
    figure,
    figureRecommendation: recommendationEnvelope?.data ?? null,
  })
}

export function useAnalysisWorkspaceQuery(
  projectId: string,
  selection: AnalysisWorkspaceSelection,
) {
  return useQuery({
    queryKey: analysisWorkspaceKeys.workspace(projectId, selection),
    queryFn: () => loadAnalysisWorkspace(projectId, selection),
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}
