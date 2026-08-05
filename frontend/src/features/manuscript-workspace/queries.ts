import { useQuery } from "@tanstack/react-query"

import {
  ApiError,
  ApprovalsApi,
  JobsApi,
  ManuscriptsApi,
  ProjectsApi,
} from "@/api/adapter"

import { mapManuscriptWorkspace } from "./mappers"
import type { ManuscriptWorkspaceRouteSearch } from "./route-contract"

export type ManuscriptWorkspaceSelection = ManuscriptWorkspaceRouteSearch

export const manuscriptWorkspaceKeys = {
  workspace: (projectId: string, selection: ManuscriptWorkspaceSelection) =>
    ["projects", projectId, "manuscript-workspace", selection] as const,
}

function noDisclosure(message: string): never {
  throw new ApiError(
    404,
    "NOT_FOUND",
    message,
    "MANUSCRIPT_WORKSPACE_ROUTE_MISMATCH",
  )
}

function assertProject(
  projectId: string,
  value: { project_id: string },
  label: string,
) {
  if (value.project_id !== projectId)
    noDisclosure(`${label} is not available in this project.`)
}

async function loadSelectedManuscriptWorkspace(
  projectId: string,
  selection: ManuscriptWorkspaceSelection,
) {
  const projectEnvelope = await ProjectsApi.get(projectId)
  const project = projectEnvelope.data
  const permissionsKnown = Array.isArray(project.allowed_actions)
  const discovery = (await ManuscriptsApi.discover(projectId)).data
  for (const manuscript of discovery.manuscripts)
    assertProject(projectId, manuscript, "Discovered Manuscript")
  for (const version of discovery.versions)
    assertProject(projectId, version, "Discovered ManuscriptVersion")
  if (discovery.current_manuscript)
    assertProject(projectId, discovery.current_manuscript, "Current Manuscript")
  if (discovery.current_version)
    assertProject(
      projectId,
      discovery.current_version,
      "Current ManuscriptVersion",
    )
  if (
    (discovery.current_version && !discovery.current_manuscript) ||
    (discovery.current_manuscript?.current_version_id ?? null) !==
      (discovery.current_version?.id ?? null)
  ) {
    noDisclosure("Current Manuscript discovery facts are inconsistent.")
  }

  const [
    manuscriptEnvelope,
    versionEnvelope,
    runEnvelope,
    issueEnvelope,
    planEnvelope,
    auditEnvelope,
    claimEnvelope,
  ] = await Promise.all([
    selection.manuscript ? ManuscriptsApi.get(selection.manuscript) : null,
    selection.version ? ManuscriptsApi.version(selection.version) : null,
    selection.checkRun ? ManuscriptsApi.checkRun(selection.checkRun) : null,
    selection.issue ? ManuscriptsApi.issue(selection.issue) : null,
    selection.transformation
      ? ManuscriptsApi.fixPlan(selection.transformation)
      : null,
    selection.audit ? ManuscriptsApi.revisionAudit(selection.audit) : null,
    selection.claim ? ManuscriptsApi.claim(selection.claim) : null,
  ])

  const manuscript = manuscriptEnvelope?.data ?? null
  const selectedIssue = issueEnvelope?.data ?? null
  const transformation = planEnvelope?.data ?? null
  const revisionAudit = auditEnvelope?.data ?? null
  const claim = claimEnvelope?.data ?? null
  let checkRun = runEnvelope?.data ?? null
  let selectedVersion = versionEnvelope?.data ?? null

  for (const [label, value] of [
    ["Manuscript", manuscript],
    ["ManuscriptVersion", selectedVersion],
    ["CheckRun", checkRun],
    ["Issue", selectedIssue],
    ["FixPlan", transformation],
    ["RevisionAudit", revisionAudit],
    ["Claim", claim],
  ] as const) {
    if (value) assertProject(projectId, value, label)
  }

  if (!checkRun && selectedIssue) {
    checkRun = (
      await ManuscriptsApi.checkRun(selectedIssue.manuscript_check_run_id)
    ).data
    assertProject(projectId, checkRun, "CheckRun")
  }
  const versionId =
    selectedVersion?.id ??
    checkRun?.manuscript_version_id ??
    selectedIssue?.manuscript_version_id ??
    transformation?.manuscript_version_id
  if (!selectedVersion && versionId) {
    selectedVersion = (await ManuscriptsApi.version(versionId)).data
    assertProject(projectId, selectedVersion, "ManuscriptVersion")
  }

  const manuscriptId =
    manuscript?.id ??
    selectedVersion?.manuscript_id ??
    revisionAudit?.manuscript_id
  const resolvedManuscript =
    manuscript ??
    (manuscriptId ? (await ManuscriptsApi.get(manuscriptId)).data : null) ??
    discovery.current_manuscript ??
    discovery.manuscripts[0] ??
    null
  if (!selectedVersion && resolvedManuscript?.current_version_id) {
    selectedVersion =
      discovery.versions.find(
        (version) => version.id === resolvedManuscript.current_version_id,
      ) ?? null
  }
  if (resolvedManuscript)
    assertProject(projectId, resolvedManuscript, "Manuscript")

  if (
    selectedVersion &&
    resolvedManuscript &&
    selectedVersion.manuscript_id !== resolvedManuscript.id
  ) {
    noDisclosure("The selected version is not part of this Manuscript.")
  }
  if (
    checkRun &&
    selectedVersion &&
    checkRun.manuscript_version_id !== selectedVersion.id
  ) {
    noDisclosure("The CheckRun does not match the selected version.")
  }
  if (
    selectedIssue &&
    checkRun &&
    selectedIssue.manuscript_check_run_id !== checkRun.id
  ) {
    noDisclosure("The Issue does not match the selected CheckRun.")
  }
  if (
    transformation &&
    selectedVersion &&
    transformation.manuscript_version_id !== selectedVersion.id
  ) {
    noDisclosure("The FixPlan does not match the selected version.")
  }
  if (
    revisionAudit &&
    resolvedManuscript &&
    revisionAudit.manuscript_id !== resolvedManuscript.id
  ) {
    noDisclosure("The Revision Audit does not match the selected Manuscript.")
  }

  const versions = resolvedManuscript
    ? discovery.versions.filter(
        (version) => version.manuscript_id === resolvedManuscript.id,
      )
    : []
  if (
    versions.some(
      (version) =>
        version.project_id !== projectId ||
        version.manuscript_id !== resolvedManuscript?.id,
    )
  ) {
    noDisclosure("Version history contains an unrelated resource.")
  }
  const issues = checkRun ? (await ManuscriptsApi.issues(checkRun.id)).data : []
  if (
    issues.some(
      (issue) =>
        issue.project_id !== projectId ||
        issue.manuscript_check_run_id !== checkRun?.id,
    )
  ) {
    noDisclosure("Issue list contains an unrelated resource.")
  }

  const approvalId =
    transformation?.approval_record_id ?? claim?.approval_record_id
  const approval = approvalId ? (await ApprovalsApi.get(approvalId)).data : null
  if (approval) {
    assertProject(projectId, approval, "Approval")
    const expected = transformation?.id ?? claim?.id
    if (approval.target_object_id !== expected)
      noDisclosure("Approval target does not match the selected resource.")
  }
  const jobId =
    checkRun?.job_id ?? transformation?.job_id ?? revisionAudit?.job_id
  const job = jobId ? (await JobsApi.get(jobId)).data : null
  if (job) {
    assertProject(projectId, job, "Job")
    const expectedResourceId =
      checkRun?.id ?? transformation?.id ?? revisionAudit?.id
    if (job.resource_id !== expectedResourceId)
      noDisclosure("Job target does not match the selected resource.")
  }

  return mapManuscriptWorkspace({
    projectId,
    permissionsKnown,
    discoveryState: discovery.state,
    projectAllowedActions: project.allowed_actions,
    manuscript: resolvedManuscript,
    versions,
    selectedVersion,
    checkRun,
    issues,
    selectedIssue,
    transformation,
    revisionAudit,
    claim,
    approval,
    job,
  })
}

export async function loadManuscriptWorkspace(
  projectId: string,
  selection: ManuscriptWorkspaceSelection,
) {
  try {
    return await loadSelectedManuscriptWorkspace(projectId, selection)
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 404 &&
      Object.keys(selection).length > 0
    ) {
      return loadSelectedManuscriptWorkspace(projectId, {})
    }
    throw error
  }
}

export function useManuscriptWorkspaceQuery(
  projectId: string,
  selection: ManuscriptWorkspaceSelection,
) {
  return useQuery({
    queryKey: manuscriptWorkspaceKeys.workspace(projectId, selection),
    queryFn: () => loadManuscriptWorkspace(projectId, selection),
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}
