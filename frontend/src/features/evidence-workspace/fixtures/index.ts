import type { UiErrorViewModel } from "../../projects/model"
import type {
  EvidenceWorkspaceView,
  EvidenceWorkspaceViewModel,
} from "../model"
import type {
  EvidenceWorkspaceEvent,
  EvidenceWorkspaceProps,
} from "../ui/contracts"

const id = (value: number) =>
  `00000000-0000-4000-8000-${String(value).padStart(12, "0")}`
const hash = (value: string) => value.repeat(64).slice(0, 64)
const actions = (...values: string[]) => new Set(values)
const capability = (
  allowed: boolean,
  reason = "Not allowed by server facts",
) => ({
  allowed,
  disabledReason: allowed ? null : reason,
})

const graphNode = (
  value: number,
  nodeType: string,
  label: string,
  rank: number,
) => ({
  id: `${nodeType}:${id(value)}`,
  nodeType,
  objectId: id(value),
  label,
  risk: "LOW" as const,
  scope: "AVAILABLE" as const,
  invalidated: false,
  stale: false,
  sourceKind: "DOMAIN" as const,
  detailIntent: `open-${nodeType.toLowerCase()}`,
  limitations: [] as string[],
  allowedActions: actions("evidence.read"),
  lane: nodeType,
  rank,
  status: "AVAILABLE",
  knownStatus: true,
})

