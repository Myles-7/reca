import type {
  ApprovalPublic,
  ClaimAuditPublic,
  ClaimEvidenceLinkPublic,
  ClaimPublic,
  EvidenceCompleteness,
  EvidenceGraphProjection,
  ExportPublic,
  ExportReadiness,
  GraphEdge,
  GraphNode,
  JobPublic,
  ProjectPublic,
  ReproPackageHistoryItem,
  ReproPackagePublic,
} from "@/api/adapter"

import type {
  ActionCapability,
  ApprovalViewModel,
  ClaimAuditViewModel,
  ClaimCompletenessViewModel,
  ClaimSummaryViewModel,
  ClaimViewModel,
  EdgeSemantic,
  EvidenceGraphEdgeViewModel,
  EvidenceGraphNodeViewModel,
  EvidenceLinkViewModel,
  EvidenceReferenceViewModel,
  EvidenceRisk,
  EvidenceScope,
  EvidenceScopeNotice,
  EvidenceWorkspaceViewModel,
  ExportCandidateViewModel,
  ExportReadinessViewModel,
  ExportViewModel,
  GraphCanvasEdge,
  GraphCanvasNode,
  JobViewModel,
  ManifestFileViewModel,
  ManifestViewModel,
  ReproPackageHistoryItemViewModel,
  ReproPackageViewModel,
} from "./model"

