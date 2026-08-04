import { useQuery } from "@tanstack/react-query"

import {
  ApiError,
  ApprovalsApi,
  DataCleaningApi,
  DataQualityApi,
  DatasetsApi,
  JobsApi,
  ProjectsApi,
} from "@/api/adapter"

import { mapDataWorkspace } from "./mappers"

export type DataWorkspaceSelection = {
  datasetId?: string
  versionId?: string
  qualityRunId?: string
  planId?: string
  approvalId?: string
  jobId?: string
  compareWithVersionId?: string
}

export const dataWorkspaceKeys = {
  workspace: (projectId: string, selection: DataWorkspaceSelection) =>
    ["projects", projectId, "data-workspace", selection] as const,
}

function assertProject(
  projectId: string,
  value: { project_id: string },
  label: string,
) {
  if (value.project_id !== projectId) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      `${label} does not match this project route.`,
      "DATA_WORKSPACE_ROUTE_MISMATCH",
    )
  }
}

export async function loadDataWorkspace(
  projectId: string,
  selection: DataWorkspaceSelection,
) {
  const [projectEnvelope, datasetsEnvelope] = await Promise.all([
    ProjectsApi.get(projectId),
    DatasetsApi.list(projectId),
  ])
  const datasets = datasetsEnvelope.data
  const [selectedRunEnvelope, selectedApprovalEnvelope] = await Promise.all([
    selection.qualityRunId ? DataQualityApi.get(selection.qualityRunId) : null,
    selection.approvalId ? ApprovalsApi.get(selection.approvalId) : null,
  ])
  const run = selectedRunEnvelope?.data ?? null
  const selectedApproval = selectedApprovalEnvelope?.data ?? null
  if (run) assertProject(projectId, run, "DataQualityRun")
  if (selectedApproval) assertProject(projectId, selectedApproval, "Approval")
  if (
    selectedApproval &&
    selectedApproval.target_object_type !== "cleaning_plan"
  ) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "Approval is not associated with a CleaningPlan.",
    )
  }
  const selectedPlanId =
    selection.planId ?? selectedApproval?.target_object_id ?? undefined
  const selectedPlanEnvelope = selectedPlanId
    ? await DataCleaningApi.get(selectedPlanId)
    : null
  const plan = selectedPlanEnvelope?.data ?? null
  if (plan) assertProject(projectId, plan, "CleaningPlan")
  const selectedVersionId =
    selection.versionId ??
    plan?.dataset_version_id ??
    run?.dataset_version_id ??
    undefined
  const selectedVersionEnvelope = selectedVersionId
    ? await DatasetsApi.version(selectedVersionId)
    : null
  const selectedVersion = selectedVersionEnvelope?.data ?? null
  if (selectedVersion)
    assertProject(projectId, selectedVersion, "DatasetVersion")
  const selectedDatasetId =
    selection.datasetId ?? selectedVersion?.dataset_id ?? datasets[0]?.id
  const datasetEnvelope = selectedDatasetId
    ? await DatasetsApi.get(selectedDatasetId)
    : null
  const dataset = datasetEnvelope?.data ?? null
  if (dataset) assertProject(projectId, dataset, "Dataset")
  const resolvedVersionId =
    selectedVersion?.id ?? dataset?.current_version_id ?? undefined
  const versionEnvelope = resolvedVersionId
    ? (selectedVersionEnvelope ??
      (await DatasetsApi.version(resolvedVersionId)))
    : null
  const version = versionEnvelope?.data ?? null
  if (version) assertProject(projectId, version, "DatasetVersion")
  if (dataset && version && version.dataset_id !== dataset.id) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "DatasetVersion does not belong to the selected Dataset.",
      "DATA_WORKSPACE_DATASET_VERSION_MISMATCH",
    )
  }

  const versionsEnvelope = dataset
    ? await DatasetsApi.versions(dataset.id)
    : null
  const versions = versionsEnvelope?.data ?? []
  if (
    dataset &&
    versions.some(
      (item) => item.project_id !== projectId || item.dataset_id !== dataset.id,
    )
  ) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "Dataset version history contains an unrelated resource.",
      "DATA_WORKSPACE_VERSION_HISTORY_MISMATCH",
    )
  }

  const [columnsEnvelope, previewEnvelope, jobEnvelope] = await Promise.all([
    version ? DatasetsApi.columns(version.id) : null,
    version && ["AVAILABLE", "INVALIDATED"].includes(version.status)
      ? DatasetsApi.preview(version.id, { limit: 20 })
      : null,
    selection.jobId ? JobsApi.get(selection.jobId) : null,
  ])
  if (run && version && run.dataset_version_id !== version.id) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "DataQualityRun does not match the selected DatasetVersion.",
    )
  }
  const issuesEnvelope = run
    ? await DataQualityApi.issues(run.id, { page: 1, page_size: 100 })
    : null
  if (plan && version && plan.dataset_version_id !== version.id) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "CleaningPlan does not match the selected DatasetVersion.",
    )
  }
  const approvalId = selectedApproval?.id ?? plan?.approval_record_id
  const approvalEnvelope = approvalId
    ? (selectedApprovalEnvelope ?? (await ApprovalsApi.get(approvalId)))
    : null
  const approval = approvalEnvelope?.data ?? null
  if (approval) assertProject(projectId, approval, "Approval")
  if (
    approval &&
    plan &&
    (approval.target_object_type !== "cleaning_plan" ||
      approval.target_object_id !== plan.id)
  ) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "Approval does not match the selected CleaningPlan.",
    )
  }
  const job = jobEnvelope?.data ?? null
  if (job) assertProject(projectId, job, "Job")
  const transformationEnvelope = plan?.transformation_id
    ? await DataCleaningApi.transformation(plan.transformation_id)
    : null
  const transformation = transformationEnvelope?.data ?? null
  if (transformation) {
    assertProject(projectId, transformation, "DataTransformation")
    if (
      !plan ||
      transformation.cleaning_plan_id !== plan.id ||
      transformation.source_dataset_version_id !== plan.dataset_version_id
    ) {
      throw new ApiError(
        404,
        "NOT_FOUND",
        "DataTransformation does not match the selected CleaningPlan.",
        "DATA_WORKSPACE_TRANSFORMATION_MISMATCH",
      )
    }
  }
  if (
    job &&
    transformation &&
    (job.resource_type !== "data_transformation" ||
      job.resource_id !== transformation.id)
  ) {
    throw new ApiError(
      404,
      "NOT_FOUND",
      "Job does not match the selected DataTransformation.",
      "DATA_WORKSPACE_TRANSFORMATION_JOB_MISMATCH",
    )
  }
  const comparisonEnvelope =
    dataset && version && selection.compareWithVersionId
      ? await DataCleaningApi.compare(
          dataset.id,
          selection.compareWithVersionId,
          version.id,
        )
      : null

  return mapDataWorkspace({
    projectId,
    project: projectEnvelope.data,
    datasets,
    dataset,
    version,
    versions,
    columns: columnsEnvelope?.data ?? [],
    preview: previewEnvelope?.data ?? null,
    run,
    issues: issuesEnvelope?.data ?? [],
    plan,
    approval,
    transformation,
    job,
    comparison: comparisonEnvelope?.data ?? null,
  })
}

export function useDataWorkspaceQuery(
  projectId: string,
  selection: DataWorkspaceSelection,
) {
  return useQuery({
    queryKey: dataWorkspaceKeys.workspace(projectId, selection),
    queryFn: () => loadDataWorkspace(projectId, selection),
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}
