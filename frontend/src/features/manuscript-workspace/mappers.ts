import type {
  ApprovalPublic,
  ClaimPublic,
  JobPublic,
  ManuscriptCheckRunPublic,
  ManuscriptIssuePublic,
  ManuscriptPublic,
  ManuscriptTransformationPublic,
  ManuscriptVersionPublic,
  RevisionAuditPublic,
} from "@/api/adapter"

import type {
  ActionCapability,
  CheckRunViewModel,
  ClaimViewModel,
  IssueViewModel,
  JobViewModel,
  ManuscriptVersionViewModel,
  ManuscriptViewModel,
  ManuscriptWorkspaceViewModel,
  RevisionAuditViewModel,
  TransformationViewModel,
} from "./model"

const CHECK_DEFINITIONS = [
  ["CITATION", "Citations and references"],
  ["NUMERIC_CONSISTENCY", "Numeric consistency"],
  ["CAUSALITY", "Causal language"],
  ["TERMINOLOGY", "Terminology"],
  ["BASIC_FORMAT", "Basic format"],
] as const

const CLAIM_TYPES = [
  ["LITERATURE_SUMMARY", "Literature summary"],
  ["CONSENSUS", "Consensus"],
  ["CONTROVERSY", "Controversy"],
  ["EVIDENCE_GAP", "Evidence gap"],
  ["TOPIC_RATIONALE", "Topic rationale"],
  ["DATA_DESCRIPTION", "Data description"],
  ["STATISTICAL_RESULT", "Statistical result"],
  ["INTERPRETATION", "Interpretation"],
  ["MANUSCRIPT_STATEMENT", "Manuscript statement"],
] as const

const CLAIM_TRANSITIONS: Readonly<Record<string, readonly string[]>> = {
  DRAFT: ["NEEDS_EVIDENCE", "REJECTED"],
  NEEDS_EVIDENCE: ["SUPPORTED", "CONFLICTED", "INSUFFICIENT", "REJECTED"],
  SUPPORTED: ["NEEDS_EVIDENCE", "CONFLICTED", "INSUFFICIENT", "REJECTED"],
  CONFLICTED: ["NEEDS_EVIDENCE", "SUPPORTED", "INSUFFICIENT", "REJECTED"],
  INSUFFICIENT: ["NEEDS_EVIDENCE", "SUPPORTED", "CONFLICTED", "REJECTED"],
}