const baseWorkspace = (): EvidenceWorkspaceViewModel => {
  const nodes = [
    graphNode(10, "CLAIM", "Remote work improves retention", 0),
    graphNode(11, "EVIDENCE_SPAN", "Longitudinal study, page 14", 1),
    graphNode(12, "DATASET_VERSION", "Retention cohort v3", 1),
    graphNode(13, "ANALYSIS_RESULT", "Adjusted hazard ratio", 2),
    graphNode(14, "FIGURE", "Retention survival curve", 3),
  ]
  const edges = [
    {
      id: `link:${id(20)}`,
      source: nodes[0].id,
      target: nodes[1].id,
      relationType: "SUPPORTED_BY",
      strength: "STRONG",
      semantic: "SUPPORT" as const,
      risk: "LOW" as const,
      invalidated: false,
      sourceKind: "STORED" as const,
      status: "ACTIVE",
      knownStatus: true,
    },
    {
      id: `derived:${id(12)}:${id(13)}`,
      source: nodes[2].id,
      target: nodes[3].id,
      relationType: "PRODUCES",
      strength: null,
      semantic: "PROVENANCE" as const,
      risk: "LOW" as const,
      invalidated: false,
      sourceKind: "DERIVED" as const,
      status: "AVAILABLE",
      knownStatus: true,
    },
  ]
  const selectedClaim = {
    id: id(10),
    projectId: id(1),
    claimType: "INTERPRETIVE",
    text: "Remote work improves retention in the observed cohort.",
    sourceObjectType: "MANUSCRIPT_VERSION",
    sourceObjectId: id(9),
    sourceHash: hash("a"),
    textHash: hash("b"),
    lockVersion: 3,
    stale: false,
    status: "SUPPORTED",
    knownStatus: true,
    allowedActions: actions("evidence.link.create", "evidence.audit.run"),
  }
  const selectedLink = {
    id: id(20),
    projectId: id(1),
    claimId: id(10),
    relationType: "SUPPORTED_BY",
    semantic: "SUPPORT" as const,
    strength: "STRONG",
    explanation: "The quoted passage reports the observed association.",
    lockVersion: 2,
    stale: false,
    invalidated: false,
    evidence: {
      objectType: "EVIDENCE_SPAN",
      objectId: id(11),
      projectId: id(1),
      label: "Longitudinal study, page 14",
      sourceHash: hash("c"),
      detailIntent: "open-evidence-span",
      scope: "AVAILABLE" as const,
      stale: false,
      invalidated: false,
      limitations: [] as string[],
      status: "AVAILABLE",
      knownStatus: true,
      allowedActions: actions("evidence.read"),
    },
    status: "ACTIVE",
    knownStatus: true,
    allowedActions: actions("evidence.link.invalidate"),
  }
  const readiness = {
    auditId: id(30),
    ready: true,
    requiresConfirmation: false,
    blockers: [],
    warnings: [],
    candidates: [
      {
        objectType: "MANIFEST",
        objectId: id(31),
        artifactId: id(32),
        packagePath: "manifest.json",
        sha256: hash("d"),
        exclusionReason: null,
        licenseStatus: "PERMITTED",
        sensitive: false,
        redistribution: "INCLUDED",
        status: "INCLUDED",
        knownStatus: true,
      },
    ],
    limitations: ["Agent logs are NOT_AVAILABLE before M8."],
    snapshotHash: hash("e"),
    ruleSetVersion: "m7-export-readiness-v1",
  }
  const exportValue = {
    id: id(40),
    projectId: id(1),
    exportType: "REPRO_PACKAGE",
    scopeHash: hash("f"),
    readinessAuditId: id(30),
    approvalId: null,
    jobId: id(41),
    lockVersion: 4,
    errorCode: null,
    status: "COMPLETED",
    knownStatus: true,
    allowedActions: actions("export.read"),
  }
  const packageValue = {
    id: id(50),
    exportId: id(40),
    projectId: id(1),
    artifactId: id(51),
    manifestArtifactId: id(52),
    packageVersion: 2,
    schemaVersion: "reca.repro-package.v1",
    containsSensitiveData: false,
    containsRestrictedData: true,
    fileCount: 3,
    totalSizeBytes: 8192,
    sha256: hash("1"),
    manifest: {
      schemaVersion: "reca.repro-package.manifest.v1",
      sha256: hash("2"),
      files: [
        {
          path: "README_REPRODUCE.md",
          size: 1200,
          sha256: hash("3"),
          type: "README",
          source: { generated_by: "reca", rule_version: "v1" },
          licenseStatus: "PERMITTED",
          sensitive: false,
          redistribution: "INCLUDED",
        },
        {
          path: "literature/record-11/metadata.json",
          size: 820,
          sha256: hash("4"),
          type: "LITERATURE_METADATA",
          source: { object_id: id(11), source_version: 2 },
          licenseStatus: "RESTRICTED",
          sensitive: false,
          redistribution: "METADATA_ONLY",
        },
      ],
      agentLogs: "NOT_AVAILABLE" as const,
      limitations: ["Restricted PDF bytes are not included."],
      runtimeDependencies: [{ name: "reca", version: "0.1.0" }],
      serviceImages: [{ service: "backend", digest: `sha256:${hash("5")}` }],
    },
    tampered: false,
    status: "AVAILABLE",
    knownStatus: true,
    allowedActions: actions("export.download"),
  }
  return {
    projectId: id(1),
    permissionsKnown: true,
    graph: {
      nodes,
      edges,
      canvasNodes: nodes.map((node, index) => ({
        id: node.id,
        position: { x: node.rank * 320, y: index * 104 },
        data: node,
        selectable: true,
        draggable: true,
        connectable: false,
      })),
      canvasEdges: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        data: edge,
        selectable: true,
        reconnectable: false,
      })),
      complete: true,
      partial: false,
      nextCursor: null,
      degraded: false,
      limitations: [],
    },
    claims: [
      {
        id: id(10),
        label: nodes[0].label,
        risk: "LOW",
        stale: false,
        invalidated: false,
        status: "SUPPORTED",
        knownStatus: true,
        allowedActions: actions("evidence.read"),
      },
    ],
    selectedClaim,
    links: [selectedLink],
    selectedLink,
    selectedNode: nodes[0],
    completeness: {
      [id(10)]: {
        claimId: id(10),
        ruleSetVersion: "m7-completeness-v1",
        items: [
          {
            code: "ACTIVE_SOURCE",
            sourceObjectIds: [id(11)],
            limitations: [],
            missingActions: [],
            scientificQualityScore: null,
            status: "SATISFIED",
            knownStatus: true,
          },
        ],
        limitations: ["Completeness is not a scientific quality score."],
        isScientificQualityScore: false,
      },
    },
    audit: {
      id: id(60),
      projectId: id(1),
      auditType: "CLAIM_EVIDENCE",
      targetObjectType: "CLAIM",
      targetObjectId: id(10),
      jobId: id(61),
      outcome: "VERIFIED",
      outcomeKnown: true,
      sourceSnapshotHash: hash("6"),
      resultHash: hash("7"),
      findings: [],
      limitations: [],
      degraded: false,
      ruleSetVersion: "m7-claim-audit-v1",
      status: "COMPLETED",
      knownStatus: true,
      allowedActions: actions("evidence.audit.read"),
    },
    auditJob: {
      id: id(61),
      projectId: id(1),
      taskType: "EVIDENCE_AUDIT",
      resourceType: "audit_result",
      resourceId: id(60),
      progress: 100,
      retryable: false,
      errorCode: null,
      status: "COMPLETED",
      knownStatus: true,
    },
    readiness,
    export: exportValue,
    approval: null,
    job: {
      id: id(41),
      projectId: id(1),
      taskType: "REPRO_PACKAGE_EXPORT",
      resourceType: "EXPORT",
      resourceId: id(40),
      progress: 100,
      retryable: false,
      errorCode: null,
      status: "COMPLETED",
      knownStatus: true,
    },
    package: packageValue,
    packageHistory: [
      {
        id: packageValue.id,
        exportId: packageValue.exportId,
        projectId: packageValue.projectId,
        artifactId: packageValue.artifactId,
        manifestArtifactId: packageValue.manifestArtifactId,
        packageVersion: packageValue.packageVersion,
        schemaVersion: packageValue.schemaVersion,
        containsSensitiveData: packageValue.containsSensitiveData,
        containsRestrictedData: packageValue.containsRestrictedData,
        fileCount: packageValue.fileCount,
        totalSizeBytes: packageValue.totalSizeBytes,
        sha256: packageValue.sha256,
        createdAt: "2026-08-06T08:00:00Z",
        selected: true,
        allowedActions: actions("export.read", "export.download"),
      },
    ],
    packageHistoryPage: 1,
    packageHistoryHasNext: false,
    scopeNotices: [],
    routeFallback: false,
    capabilities: {
      permissionsKnown: true,
      createEvidenceLink: capability(true),
      confirmEvidenceLink: capability(false),
      invalidateEvidenceLink: capability(true),
      runClaimAudit: capability(true),
      runExportReadiness: capability(true),
      createReproPackage: capability(true),
      requestExportConfirmation: capability(false),
      retryJob: capability(false),
      cancelJob: capability(false),
      downloadReproPackage: capability(true),
    },
  }
}

