import { useQuery } from "@tanstack/react-query"

import {
  ApiError,
  ApprovalsApi,
  EvidenceGraphApi,
  ExportsApi,
  JobsApi,
  ManuscriptsApi,
  ProjectsApi,
} from "@/api/adapter"

import { mapEvidenceWorkspace } from "./mappers"
import type { EvidenceWorkspaceRouteSearch } from "./route-contract"

export type EvidenceWorkspaceSelection = EvidenceWorkspaceRouteSearch

export const evidenceWorkspaceKeys = {
  workspace: (projectId: string, selection: EvidenceWorkspaceSelection) =>
    ["projects", projectId, "evidence-workspace", selection] as const,
}

function noDisclosure(message: string): never {
  throw new ApiError(
    404,
    "NOT_FOUND",
    message,
    "EVIDENCE_WORKSPACE_ROUTE_MISMATCH",
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

async function loadSelectedEvidenceWorkspace(
  projectId: string,
  selection: EvidenceWorkspaceSelection,
) {
  const project = (await ProjectsApi.get(projectId)).data
  if (project.id !== projectId)
    noDisclosure("The Project response is inconsistent.")

  const [linkEnvelope, auditEnvelope, packageEnvelope, directExportEnvelope] =
    await Promise.all([
      selection.link ? EvidenceGraphApi.link(selection.link) : null,
      selection.audit ? EvidenceGraphApi.audit(selection.audit) : null,
      selection.package ? ExportsApi.package(selection.package) : null,
      selection.export ? ExportsApi.get(selection.export) : null,
    ])
  const selectedLink = linkEnvelope?.data ?? null
  const audit = auditEnvelope?.data ?? null
  const packageValue = packageEnvelope?.data ?? null
  let exportValue = directExportEnvelope?.data ?? null

  for (const [label, value] of [
    ["Evidence Link", selectedLink],
    ["Audit", audit],
    ["ReproPackage", packageValue],
    ["Export", exportValue],
  ] as const) {
    if (value) assertProject(projectId, value, label)
  }

  if (packageValue) {
    if (exportValue && exportValue.id !== packageValue.export_id)
      noDisclosure("The selected package is not part of the selected Export.")
    if (!exportValue)
      exportValue = (await ExportsApi.get(packageValue.export_id)).data
    assertProject(projectId, exportValue, "Export")
  }

  const claimId = selection.claim ?? selectedLink?.claim_id ?? null
  const selectedClaim = claimId
    ? (await ManuscriptsApi.claim(claimId)).data
    : null
  if (selectedClaim) assertProject(projectId, selectedClaim, "Claim")
  if (
    selectedLink &&
    selectedClaim &&
    selectedLink.claim_id !== selectedClaim.id
  )
    noDisclosure("The selected Link is not part of the selected Claim.")
  if (
    audit?.target_object_type === "CLAIM" &&
    selectedClaim &&
    audit.target_object_id !== selectedClaim.id
  )
    noDisclosure("The selected Audit is not for the selected Claim.")

  const loadPackageHistory =
    selection.view === "exports" ||
    Boolean(selection.export || selection.package)
  const [
    graphEnvelope,
    linksEnvelope,
    approvalEnvelope,
    jobEnvelope,
    auditJobEnvelope,
    packageHistoryEnvelope,
  ] = await Promise.all([
    EvidenceGraphApi.graph(projectId, {
      root_claim_id: selectedClaim?.id ?? null,
      depth: 4,
      include_invalidated: true,
      limit: 500,
    }),
    selectedClaim ? EvidenceGraphApi.links(selectedClaim.id, true) : null,
    exportValue?.approval_record_id
      ? ApprovalsApi.get(exportValue.approval_record_id)
      : null,
    exportValue?.job_id ? JobsApi.get(exportValue.job_id) : null,
    audit?.job_id ? JobsApi.get(audit.job_id) : null,
    loadPackageHistory
      ? ExportsApi.packages(projectId, { page: 1, page_size: 100 })
      : null,
  ])
  const graph = graphEnvelope.data
  const links = linksEnvelope?.data ?? []
  const approval = approvalEnvelope?.data ?? null
  const job = jobEnvelope?.data ?? null
  const auditJob = auditJobEnvelope?.data ?? null
  const packageHistory = packageHistoryEnvelope?.data ?? []

  for (const link of links) {
    assertProject(projectId, link, "Evidence Link")
    if (link.claim_id !== selectedClaim?.id)
      noDisclosure("The Link list contains an unrelated resource.")
  }
  if (selectedLink && !links.some((link) => link.id === selectedLink.id))
    noDisclosure(
      "The selected Link is not visible in the selected Claim scope.",
    )
  if (approval) {
    assertProject(projectId, approval, "Approval")
    if (approval.target_object_id !== exportValue?.id)
      noDisclosure("The Approval target does not match the selected Export.")
  }
  if (job) {
    assertProject(projectId, job, "Job")
    if (job.resource_id !== exportValue?.id)
      noDisclosure("The Job target does not match the selected Export.")
  }
  if (auditJob) {
    assertProject(projectId, auditJob, "Audit Job")
    if (
      auditJob.resource_type !== "audit_result" ||
      auditJob.resource_id !== audit?.id ||
      auditJob.task_type !== "EVIDENCE_AUDIT"
    )
      noDisclosure("The Audit Job target does not match the selected Audit.")
  }
  for (const historyItem of packageHistory) {
    assertProject(projectId, historyItem, "ReproPackage history item")
  }
  return mapEvidenceWorkspace({
    projectId,
    project,
    graph,
    selectedClaim,
    links,
    selectedLink,
    selectedNodeId: selection.node,
    audit,
    auditJob,
    readiness: null,
    export: exportValue,
    approval,
    job,
    package: packageValue,
    packageHistory,
    packageHistoryPage: packageHistoryEnvelope?.pagination.page ?? 1,
    packageHistoryHasNext: packageHistoryEnvelope?.pagination.has_next ?? false,
  })
}

export async function loadEvidenceWorkspace(
  projectId: string,
  selection: EvidenceWorkspaceSelection,
) {
  try {
    return await loadSelectedEvidenceWorkspace(projectId, selection)
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 404 &&
      Object.values(selection).some(Boolean)
    ) {
      const fallback = await loadSelectedEvidenceWorkspace(projectId, {})
      return { ...fallback, routeFallback: true }
    }
    throw error
  }
}

export function useEvidenceWorkspaceQuery(
  projectId: string,
  selection: EvidenceWorkspaceSelection,
) {
  return useQuery({
    queryKey: evidenceWorkspaceKeys.workspace(projectId, selection),
    queryFn: () => loadEvidenceWorkspace(projectId, selection),
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}