const KNOWN = {
  manuscript: new Set(["ACTIVE", "ARCHIVED", "INVALIDATED"]),
  version: new Set(["UPLOADED", "AVAILABLE", "FAILED", "INVALIDATED"]),
  check: new Set([
    "UPLOADED",
    "QUEUED",
    "PARSING",
    "CHECKING_RULES",
    "CHECKING_PROJECT_CONSISTENCY",
    "NEEDS_REVIEW",
    "COMPLETED",
    "FAILED",
    "LOW_CONFIDENCE",
    "CANCELLED",
  ]),
  issue: new Set([
    "OPEN",
    "ACKNOWLEDGED",
    "ACCEPTED",
    "REJECTED",
    "RESOLVED",
    "INVALIDATED",
  ]),
  transformation: new Set([
    "DRAFT",
    "NEEDS_APPROVAL",
    "APPROVED",
    "REJECTED",
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "INVALIDATED",
  ]),
  audit: new Set(["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]),
  claim: new Set([
    "DRAFT",
    "NEEDS_EVIDENCE",
    "SUPPORTED",
    "CONFLICTED",
    "INSUFFICIENT",
    "CONFIRMED",
    "REJECTED",
    "INVALIDATED",
  ]),
  approval: new Set([
    "PENDING",
    "APPROVED",
    "REJECTED",
    "CANCELLED",
    "SUPERSEDED",
    "EXPIRED",
  ]),
  job: new Set([
    "DRAFT",
    "QUEUED",
    "RUNNING",
    "NEEDS_REVIEW",
    "COMPLETED",
    "FAILED",
    "CANCEL_REQUESTED",
    "CANCELLED",
    "DISPATCH_FAILED",
  ]),
}

const actions = (value: readonly string[] | undefined) => new Set(value ?? [])
const record = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null
const strings = (value: unknown) =>
  Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : []

export function mapManuscript(value: ManuscriptPublic): ManuscriptViewModel {
  const knownStatus = KNOWN.manuscript.has(value.status)
  return {
    id: value.id,
    projectId: value.project_id,
    title: value.title ?? "Untitled manuscript",
    currentVersionId: value.current_version_id,
    status: value.status,
    knownStatus,
    lockVersion: value.lock_version,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

export function mapVersion(
  value: ManuscriptVersionPublic,
): ManuscriptVersionViewModel {
  const snapshot = record(value.parse_snapshot)
  const knownStatus = KNOWN.version.has(value.status)
  return {
    id: value.id,
    manuscriptId: value.manuscript_id,
    projectId: value.project_id,
    versionNumber: value.version_number,
    parentVersionId: value.parent_version_id,
    artifactId: value.artifact_id,
    versionType: value.version_type,
    sourceTransformationId: value.source_transformation_id,
    status: value.status,
    knownStatus,
    sourceHash: value.source_hash,
    parseConfidence:
      typeof snapshot?.confidence === "string" ? snapshot.confidence : null,
    unsupportedFeatures: strings(snapshot?.unsupported_features),
    invalidationReason: value.invalidation_reason,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

export function mapJob(value: JobPublic): JobViewModel {
  return {
    id: value.id,
    projectId: value.project_id,
    resourceType: value.resource_type,
    resourceId: value.resource_id,
    status: value.status,
    knownStatus: KNOWN.job.has(value.status),
    progress: value.progress_percent,
    retryable: value.retryable,
    errorCode: value.error?.code ?? null,
  }
}

export function mapCheckRun(
  value: ManuscriptCheckRunPublic,
): CheckRunViewModel {
  const knownStatus = KNOWN.check.has(value.status)
  return {
    id: value.id,
    projectId: value.project_id,
    versionId: value.manuscript_version_id,
    jobId: value.job_id,
    sourceHash: value.source_hash,
    status: value.status,
    knownStatus,
    issueCount: value.issue_count,
    highIssueCount: value.high_issue_count,
    degradation: record(value.degradation),
    lowConfidence: value.status === "LOW_CONFIDENCE",
    errorCode: value.error_code,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

export function mapIssue(value: ManuscriptIssuePublic): IssueViewModel {
  const knownStatus = KNOWN.issue.has(value.status)
  return {
    id: value.id,
    projectId: value.project_id,
    checkRunId: value.manuscript_check_run_id,
    versionId: value.manuscript_version_id,
    issueType: value.issue_type,
    severity: value.severity,
    locator: value.locator,
    excerpt: value.original_text,
    reason: value.reason,
    suggestion: value.suggestion,
    findingHash: value.finding_hash,
    confidence: value.confidence,
    deterministic: value.source_model_invocation_id === null,
    highRisk: value.severity === "HIGH" || value.severity === "MEDIUM",
    autoFixable:
      knownStatus &&
      value.auto_fixable &&
      ["LOW", "INFO"].includes(value.severity),
    status: value.status,
    knownStatus,
    lockVersion: value.lock_version,
    evidence: (value.evidence ?? []).map((item) => ({
      id: item.id,
      type: item.evidence_type,
      objectType: item.evidence_object_type,
      objectId: item.evidence_object_id,
      excerpt: item.evidence_text,
      hash: item.evidence_hash,
      metadata: record(item.evidence_metadata),
      readScope: "AVAILABLE" as const,
    })),
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

function mapApproval(
  approval: ApprovalPublic | null,
  expectedTargetId: string,
) {
  const status = approval?.status ?? null
  const known = status === null || KNOWN.approval.has(status)
  const stale =
    approval !== null &&
    (approval.target_object_id !== expectedTargetId ||
      approval.status === "SUPERSEDED" ||
      approval.status === "EXPIRED")
  return { status, known, stale }
}

export function mapTransformation(
  value: ManuscriptTransformationPublic,
  approval: ApprovalPublic | null,
): TransformationViewModel {
  const approvalFact = mapApproval(approval, value.id)
  const knownStatus = KNOWN.transformation.has(value.status)
  return {
    id: value.id,
    projectId: value.project_id,
    inputVersionId: value.manuscript_version_id,
    issueIds: value.approved_issue_ids,
    inputArtifactHash: value.input_artifact_hash,
    preview: record(value.preview),
    previewHash: value.preview_hash,
    approvalId: value.approval_record_id,
    approvalStatus: approvalFact.status,
    approvalKnown: approvalFact.known,
    approvalStale: approvalFact.stale,
    outputVersionId: value.output_manuscript_version_id,
    payloadHash: value.payload_hash,
    lockVersion: value.lock_version,
    jobId: value.job_id,
    errorCode: value.error_code,
    status: value.status,
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

const findingCodes = new Set([
  "CLAIM_NUMERIC_MISMATCH",
  "CITATION_REMOVED",
  "CITATION_ADDED",
  "CLAIM_CAUSAL_OVERSTATEMENT",
  "CLAIM_SCOPE_EXPANDED",
  "CLAIM_FIGURE_VERSION_MISMATCH",
  "CLAIM_STALE_AFTER_REVISION",
  "POTENTIAL_CLAIM_UNLOCATED",
])

export function mapRevisionAudit(
  value: RevisionAuditPublic,
): RevisionAuditViewModel {
  const result = record(value.result)
  const knownStatus = KNOWN.audit.has(value.status)
  const rawFindings = Array.isArray(result?.findings) ? result.findings : []
  return {
    id: value.id,
    projectId: value.project_id,
    manuscriptId: value.manuscript_id,
    beforeVersionId: value.before_version_id,
    afterVersionId: value.after_version_id,
    beforeSourceHash: value.before_source_hash,
    afterSourceHash: value.after_source_hash,
    resultHash: value.result_hash,
    findings: rawFindings.map((raw) => {
      const detail = record(raw) ?? {}
      const code = typeof detail.code === "string" ? detail.code : "UNKNOWN"
      return {
        code,
        knownCode: findingCodes.has(code),
        severity: "UNKNOWN" as const,
        locator: record(detail.locator),
        detail,
      }
    }),
    limitations: strings(result?.limitations),
    jobId: value.job_id,
    errorCode: value.error_code,
    status: value.status,
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

export function mapClaim(
  value: ClaimPublic,
  approval: ApprovalPublic | null,
): ClaimViewModel {
  const approvalFact = mapApproval(approval, value.id)
  const knownStatus = KNOWN.claim.has(value.status)
  return {
    id: value.id,
    projectId: value.project_id,
    claimType: value.claim_type,
    text: value.claim_text,
    normalizedClaim: value.normalized_claim,
    scopeStatement: value.scope_statement,
    sourceObjectType: value.source_object_type,
    sourceObjectId: value.source_object_id,
    sourceLocation: value.source_location,
    sourceHash: value.source_hash,
    textHash: value.text_hash,
    status: value.status,
    knownStatus,
    confidence: value.confidence,
    approvalId: value.approval_record_id,
    approvalStatus: approvalFact.status,
    approvalKnown: approvalFact.known,
    approvalStale: approvalFact.stale,
    lockVersion: value.lock_version,
    readOnly:
      !knownStatus ||
      ["CONFIRMED", "REJECTED", "INVALIDATED"].includes(value.status),
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

const capability = (allowed: boolean, reason: string): ActionCapability => ({
  allowed,
  disabledReason: allowed ? null : reason,
})

export type WorkspaceMapperInput = {
  projectId: string
  permissionsKnown: boolean
  discoveryState: string
  projectAllowedActions: readonly string[]
  manuscript: ManuscriptPublic | null
  versions: readonly ManuscriptVersionPublic[]
  selectedVersion: ManuscriptVersionPublic | null
  checkRun: ManuscriptCheckRunPublic | null
  issues: readonly ManuscriptIssuePublic[]
  selectedIssue: ManuscriptIssuePublic | null
  transformation: ManuscriptTransformationPublic | null
  revisionAudit: RevisionAuditPublic | null
  claim: ClaimPublic | null
  approval: ApprovalPublic | null
  job: JobPublic | null
}

export function mapManuscriptWorkspace(
  input: WorkspaceMapperInput,
): ManuscriptWorkspaceViewModel {
  const discoveryKnown = ["NONE", "ACTIVE", "ARCHIVED", "INVALIDATED"].includes(
    input.discoveryState,
  )
  const manuscript = input.manuscript ? mapManuscript(input.manuscript) : null
  const versions = input.versions.map(mapVersion)
  const selectedVersion = input.selectedVersion
    ? mapVersion(input.selectedVersion)
    : null
  const checkRun = input.checkRun ? mapCheckRun(input.checkRun) : null
  const issues = input.issues.map(mapIssue)
  const selectedIssue = input.selectedIssue
    ? mapIssue(input.selectedIssue)
    : null
  const transformation = input.transformation
    ? mapTransformation(input.transformation, input.approval)
    : null
  const revisionAudit = input.revisionAudit
    ? mapRevisionAudit(input.revisionAudit)
    : null
  const claim = input.claim ? mapClaim(input.claim, input.approval) : null
  const job = input.job ? mapJob(input.job) : null
  const projectActions = actions(input.projectAllowedActions)
  const known = input.permissionsKnown
  const factsKnown = known && discoveryKnown
  const can = (
    value: boolean,
    reason = "Not allowed by current server facts",
  ) =>
    capability(
      factsKnown && value,
      !known
        ? "Permissions are unknown"
        : !discoveryKnown
          ? "Manuscript discovery state is unknown"
          : reason,
    )
  return {
    projectId: input.projectId,
    permissionsKnown: known,
    discoveryState: input.discoveryState,
    discoveryKnown,
    manuscript,
    versions,
    selectedVersion,
    checkRun,
    issues,
    selectedIssue,
    transformation,
    revisionAudit,
    claim,
    job,
    checkDefinitions: CHECK_DEFINITIONS.map(([value, label]) => ({
      value,
      label,
      allowed: Boolean(
        known &&
          selectedVersion?.knownStatus &&
          selectedVersion.allowedActions.has("manuscript_version.check"),
      ),
      disabledReason: !known
        ? "Permissions are unknown"
        : selectedVersion?.knownStatus &&
            selectedVersion.allowedActions.has("manuscript_version.check")
          ? null
          : "The selected version cannot run checks",
    })),
    revisionReferences: versions.map((version) => ({
      value: version.id,
      label: `Version ${version.versionNumber}`,
      sourceHash: version.sourceHash,
      versionNumber: version.versionNumber,
      allowed: Boolean(
        known && version.knownStatus && version.status === "AVAILABLE",
      ),
      disabledReason: !known
        ? "Permissions are unknown"
        : version.knownStatus && version.status === "AVAILABLE"
          ? null
          : "This version is unavailable for revision audit",
    })),
    claimTypeDefinitions: CLAIM_TYPES.map(([value, label]) => ({
      value,
      label,
      allowed: Boolean(known && projectActions.has("claim.create")),
      disabledReason: !known
        ? "Permissions are unknown"
        : projectActions.has("claim.create")
          ? null
          : "Claim creation is not allowed",
    })),
    claimStatusTransitions: (claim && claim.knownStatus
      ? (CLAIM_TRANSITIONS[claim.status] ?? [])
      : []
    ).map((value) => ({
      value,
      label: value.replace(/_/g, " ").toLowerCase(),
      allowed: Boolean(known && claim?.allowedActions.has("claim.update")),
      disabledReason: !known
        ? "Permissions are unknown"
        : claim?.allowedActions.has("claim.update")
          ? null
          : "Claim status cannot be changed",
    })),
    degraded:
      !discoveryKnown ||
      Boolean(checkRun?.degradation) ||
      [
        manuscript,
        selectedVersion,
        checkRun,
        transformation,
        revisionAudit,
        claim,
      ].some((item) => item !== null && !item.knownStatus),
    capabilities: {
      permissionsKnown: known,
      uploadManuscript: can(projectActions.has("manuscript.upload")),
      startCheck: can(
        Boolean(
          selectedVersion?.knownStatus &&
            selectedVersion.allowedActions.has("manuscript_version.check"),
        ),
      ),
      retryJob: can(
        Boolean(job?.knownStatus && job.retryable && job.status === "FAILED"),
      ),
      cancelJob: can(
        Boolean(job?.knownStatus && ["QUEUED", "RUNNING"].includes(job.status)),
      ),
      acceptIssue: can(
        Boolean(
          selectedIssue?.knownStatus &&
            selectedIssue.allowedActions.has("manuscript_issue.accept"),
        ),
      ),
      rejectIssue: can(
        Boolean(
          selectedIssue?.knownStatus &&
            selectedIssue.allowedActions.has("manuscript_issue.reject"),
        ),
      ),
      createFixPlan: can(
        issues.some(
          (issue) =>
            issue.knownStatus &&
            issue.status === "ACCEPTED" &&
            issue.autoFixable,
        ),
      ),
      previewFixPlan: can(
        Boolean(
          transformation?.knownStatus &&
            transformation.allowedActions.has("manuscript_fix_plan.preview"),
        ),
      ),
      requestFixApproval: can(
        Boolean(
          transformation?.knownStatus &&
            transformation.allowedActions.has(
              "manuscript_fix_plan.request_approval",
            ) &&
            transformation.previewHash,
        ),
      ),
      executeFixPlan: can(
        Boolean(
          transformation?.knownStatus &&
            transformation.approvalKnown &&
            !transformation.approvalStale &&
            transformation.approvalStatus === "APPROVED" &&
            transformation.allowedActions.has("manuscript_fix_plan.execute"),
        ),
      ),
      startRevisionAudit: can(
        projectActions.has("manuscript.audit") && versions.length >= 2,
      ),
      createClaim: can(projectActions.has("claim.create")),
      updateClaim: can(
        Boolean(
          claim?.knownStatus &&
            !claim.readOnly &&
            claim.allowedActions.has("claim.update"),
        ),
      ),
      requestClaimConfirmation: can(
        Boolean(
          claim?.knownStatus &&
            claim.status === "SUPPORTED" &&
            claim.allowedActions.has("claim.request_confirmation"),
        ),
      ),
      downloadVersion: can(
        Boolean(
          selectedVersion?.knownStatus &&
            selectedVersion.allowedActions.has("manuscript_version.download"),
        ),
      ),
    },
  }
}