const error = (
  overrides: Partial<UiErrorViewModel> = {},
): UiErrorViewModel => ({
  title: "Request failed",
  message: "The server did not accept the request.",
  code: "UNKNOWN",
  requestId: "request-m7-fixture",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
  ...overrides,
})

export type EvidenceWorkspaceFixture = {
  id: string
  title: string
  description: string
  viewport: "desktop" | "tablet" | "mobile"
  theme: "light" | "dark"
  initialView: EvidenceWorkspaceView
  content: EvidenceWorkspaceProps["content"]
  pendingAction: EvidenceWorkspaceEvent["action"] | null
  mutationError: UiErrorViewModel | null
}

const ready = (
  fixtureId: string,
  mutate: (
    workspace: EvidenceWorkspaceViewModel,
  ) => EvidenceWorkspaceViewModel = (workspace) => workspace,
  options: Partial<Omit<EvidenceWorkspaceFixture, "id" | "content">> = {},
): EvidenceWorkspaceFixture => ({
  id: fixtureId,
  title: fixtureId.replace(/-/g, " "),
  description: `Synthetic M7 contract fixture: ${fixtureId}`,
  viewport: "desktop",
  theme: "light",
  initialView: "graph",
  pendingAction: null,
  mutationError: null,
  ...options,
  content: { state: "ready", data: mutate(baseWorkspace()) },
})

const completeness = (fixtureId: string, status: string) =>
  ready(fixtureId, (workspace) => {
    const current = workspace.completeness[id(10)]
    return {
      ...workspace,
      completeness: {
        [id(10)]: {
          ...current,
          items: [
            {
              ...current.items[0],
              status,
              knownStatus: status !== "FUTURE_COMPLETENESS_STATE",
              missingActions: status === "MISSING" ? ["link evidence"] : [],
              limitations: status === "RESTRICTED" ? ["scope denied"] : [],
            },
          ],
        },
      },
    }
  })

const exportState = (fixtureId: string, status: string, progress: number) =>
  ready(
    fixtureId,
    (workspace) => ({
      ...workspace,
      export: workspace.export ? { ...workspace.export, status } : null,
      job: workspace.job ? { ...workspace.job, progress, status } : null,
      package: status === "COMPLETED" ? workspace.package : null,
    }),
    { initialView: "exports" },
  )

