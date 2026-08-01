import {
  ApiError,
  type ApprovalPublic,
  type ArtifactPublic,
  type AuditListEnvelope,
  type JobPublic,
  type ProjectMemberPublic,
  type ProjectOverviewPublic,
  type ProjectPublic,
} from "@/api/adapter"

import type {
  ApprovalViewModel,
  ArtifactViewModel,
  AuditViewModel,
  CapabilityViewModel,
  JobViewModel,
  MemberViewModel,
  OverviewViewModel,
  ProjectListItemViewModel,
  ProjectViewModel,
  SemanticTone,
  UiErrorViewModel,
  WorkspacePermissions,
} from "./model"

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
})

export function formatDate(value: string | null): string {
  if (!value) return "Not recorded"
  const date = new Date(value)
  return Number.isNaN(date.valueOf())
    ? "Invalid date"
    : dateFormatter.format(date)
}

export function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 ** 2).toFixed(1)} MB`
}

export function mapUiError(error: unknown): UiErrorViewModel {
  if (error instanceof ApiError) {
    return {
      title: error.status === 403 ? "Access denied" : "Request failed",
      message: error.message,
      code: error.code,
      requestId: error.requestId,
      retryable: error.retryable,
      forbidden: error.status === 403,
      notFound: error.status === 404,
      conflict: error.status === 409,
    }
  }
  return {
    title: "Connection problem",
    message: "The workspace could not be loaded.",
    code: "NETWORK_ERROR",
    requestId: null,
    retryable: true,
    forbidden: false,
    notFound: false,
    conflict: false,
  }
}

export function mapProjectListItem(
  project: ProjectPublic,
): ProjectListItemViewModel {
  return {
    id: project.id,
    name: project.name,
    description: project.description,
    stage: project.current_stage,
    status: project.status,
    type: project.project_type,
    updatedAt: formatDate(project.updated_at),
    canUpdate: project.permissions.can_update,
  }
}

export function mapProject(project: ProjectPublic): ProjectViewModel {
  return {
    ...mapProjectListItem(project),
    ownerId: project.owner_id,
    discipline: project.discipline,
    researchDirection: project.research_direction,
    lockVersion: project.lock_version,
    canDelete: project.permissions.can_delete,
  }
}

const capabilityLabels: Readonly<Record<string, string>> = {
  research_question: "Research question",
  literature: "Literature",
  dataset: "Dataset",
  analysis: "Analysis",
  figure: "Figures",
  manuscript: "Manuscript",
  evidence: "Evidence",
}

const capabilityCounts: Readonly<Record<string, string>> = {
  literature: "literature_total",
  dataset: "datasets",
  analysis: "analysis_runs",
  figure: "figures",
  manuscript: "manuscript_issues",
}

function capabilityTone(value: string): SemanticTone {
  if (value === "AVAILABLE") return "success"
  if (value === "DEGRADED") return "degraded"
  return "neutral"
}

export function mapOverview(
  overview: ProjectOverviewPublic,
): OverviewViewModel {
  const capabilities: CapabilityViewModel[] = Object.entries(
    overview.module_availability,
  ).map(([key, availability]) => {
    const normalized =
      availability === "AVAILABLE" || availability === "DEGRADED"
        ? availability
        : "NOT_AVAILABLE"
    const countKey = capabilityCounts[key]
    return {
      key,
      label: capabilityLabels[key] ?? key.replace(/_/g, " "),
      availability: normalized,
      value:
        normalized === "AVAILABLE" && countKey
          ? overview.counts[countKey]
          : null,
      tone: capabilityTone(normalized),
    }
  })
  return {
    stage: overview.current_stage,
    foundationCounts: [
      { label: "Members", value: overview.foundation_counts.members },
      {
        label: "Artifacts",
        value: overview.foundation_counts.artifacts ?? null,
      },
      {
        label: "Active jobs",
        value: overview.foundation_counts.jobs_active ?? null,
      },
      {
        label: "Pending approvals",
        value: overview.foundation_counts.approvals_pending ?? null,
      },
      { label: "Audit events", value: overview.foundation_counts.audit_events },
    ],
    capabilities,
    researchQuestion: null,
    evidenceCompleteness: null,
    pendingActionCount: overview.pending_actions.length,
  }
}

export function mapMembers(
  members: ProjectMemberPublic[],
  currentUserId: string | undefined,
): { members: MemberViewModel[]; permissions: WorkspacePermissions } {
  const current = members.find((member) => member.user.id === currentUserId)
  const actions = new Set(current?.allowed_actions ?? [])
  return {
    members: members.map((member) => ({
      id: member.id,
      userId: member.user.id,
      displayName: member.user.full_name || member.user.email,
      email: member.user.email,
      role: member.role,
      joinedAt: formatDate(member.joined_at),
      removed: member.removed_at !== null,
      isCurrentUser: member.user.id === currentUserId,
      isOwner: member.role === "OWNER" && member.removed_at === null,
    })),
    permissions: {
      actions,
      canManageMembers: actions.has("project.manage_members"),
      canUploadArtifact: actions.has("artifact.upload"),
      canRetryJob: actions.has("job.retry"),
      canCancelJob: actions.has("job.cancel"),
    },
  }
}

export function mapArtifact(artifact: ArtifactPublic): ArtifactViewModel {
  return {
    id: artifact.id,
    filename: artifact.original_filename || artifact.filename,
    kind: artifact.artifact_type,
    origin: artifact.is_original ? "ORIGINAL" : "DERIVED",
    status: artifact.status,
    size: formatBytes(artifact.size_bytes),
    sha256: artifact.sha256,
    createdAt: formatDate(artifact.created_at),
    canDownload: artifact.allowed_actions.includes("artifact.download"),
    immutable: artifact.is_immutable,
  }
}

function jobTone(status: string): SemanticTone {
  if (status === "COMPLETED") return "success"
  if (["FAILED", "DISPATCH_FAILED"].includes(status)) return "danger"
  if (["CANCEL_REQUESTED", "NEEDS_REVIEW"].includes(status)) return "warning"
  if (["QUEUED", "RUNNING"].includes(status)) return "info"
  return "neutral"
}

export function mapJob(job: JobPublic): JobViewModel {
  return {
    id: job.id,
    taskLabel: job.task_type.replace(/_/g, " "),
    status: job.status,
    progress: job.progress_percent,
    step: job.current_step,
    retryable: job.retryable,
    retryCount: job.retry_count,
    maxRetries: job.max_retries,
    error: job.error ? `${job.error.code}: ${job.error.message}` : null,
    resultUrl: job.result?.url ?? null,
    createdAt: formatDate(job.created_at),
    active: ["DRAFT", "QUEUED", "RUNNING", "CANCEL_REQUESTED"].includes(
      job.status,
    ),
    tone: jobTone(job.status),
  }
}

function approvalTone(status: string): SemanticTone {
  if (status === "APPROVED") return "success"
  if (["REJECTED", "CANCELLED"].includes(status)) return "danger"
  if (["EXPIRED", "SUPERSEDED"].includes(status)) return "warning"
  return "info"
}

export function mapApproval(approval: ApprovalPublic): ApprovalViewModel {
  return {
    id: approval.id,
    type: approval.approval_type.replace(/_/g, " "),
    target: `${approval.target_object_type} · ${approval.target_object_id}`,
    status: approval.status,
    requester: approval.requester.id
      ? `${approval.requester.type} · ${approval.requester.id}`
      : approval.requester.type,
    requestedAt: formatDate(approval.requested_at),
    expiresAt: approval.expires_at ? formatDate(approval.expires_at) : null,
    payloadHash: approval.payload_hash,
    allowedActions: new Set(approval.allowed_actions),
    stale: ["EXPIRED", "SUPERSEDED"].includes(approval.status),
    tone: approvalTone(approval.status),
  }
}

function auditTone(outcome: string): SemanticTone {
  if (outcome === "SUCCEEDED") return "success"
  if (outcome === "DENIED") return "warning"
  return "danger"
}

export function mapAuditList(envelope: AuditListEnvelope): AuditViewModel[] {
  return envelope.data.map((audit) => ({
    id: audit.id,
    actor: audit.actor.display_name || audit.actor.id || audit.actor.type,
    action: audit.action.replace(/_/g, " "),
    target: audit.target.label || audit.target.type,
    occurredAt: formatDate(audit.created_at),
    requestId: audit.request_id,
    outcome: audit.outcome,
    summary: audit.reason,
    tone: auditTone(audit.outcome),
  }))
}