const KNOWN = {
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
  link: new Set(["SUGGESTED", "ACTIVE", "REJECTED", "INVALIDATED"]),
  completeness: new Set([
    "SATISFIED",
    "MISSING",
    "STALE",
    "RESTRICTED",
    "CONFLICTED",
    "NOT_APPLICABLE",
    "UNKNOWN",
  ]),
  auditExecution: new Set([
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
  ]),
  auditOutcome: new Set([
    "VERIFIED",
    "NEEDS_REVIEW",
    "INSUFFICIENT_EVIDENCE",
    "SOURCE_INCOMPLETE",
    "CONFLICTED",
    "DATA_MISMATCH",
    "FIGURE_MISMATCH",
    "OVERCLAIM_RISK",
    "REJECTED_BY_USER",
    "INVALIDATED",
  ]),
  export: new Set([
    "DRAFT",
    "VALIDATING",
    "NEEDS_CONFIRMATION",
    "QUEUED",
    "PACKAGING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
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
  include: new Set([
    "INCLUDED",
    "EXCLUDED",
    "METADATA_ONLY",
    "REFERENCE_ONLY",
    "BLOCKED",
    "MISSING",
  ]),
}

const actions = (value: unknown): ReadonlySet<string> =>
  new Set(
    Array.isArray(value)
      ? value.filter((item): item is string => typeof item === "string")
      : [],
  )
const stringValue = (value: unknown, fallback = "UNKNOWN") =>
  typeof value === "string" ? value : fallback
const objectValue = (value: unknown): Record<string, unknown> | null =>
  value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null
const strings = (value: unknown) =>
  Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : []
const records = (value: unknown) =>
  Array.isArray(value)
    ? value.filter(
        (item): item is Record<string, unknown> => objectValue(item) !== null,
      )
    : []

function sourceKind(value: unknown) {
  return value === "DOMAIN" || value === "STORED" || value === "DERIVED"
    ? value
    : "UNKNOWN"
}

function risk(value: unknown): EvidenceRisk {
  return value === "LOW" ||
    value === "MEDIUM" ||
    value === "HIGH" ||
    value === "UNKNOWN"
    ? value
    : "UNKNOWN"
}

function evidenceScope(value: {
  knownStatus: boolean
  stale: boolean
  invalidated: boolean
}): EvidenceScope {
  if (!value.knownStatus) return "UNKNOWN"
  if (value.stale || value.invalidated) return "STALE"
  return "AVAILABLE"
}

function edgeSemantic(
  relationType: string,
  strength: string | null,
  kind: string,
): EdgeSemantic {
  if (kind === "DERIVED") return "PROVENANCE"
  if (relationType === "CONTRADICTED_BY") return "CONTRADICT"
  if (relationType === "SUPPORTED_BY")
    return strength === "WEAK" ? "QUALIFY" : "SUPPORT"
  if (
    [
      "DERIVED_FROM",
      "TRANSFORMED_FROM",
      "ANALYZED_BY",
      "PRODUCED_BY",
      "VISUALIZED_AS",
      "CONFIRMED_BY",
      "AUDITED_BY",
      "INVALIDATED_BY",
    ].includes(relationType)
  )
    return "PROVENANCE"
  return "UNKNOWN"
}

export function mapGraphNode(value: GraphNode): EvidenceGraphNodeViewModel {
  const status = stringValue(value.raw_status)
  const knownStatus = value.known_status === true
  const invalidated = value.invalidated === true
  const stale = value.stale === true
  return {
    id: value.id,
    nodeType: stringValue(value.node_type),
    objectId: value.object_id,
    label: value.label,
    status,
    knownStatus,
    risk: risk(value.risk),
    scope: evidenceScope({ knownStatus, stale, invalidated }),
    invalidated,
    stale,
    sourceKind: sourceKind(value.source_kind),
    detailIntent: value.detail_intent,
    limitations: [...value.limitations],
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
    lane: value.lane ?? null,
    rank: value.rank ?? null,
  }
}

export function mapGraphEdge(value: GraphEdge): EvidenceGraphEdgeViewModel {
  const relationType = stringValue(value.relation_type)
  const strength = value.strength ? stringValue(value.strength) : null
  const kind = sourceKind(value.source_kind)
  return {
    id: value.id,
    source: value.source,
    target: value.target,
    relationType,
    strength,
    semantic: edgeSemantic(relationType, strength, kind),
    status: stringValue(value.raw_status),
    knownStatus: value.known_status === true,
    risk: risk(value.risk),
    invalidated: value.invalidated === true,
    sourceKind: kind === "DOMAIN" ? "UNKNOWN" : kind,
  }
}

export function mapGraphCanvas(
  nodes: readonly EvidenceGraphNodeViewModel[],
  edges: readonly EvidenceGraphEdgeViewModel[],
): { nodes: GraphCanvasNode[]; edges: GraphCanvasEdge[] } {
  const lanes = [
    ...new Set(nodes.map((node) => node.lane ?? node.nodeType)),
  ].sort()
  const counters = new Map<string, number>()
  return {
    nodes: nodes.map((node) => {
      const lane = node.lane ?? node.nodeType
      const key = `${lane}:${node.rank ?? 0}`
      const offset = counters.get(key) ?? 0
      counters.set(key, offset + 1)
      return {
        id: node.id,
        position: {
          x: (node.rank ?? 0) * 280,
          y: lanes.indexOf(lane) * 132 + offset * 84,
        },
        data: node,
        selectable: true,
        draggable: true,
        connectable: false,
      }
    }),
    edges: edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      data: edge,
      selectable: true,
      reconnectable: false,
    })),
  }
}