const approvalState = (fixtureId: string, status: string, stale = false) =>
  ready(
    fixtureId,
    (workspace) => ({
      ...workspace,
      export: workspace.export
        ? {
            ...workspace.export,
            status: "NEEDS_CONFIRMATION",
            approvalId: id(70),
          }
        : null,
      approval: {
        id: id(70),
        projectId: id(1),
        targetObjectType: "EXPORT",
        targetObjectId: id(40),
        payloadHash: hash("8"),
        stale,
        expiresAt: "2026-08-07T00:00:00Z",
        items: [
          {
            itemType: "export_warning",
            itemId: id(71),
            decision: null,
            reason: null,
          },
        ],
        status,
        knownStatus: status !== "FUTURE_APPROVAL_STATE",
        allowedActions: actions("export.confirm"),
      },
      capabilities: {
        ...workspace.capabilities,
        requestExportConfirmation: capability(status === "PENDING" && !stale),
      },
    }),
    { initialView: "exports" },
  )

const nodeChain = (fixtureId: string, count: number) =>
  ready(fixtureId, (workspace) => ({
    ...workspace,
    graph: {
      ...workspace.graph,
      nodes: workspace.graph.nodes.slice(0, count),
      edges: workspace.graph.edges.slice(0, Math.max(0, count - 1)),
      canvasNodes: workspace.graph.canvasNodes.slice(0, count),
      canvasEdges: workspace.graph.canvasEdges.slice(0, Math.max(0, count - 1)),
    },
  }))

export const evidenceWorkspaceFixtures = [
  ready("graph-empty", (w) => ({
    ...w,
    graph: {
      ...w.graph,
      nodes: [],
      edges: [],
      canvasNodes: [],
      canvasEdges: [],
    },
    claims: [],
    selectedClaim: null,
    links: [],
    selectedLink: null,
    selectedNode: null,
  })),
  nodeChain("graph-single-claim", 1),
  nodeChain("graph-literature-chain", 2),
  nodeChain("graph-data-analysis-figure-chain", 5),
  ready("graph-full-chain"),
  ready("edge-contradict", (w) => ({
    ...w,
    graph: {
      ...w.graph,
      edges: w.graph.edges.map((edge, index) =>
        index === 0
          ? { ...edge, semantic: "CONTRADICT", relationType: "CONTRADICTED_BY" }
          : edge,
      ),
    },
  })),
  ready("edge-qualify", (w) => ({
    ...w,
    graph: {
      ...w.graph,
      edges: w.graph.edges.map((edge, index) =>
        index === 0 ? { ...edge, semantic: "QUALIFY", strength: "WEAK" } : edge,
      ),
    },
  })),
  ready("link-suggested", (w) => ({
    ...w,
    selectedLink: w.selectedLink
      ? {
          ...w.selectedLink,
          status: "SUGGESTED",
          allowedActions: actions("evidence.link.confirm"),
        }
      : null,
    capabilities: {
      ...w.capabilities,
      confirmEvidenceLink: capability(true),
    },
  })),
  ready("link-invalidated-stale", (w) => ({
    ...w,
    selectedLink: w.selectedLink
      ? {
          ...w.selectedLink,
          status: "INVALIDATED",
          stale: true,
          invalidated: true,
        }
      : null,
  })),
  ready("link-unknown", (w) => ({
    ...w,
    selectedLink: w.selectedLink
      ? {
          ...w.selectedLink,
          status: "FUTURE_LINK_STATE",
          knownStatus: false,
          allowedActions: actions(),
        }
      : null,
  })),
  ready("evidence-denied-no-disclosure", (w) => ({
    ...w,
    scopeNotices: [
      {
        scope: "DENIED",
        message: "Some evidence is outside the authorized scope.",
      },
    ],
    graph: { ...w.graph, limitations: ["authorized scope limited"] },
  })),
  ready("evidence-missing", (w) => ({
    ...w,
    scopeNotices: [
      { scope: "MISSING", message: "Required evidence is missing." },
    ],
  })),
  ready("evidence-stale", (w) => ({
    ...w,
    graph: {
      ...w.graph,
      nodes: w.graph.nodes.map((node, index) =>
        index === 1 ? { ...node, scope: "STALE", stale: true } : node,
      ),
    },
  })),
  completeness("completeness-satisfied", "SATISFIED"),
  completeness("completeness-missing", "MISSING"),
  completeness("completeness-restricted", "RESTRICTED"),
  completeness("completeness-conflicted", "CONFLICTED"),
  completeness("completeness-unknown", "FUTURE_COMPLETENESS_STATE"),
  completeness("completeness-not-applicable", "NOT_APPLICABLE"),
  ready(
    "audit-queued",
    (w) => ({
      ...w,
      audit: w.audit
        ? { ...w.audit, status: "QUEUED", outcome: null, outcomeKnown: false }
        : null,
    }),
    { initialView: "audits" },
  ),
  ready(
    "audit-running-degraded",
    (w) => ({
      ...w,
      audit: w.audit
        ? {
            ...w.audit,
            status: "RUNNING",
            outcome: null,
            outcomeKnown: false,
            degraded: true,
            limitations: [
              "AI provider unavailable; deterministic audit continues.",
            ],
          }
        : null,
    }),
    { initialView: "audits" },
  ),
  ready(
    "audit-needs-review",
    (w) => ({
      ...w,
      audit: w.audit ? { ...w.audit, outcome: "NEEDS_REVIEW" } : null,
    }),
    { initialView: "audits" },
  ),
  ready(
    "audit-insufficient",
    (w) => ({
      ...w,
      audit: w.audit ? { ...w.audit, outcome: "INSUFFICIENT_EVIDENCE" } : null,
    }),
    { initialView: "audits" },
  ),
  ready(
    "audit-conflicted",
    (w) => ({
      ...w,
      audit: w.audit ? { ...w.audit, outcome: "CONFLICTED" } : null,
    }),
    { initialView: "audits" },
  ),
  ready(
    "audit-failed",
    (w) => ({
      ...w,
      audit: w.audit
        ? { ...w.audit, status: "FAILED", outcome: null, outcomeKnown: false }
        : null,
    }),
    { initialView: "audits" },
  ),
  ready(
    "audit-unknown",
    (w) => ({
      ...w,
      audit: w.audit
        ? {
            ...w.audit,
            status: "FUTURE_AUDIT_STATE",
            knownStatus: false,
            allowedActions: actions(),
          }
        : null,
    }),
    { initialView: "audits" },
  ),
  ready("graph-partial-cursor", (w) => ({
    ...w,
    graph: {
      ...w.graph,
      complete: false,
      partial: true,
      nextCursor: "cursor-page-2",
      limitations: ["Node limit reached."],
    },
  })),
  ready("graph-large-500", (w) => {
    const nodes = Array.from({ length: 500 }, (_, index) =>
      graphNode(
        1000 + index,
        index === 0 ? "CLAIM" : "EVIDENCE_SPAN",
        `Representative node ${index + 1}`,
        index % 8,
      ),
    )
    const edges = nodes.slice(1).map((node, index) => ({
      ...w.graph.edges[0],
      id: `large-edge-${index}`,
      source: nodes[0].id,
      target: node.id,
    }))
    return {
      ...w,
      graph: {
        ...w.graph,
        nodes,
        edges,
        canvasNodes: nodes.map((node, index) => ({
          id: node.id,
          position: { x: (index % 8) * 280, y: Math.floor(index / 8) * 88 },
          data: node,
          selectable: true,
          draggable: true,
          connectable: false,
        })),
        canvasEdges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          data: edge,
          selectable: true,
          reconnectable: false,
        })),
        complete: false,
        partial: true,
        nextCursor: "cursor-after-500",
        limitations: ["500-node representative limit reached."],
      },
    }
  }),
  ready("permissions-unknown", (w) => ({
    ...w,
    permissionsKnown: false,
    capabilities: Object.fromEntries(
      Object.entries(w.capabilities).map(([key]) =>
        key === "permissionsKnown"
          ? [key, false]
          : [key, capability(false, "Permissions are unknown.")],
      ),
    ) as EvidenceWorkspaceViewModel["capabilities"],
  })),
  ready("read-only", (w) => ({
    ...w,
    capabilities: {
      ...w.capabilities,
      createEvidenceLink: capability(false),
      invalidateEvidenceLink: capability(false),
      runClaimAudit: capability(false),
      runExportReadiness: capability(false),
      createReproPackage: capability(false),
    },
  })),
  ready("route-fallback", (w) => ({
    ...w,
    routeFallback: true,
    selectedNode: null,
    selectedClaim: null,
    selectedLink: null,
  })),
  ready("readiness-ready", undefined, { initialView: "exports" }),
  ready(
    "readiness-license-blocker",
    (w) => ({
      ...w,
      readiness: w.readiness
        ? {
            ...w.readiness,
            ready: false,
            blockers: [
              {
                code: "REDISTRIBUTION_PROHIBITED",
                objectType: "ARTIFACT",
                objectId: id(80),
                message: "License prohibits redistribution.",
                blocking: true,
              },
            ],
          }
        : null,
    }),
    { initialView: "exports" },
  ),
  ready(
    "readiness-sensitive-warning",
    (w) => ({
      ...w,
      readiness: w.readiness
        ? {
            ...w.readiness,
            requiresConfirmation: true,
            warnings: [
              {
                code: "SENSITIVE_CONFIRMATION_REQUIRED",
                objectType: "DATASET_VERSION",
                objectId: id(12),
                message: "Sensitive data requires formal confirmation.",
                blocking: false,
              },
            ],
          }
        : null,
    }),
    { initialView: "exports" },
  ),
  ready(
    "readiness-missing-artifact",
    (w) => ({
      ...w,
      readiness: w.readiness
        ? {
            ...w.readiness,
            ready: false,
            candidates: [
              {
                ...w.readiness.candidates[0],
                status: "MISSING",
                knownStatus: true,
                exclusionReason: "ARTIFACT_MISSING",
              },
            ],
          }
        : null,
    }),
    { initialView: "exports" },
  ),
  ready(
    "readiness-invalidated-unconfirmed",
    (w) => ({
      ...w,
      readiness: w.readiness
        ? {
            ...w.readiness,
            ready: false,
            blockers: [
              {
                code: "SOURCE_INVALIDATED",
                objectType: "CLAIM",
                objectId: id(10),
                message: "A selected source is invalidated or unconfirmed.",
                blocking: true,
              },
            ],
          }
        : null,
    }),
    { initialView: "exports" },
  ),
  ready(
    "readiness-unknown",
    (w) => ({
      ...w,
      readiness: w.readiness
        ? {
            ...w.readiness,
            ready: false,
            candidates: [
              {
                ...w.readiness.candidates[0],
                status: "FUTURE_INCLUDE_STATE",
                knownStatus: false,
              },
            ],
          }
        : null,
    }),
    { initialView: "exports" },
  ),
  exportState("export-draft", "DRAFT", 0),
  exportState("export-validating", "VALIDATING", 10),
  exportState("export-queued", "QUEUED", 20),
  exportState("export-packaging", "PACKAGING", 65),
  exportState("export-completed", "COMPLETED", 100),
  exportState("export-failed", "FAILED", 70),
  exportState("export-cancelled", "CANCELLED", 30),
  ready(
    "export-failed-retryable",
    (w) => ({
      ...w,
      export: w.export ? { ...w.export, status: "FAILED" } : null,
      job: w.job
        ? {
            ...w.job,
            progress: 70,
            retryable: true,
            errorCode: "PACKAGE_UPLOAD_FAILED",
            status: "FAILED",
          }
        : null,
      package: null,
      capabilities: {
        ...w.capabilities,
        retryJob: capability(true),
        cancelJob: capability(false),
        downloadReproPackage: capability(false),
      },
    }),
    { initialView: "exports" },
  ),
  ready(
    "export-running-cancellable",
    (w) => ({
      ...w,
      export: w.export ? { ...w.export, status: "PACKAGING" } : null,
      job: w.job
        ? {
            ...w.job,
            progress: 45,
            retryable: false,
            errorCode: null,
            status: "RUNNING",
          }
        : null,
      package: null,
      capabilities: {
        ...w.capabilities,
        retryJob: capability(false),
        cancelJob: capability(true),
        downloadReproPackage: capability(false),
      },
    }),
    { initialView: "exports" },
  ),
  approvalState("approval-pending", "PENDING"),
  approvalState("approval-approved", "APPROVED"),
  approvalState("approval-stale", "APPROVED", true),
  approvalState("approval-rejected", "REJECTED"),
  approvalState("approval-expired", "EXPIRED"),
  ready(
    "package-tampered",
    (w) => ({
      ...w,
      package: w.package
        ? { ...w.package, tampered: true, allowedActions: actions() }
        : null,
    }),
    { initialView: "exports" },
  ),
  ready(
    "package-unavailable",
    (w) => ({
      ...w,
      package: w.package
        ? {
            ...w.package,
            status: "FAILED",
            knownStatus: true,
            allowedActions: actions(),
          }
        : null,
    }),
    { initialView: "exports" },
  ),
  ready(
    "package-history-versions",
    (w) => ({
      ...w,
      package: w.package ? { ...w.package, packageVersion: 7 } : null,
      packageHistory: w.packageHistory.length
        ? [
            {
              ...w.packageHistory[0],
              packageVersion: 7,
              selected: true,
            },
            {
              ...w.packageHistory[0],
              id: id(53),
              exportId: id(43),
              artifactId: id(54),
              manifestArtifactId: id(55),
              packageVersion: 6,
              fileCount: 2,
              totalSizeBytes: 4096,
              sha256: hash("9"),
              createdAt: "2026-08-05T08:00:00Z",
              selected: false,
            },
            {
              ...w.packageHistory[0],
              id: id(56),
              exportId: id(44),
              artifactId: id(57),
              manifestArtifactId: id(58),
              packageVersion: 5,
              fileCount: 2,
              totalSizeBytes: 3072,
              sha256: hash("0"),
              createdAt: "2026-08-04T08:00:00Z",
              selected: false,
            },
          ]
        : [],
      scopeNotices: [
        {
          scope: "STALE",
          message:
            "Earlier immutable package versions remain available in history.",
        },
      ],
    }),
    { initialView: "exports" },
  ),
  ready(
    "manifest-long-paths-licenses",
    (w) => ({
      ...w,
      package: w.package
        ? {
            ...w.package,
            manifest: {
              ...w.package.manifest,
              files: [
                {
                  ...w.package.manifest.files[1],
                  path: `literature/${"long-segment/".repeat(8)}metadata-only.json`,
                  redistribution: "REFERENCE_ONLY",
                },
              ],
            },
          }
        : null,
    }),
    { initialView: "exports" },
  ),
  ready("mutation-pending", undefined, {
    pendingAction: "create-repro-package",
    initialView: "exports",
  }),
  ready("mutation-conflict", undefined, {
    mutationError: error({
      code: "PRECONDITION_FAILED",
      conflict: true,
      retryable: false,
    }),
    initialView: "exports",
  }),
  ready("desktop-light", (w) => ({ ...w, selectedNode: w.graph.nodes[3] }), {
    viewport: "desktop",
    theme: "light",
  }),
  ready("tablet-dark", (w) => ({ ...w, selectedNode: w.graph.nodes[1] }), {
    viewport: "tablet",
    theme: "dark",
  }),
  ready(
    "mobile-light",
    (w) => ({
      ...w,
      selectedNode: null,
      graph: {
        ...w.graph,
        limitations: ["Use the accessible table fallback on narrow screens."],
      },
    }),
    { viewport: "mobile", theme: "light" },
  ),
  ready("long-content", (w) => ({
    ...w,
    selectedClaim: w.selectedClaim
      ? {
          ...w.selectedClaim,
          text: "A very long Claim label and explanation must wrap without covering adjacent controls. ".repeat(
            8,
          ),
        }
      : null,
  })),
  {
    id: "loading",
    title: "loading",
    description: "Loading contract state",
    viewport: "desktop",
    theme: "light",
    initialView: "graph",
    content: { state: "loading", label: "Loading evidence workspace" },
    pendingAction: null,
    mutationError: null,
  },
  {
    id: "empty",
    title: "empty",
    description: "Authorized empty state",
    viewport: "mobile",
    theme: "dark",
    initialView: "claims",
    content: {
      state: "empty",
      message: "No authorized evidence is available.",
    },
    pendingAction: null,
    mutationError: null,
  },
  {
    id: "load-error",
    title: "load error",
    description: "No-disclosure load error",
    viewport: "desktop",
    theme: "dark",
    initialView: "graph",
    content: {
      state: "error",
      error: error({ code: "NOT_FOUND", notFound: true, retryable: false }),
    },
    pendingAction: null,
    mutationError: null,
  },
] satisfies readonly EvidenceWorkspaceFixture[]

export const evidenceWorkspaceFixtureById = Object.fromEntries(
  evidenceWorkspaceFixtures.map((fixture) => [fixture.id, fixture]),
) as Readonly<Record<string, EvidenceWorkspaceFixture>>