export function mapClaim(value: ClaimPublic): ClaimViewModel {
  const status = stringValue(value.status)
  const knownStatus = KNOWN.claim.has(status)
  return {
    id: value.id,
    projectId: value.project_id,
    claimType: stringValue(value.claim_type),
    text: value.claim_text,
    sourceObjectType: value.source_object_type,
    sourceObjectId: value.source_object_id,
    sourceHash: value.source_hash,
    textHash: value.text_hash,
    lockVersion: value.lock_version,
    stale: status === "INVALIDATED",
    status,
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

function mapReference(
  value: ClaimEvidenceLinkPublic["evidence"],
): EvidenceReferenceViewModel {
  const status = stringValue(value.raw_status)
  const knownStatus = value.known_status === true
  const stale = value.stale === true
  const invalidated = value.invalidated === true
  return {
    objectType: stringValue(value.object_type),
    objectId: value.object_id,
    projectId: value.project_id,
    label: value.label,
    sourceHash: value.source_hash,
    detailIntent: value.detail_intent,
    scope: value.restricted
      ? ("DENIED" as const)
      : evidenceScope({
          knownStatus,
          stale,
          invalidated,
        }),
    stale,
    invalidated,
    limitations: [...(value.limitations ?? [])],
    status,
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

export function mapLink(value: ClaimEvidenceLinkPublic): EvidenceLinkViewModel {
  const status = stringValue(value.status)
  const knownStatus = KNOWN.link.has(status)
  const relationType = stringValue(value.relation_type)
  const strength = stringValue(value.strength)
  return {
    id: value.id,
    projectId: value.project_id,
    claimId: value.claim_id,
    relationType,
    semantic: edgeSemantic(relationType, strength, "STORED"),
    strength,
    explanation: value.explanation,
    lockVersion: value.lock_version,
    stale: status === "INVALIDATED" || value.evidence.stale === true,
    invalidated:
      status === "INVALIDATED" || value.evidence.invalidated === true,
    evidence: mapReference(value.evidence),
    status,
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

function mapCompleteness(
  value: EvidenceCompleteness,
): ClaimCompletenessViewModel {
  return {
    claimId: value.claim_id,
    ruleSetVersion: value.rule_set_version,
    items: value.items.map((item) => {
      const status = stringValue(item.status)
      return {
        code: item.code,
        status,
        knownStatus: KNOWN.completeness.has(status),
        sourceObjectIds: [...(item.source_object_ids ?? [])],
        limitations: [...(item.limitations ?? [])],
        missingActions: [...(item.missing_actions ?? [])],
        scientificQualityScore: null,
      }
    }),
    limitations: [...(value.limitations ?? [])],
    isScientificQualityScore: false,
  }
}

export function mapAudit(value: ClaimAuditPublic): ClaimAuditViewModel {
  const status = stringValue(value.execution_status)
  const outcome = value.outcome ? stringValue(value.outcome) : null
  return {
    id: value.id,
    projectId: value.project_id,
    auditType: stringValue(value.audit_type),
    targetObjectType: value.target_object_type,
    targetObjectId: value.target_object_id,
    jobId: value.job_id,
    status,
    knownStatus: KNOWN.auditExecution.has(status),
    outcome,
    outcomeKnown: outcome === null || KNOWN.auditOutcome.has(outcome),
    sourceSnapshotHash: value.source_snapshot_hash,
    resultHash: value.result_hash,
    findings: value.findings.map((item) => ({ ...item })),
    limitations: [...value.limitations],
    degraded: value.degraded,
    ruleSetVersion: value.rule_set_version,
    allowedActions: actions(value.allowed_actions),
  }
}

function mapCandidate(
  value: ExportReadiness["candidate_items"][number],
): ExportCandidateViewModel {
  const status = stringValue(value.include_status)
  return {
    objectType: value.object_type,
    objectId: value.object_id,
    artifactId: value.artifact_id,
    packagePath: value.package_path,
    sha256: value.sha256,
    exclusionReason: value.exclusion_reason ?? null,
    licenseStatus: value.license_status,
    sensitive: value.sensitive,
    redistribution: value.redistribution,
    status,
    knownStatus: KNOWN.include.has(status),
  }
}

export function mapReadiness(value: ExportReadiness): ExportReadinessViewModel {
  return {
    auditId: value.audit_id,
    ready: value.ready,
    requiresConfirmation: value.requires_confirmation,
    blockers: value.blocking_issues.map((item) => ({
      code: item.code,
      objectType: item.object_type,
      objectId: item.object_id ?? null,
      message: item.message,
      blocking: true,
    })),
    warnings: value.warnings.map((item) => ({
      code: item.code,
      objectType: item.object_type,
      objectId: item.object_id ?? null,
      message: item.message,
      blocking: false,
    })),
    candidates: value.candidate_items.map(mapCandidate),
    limitations: [...value.limitations],
    snapshotHash: value.snapshot_hash,
    ruleSetVersion: value.rule_set_version,
  }
}

export function mapExport(value: ExportPublic): ExportViewModel {
  const status = stringValue(value.status)
  const knownStatus = KNOWN.export.has(status)
  return {
    id: value.id,
    projectId: value.project_id,
    exportType: stringValue(value.export_type),
    scopeHash: value.scope_hash,
    readinessAuditId: value.readiness_audit_id,
    approvalId: value.approval_record_id,
    jobId: value.job_id,
    lockVersion: value.lock_version,
    errorCode: value.error_code,
    status,
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

export function mapApproval(
  value: ApprovalPublic,
  exportId: string,
): ApprovalViewModel {
  const status = stringValue(value.status)
  const knownStatus = KNOWN.approval.has(status)
  return {
    id: value.id,
    projectId: value.project_id,
    targetObjectType: value.target_object_type,
    targetObjectId: value.target_object_id,
    payloadHash: value.payload_hash,
    stale:
      value.target_object_type !== "export" ||
      value.target_object_id !== exportId ||
      status === "SUPERSEDED" ||
      status === "EXPIRED",
    expiresAt: value.expires_at,
    items: value.items.map((item) => ({
      itemType: item.item_type,
      itemId: item.item_id,
      decision: item.decision,
      reason: item.reason,
    })),
    status,
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

export function mapJob(value: JobPublic): JobViewModel {
  const status = stringValue(value.status)
  return {
    id: value.id,
    projectId: value.project_id,
    taskType: stringValue(value.task_type),
    resourceType: value.resource_type,
    resourceId: value.resource_id,
    progress: value.progress_percent,
    retryable: value.retryable,
    errorCode: value.error?.code ?? null,
    status,
    knownStatus: KNOWN.job.has(status),
  }
}

function mapManifestFile(
  value: Record<string, unknown>,
): ManifestFileViewModel {
  return {
    path: stringValue(value.path, ""),
    size: typeof value.size === "number" ? value.size : 0,
    sha256: stringValue(value.sha256, ""),
    type: stringValue(value.type),
    source: objectValue(value.source) ?? {},
    licenseStatus: stringValue(value.license_status),
    sensitive: value.sensitive === true,
    redistribution: stringValue(value.redistribution),
  }
}

function mapManifest(value: ReproPackagePublic): ManifestViewModel {
  const manifest = objectValue(value.manifest) ?? {}
  return {
    schemaVersion: stringValue(
      manifest.manifest_schema_version,
      value.schema_version,
    ),
    sha256: value.manifest_sha256,
    files: records(manifest.files).map(mapManifestFile),
    agentLogs: stringValue(manifest.agent_logs, "NOT_AVAILABLE"),
    limitations: strings(manifest.limitations),
    runtimeDependencies: records(manifest.runtime_dependencies),
    serviceImages: records(manifest.service_images),
  }
}

export function mapPackage(value: ReproPackagePublic): ReproPackageViewModel {
  const manifest = mapManifest(value)
  const knownStatus = value.allowed_actions.includes("export.read")
  return {
    id: value.id,
    exportId: value.export_id,
    projectId: value.project_id,
    artifactId: value.artifact_id,
    manifestArtifactId: value.manifest_artifact_id,
    packageVersion: value.package_version,
    schemaVersion: value.schema_version,
    containsSensitiveData: value.contains_sensitive_data,
    containsRestrictedData: value.contains_restricted_data,
    fileCount: value.file_count,
    totalSizeBytes: value.total_size_bytes,
    sha256: value.sha256,
    manifest,
    tampered:
      !/^[0-9a-f]{64}$/.test(value.sha256) ||
      !/^[0-9a-f]{64}$/.test(value.manifest_sha256),
    status: knownStatus ? "AVAILABLE" : "UNKNOWN",
    knownStatus,
    allowedActions: knownStatus ? actions(value.allowed_actions) : new Set(),
  }
}

function mapPackageHistoryItem(
  value: ReproPackageHistoryItem,
  selectedPackageId: string | null,
): ReproPackageHistoryItemViewModel {
  return {
    id: value.id,
    exportId: value.export_id,
    projectId: value.project_id,
    artifactId: value.artifact_id,
    manifestArtifactId: value.manifest_artifact_id,
    packageVersion: value.package_version,
    schemaVersion: value.schema_version,
    containsSensitiveData: value.contains_sensitive_data,
    containsRestrictedData: value.contains_restricted_data,
    fileCount: value.file_count,
    totalSizeBytes: value.total_size_bytes,
    sha256: value.sha256,
    createdAt: value.created_at,
    selected: value.id === selectedPackageId,
    allowedActions: actions(value.allowed_actions),
  }
}

const capability = (
  permissionsKnown: boolean,
  allowed: boolean,
  reason: string,
): ActionCapability => ({
  allowed: permissionsKnown && allowed,
  disabledReason: permissionsKnown && allowed ? null : reason,
})

function scopeNotices(
  graph: EvidenceGraphProjection,
  nodes: readonly EvidenceGraphNodeViewModel[],
  completeness: Readonly<Record<string, ClaimCompletenessViewModel>>,
): EvidenceScopeNotice[] {
  const notices: EvidenceScopeNotice[] = []
  if (graph.limitations.some((item) => item.includes("authorized scope")))
    notices.push({
      scope: "DENIED",
      message: "Some evidence is outside the current authorized scope.",
    })
  if (
    Object.values(completeness).some((value) =>
      value.items.some((item) => item.status === "MISSING"),
    )
  )
    notices.push({ scope: "MISSING", message: "Required evidence is missing." })
  if (nodes.some((node) => node.scope === "STALE"))
    notices.push({ scope: "STALE", message: "Some visible evidence is stale." })
  if (nodes.some((node) => node.scope === "UNKNOWN"))
    notices.push({
      scope: "UNKNOWN",
      message: "Some visible evidence has an unknown status.",
    })
  return notices
}

export function mapEvidenceWorkspace(input: {
  projectId: string
  project: ProjectPublic
  graph: EvidenceGraphProjection
  selectedClaim: ClaimPublic | null
  links: readonly ClaimEvidenceLinkPublic[]
  selectedLink: ClaimEvidenceLinkPublic | null
  selectedNodeId?: string
  audit: ClaimAuditPublic | null
  auditJob: JobPublic | null
  readiness: ExportReadiness | null
  export: ExportPublic | null
  approval: ApprovalPublic | null
  job: JobPublic | null
  package: ReproPackagePublic | null
  packageHistory: readonly ReproPackageHistoryItem[]
  packageHistoryPage: number
  packageHistoryHasNext: boolean
}): EvidenceWorkspaceViewModel {
  const permissionsKnown = Array.isArray(input.project.allowed_actions)
  const projectActions = actions(input.project.allowed_actions)
  const nodes = input.graph.nodes.map(mapGraphNode)
  const edges = input.graph.edges.map(mapGraphEdge)
  const canvas = mapGraphCanvas(nodes, edges)
  const selectedClaim = input.selectedClaim
    ? mapClaim(input.selectedClaim)
    : null
  const links = input.links.map(mapLink)
  const selectedLink = input.selectedLink ? mapLink(input.selectedLink) : null
  const selectedNode = input.selectedNodeId
    ? (nodes.find((node) => node.id === input.selectedNodeId) ?? null)
    : null
  const completeness = Object.fromEntries(
    Object.entries(input.graph.completeness).map(([id, value]) => [
      id,
      mapCompleteness(value),
    ]),
  )
  const audit = input.audit ? mapAudit(input.audit) : null
  const auditJob = input.auditJob ? mapJob(input.auditJob) : null
  const readiness = input.readiness ? mapReadiness(input.readiness) : null
  const exportValue = input.export ? mapExport(input.export) : null
  const approval =
    input.approval && exportValue
      ? mapApproval(input.approval, exportValue.id)
      : null
  const job = input.job ? mapJob(input.job) : null
  const packageValue = input.package ? mapPackage(input.package) : null
  const packageHistory = input.packageHistory.map((item) =>
    mapPackageHistoryItem(item, packageValue?.id ?? null),
  )
  const selectedClaimActions =
    selectedClaim?.allowedActions ?? new Set<string>()
  const linkActions = selectedLink?.allowedActions ?? new Set<string>()
  const packageActions = packageValue?.allowedActions ?? new Set<string>()
  const routeFallback =
    (input.selectedNodeId !== undefined && selectedNode === null) ||
    (input.selectedClaim === null && input.links.length > 0)
  const claims: ClaimSummaryViewModel[] = nodes
    .filter((node) => node.nodeType === "CLAIM")
    .map((node) => ({
      id: node.objectId,
      label: node.label,
      risk: node.risk,
      stale: node.stale,
      invalidated: node.invalidated,
      status: node.status,
      knownStatus: node.knownStatus,
      allowedActions: node.allowedActions,
    }))
  return {
    projectId: input.projectId,
    permissionsKnown,
    graph: {
      nodes,
      edges,
      canvasNodes: canvas.nodes,
      canvasEdges: canvas.edges,
      complete: !input.graph.partial,
      partial: input.graph.partial,
      nextCursor: input.graph.next_cursor,
      degraded:
        nodes.some((node) => !node.knownStatus) ||
        edges.some((edge) => !edge.knownStatus),
      limitations: [...input.graph.limitations],
    },
    claims,
    selectedClaim,
    links,
    selectedLink,
    selectedNode,
    completeness,
    audit,
    auditJob,
    readiness,
    export: exportValue,
    approval,
    job,
    package: packageValue,
    packageHistory,
    packageHistoryPage: input.packageHistoryPage,
    packageHistoryHasNext: input.packageHistoryHasNext,
    scopeNotices: scopeNotices(input.graph, nodes, completeness),
    routeFallback,
    capabilities: {
      permissionsKnown,
      createEvidenceLink: capability(
        permissionsKnown,
        selectedClaim?.knownStatus === true &&
          selectedClaimActions.has("evidence.link.create"),
        "A known Claim and server-allowed create action are required.",
      ),
      confirmEvidenceLink: capability(
        permissionsKnown,
        selectedLink?.knownStatus === true &&
          linkActions.has("evidence.link.confirm"),
        "A current suggested Link and server confirmation action are required.",
      ),
      invalidateEvidenceLink: capability(
        permissionsKnown,
        selectedLink?.knownStatus === true &&
          linkActions.has("evidence.link.invalidate"),
        "A current active Link and server invalidation action are required.",
      ),
      runClaimAudit: capability(
        permissionsKnown,
        selectedClaim?.knownStatus === true &&
          projectActions.has("evidence.audit.run"),
        "A known Claim and audit permission are required.",
      ),
      runExportReadiness: capability(
        permissionsKnown,
        projectActions.has("export.readiness"),
        "Export readiness permission is unavailable.",
      ),
      createReproPackage: capability(
        permissionsKnown,
        projectActions.has("export.create"),
        "ReproPackage creation permission is unavailable.",
      ),
      requestExportConfirmation: capability(
        permissionsKnown,
        exportValue?.status === "NEEDS_CONFIRMATION" &&
          approval?.status === "PENDING" &&
          approval.stale === false &&
          projectActions.has("export.confirm"),
        "A current pending Export Approval is required.",
      ),
      retryJob: capability(
        permissionsKnown,
        job?.knownStatus === true &&
          job.retryable &&
          ["FAILED", "DISPATCH_FAILED"].includes(job.status) &&
          projectActions.has("job.retry"),
        "Only a retryable failed Job can be retried.",
      ),
      cancelJob: capability(
        permissionsKnown,
        job?.knownStatus === true &&
          ["QUEUED", "RUNNING"].includes(job.status) &&
          projectActions.has("job.cancel"),
        "Only an active cancellable Job can be cancelled.",
      ),
      downloadReproPackage: capability(
        permissionsKnown,
        packageValue?.knownStatus === true &&
          !packageValue.tampered &&
          packageActions.has("export.download"),
        "A verified AVAILABLE ReproPackage is required.",
      ),
    },
  }
}
