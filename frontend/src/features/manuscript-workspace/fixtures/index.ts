import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type {
  ManuscriptWorkspaceViewModel,
  RevisionFindingViewModel,
} from "../model"
import type { ManuscriptWorkspaceRouteView } from "../route-contract"
import type { ManuscriptWorkspaceEvent } from "../ui/contracts"

const id = (suffix: string) =>
  `00000000-0000-4000-8000-${suffix.padStart(12, "0")}`
const hash = (value: string) => value.repeat(64).slice(0, 64)
const allowed = (value: string[]) => new Set(value)
const capability = (value: boolean) => ({
  allowed: value,
  disabledReason: value ? null : "Not allowed by current server facts",
})

const base: ManuscriptWorkspaceViewModel = {
  projectId: id("1"),
  permissionsKnown: true,
  discoveryState: "ACTIVE",
  discoveryKnown: true,
  manuscript: {
    id: id("2"),
    projectId: id("1"),
    title: "Longitudinal evidence synthesis manuscript",
    currentVersionId: id("4"),
    status: "ACTIVE",
    knownStatus: true,
    lockVersion: 2,
    allowedActions: allowed(["manuscript.read", "manuscript.upload"]),
  },
  versions: [
    {
      id: id("3"),
      manuscriptId: id("2"),
      projectId: id("1"),
      versionNumber: 1,
      parentVersionId: null,
      artifactId: id("30"),
      versionType: "ORIGINAL",
      sourceTransformationId: null,
      status: "AVAILABLE",
      knownStatus: true,
      sourceHash: hash("a"),
      parseConfidence: "HIGH",
      unsupportedFeatures: [],
      invalidationReason: null,
      allowedActions: allowed([
        "manuscript_version.read",
        "manuscript_version.check",
        "manuscript_version.download",
      ]),
    },
    {
      id: id("4"),
      manuscriptId: id("2"),
      projectId: id("1"),
      versionNumber: 2,
      parentVersionId: id("3"),
      artifactId: id("31"),
      versionType: "AUTO_FIXED",
      sourceTransformationId: id("8"),
      status: "AVAILABLE",
      knownStatus: true,
      sourceHash: hash("b"),
      parseConfidence: "HIGH",
      unsupportedFeatures: [],
      invalidationReason: null,
      allowedActions: allowed([
        "manuscript_version.read",
        "manuscript_version.check",
        "manuscript_version.download",
      ]),
    },
  ],
  selectedVersion: {
    id: id("4"),
    manuscriptId: id("2"),
    projectId: id("1"),
    versionNumber: 2,
    parentVersionId: id("3"),
    artifactId: id("31"),
    versionType: "AUTO_FIXED",
    sourceTransformationId: id("8"),
    status: "AVAILABLE",
    knownStatus: true,
    sourceHash: hash("b"),
    parseConfidence: "HIGH",
    unsupportedFeatures: [],
    invalidationReason: null,
    allowedActions: allowed([
      "manuscript_version.read",
      "manuscript_version.check",
      "manuscript_version.download",
    ]),
  },
  checkRun: {
    id: id("5"),
    projectId: id("1"),
    versionId: id("4"),
    jobId: id("50"),
    sourceHash: hash("b"),
    status: "NEEDS_REVIEW",
    knownStatus: true,
    issueCount: 3,
    highIssueCount: 1,
    degradation: null,
    lowConfidence: false,
    errorCode: null,
    allowedActions: allowed(["manuscript_check_run.read"]),
  },
  issues: [
    {
      id: id("6"),
      projectId: id("1"),
      checkRunId: id("5"),
      versionId: id("4"),
      issueType: "SAMPLE_SIZE_MISMATCH",
      severity: "HIGH",
      locator: {
        schema: "reca.manuscript.locator.v1",
        paragraph: 12,
        text_hash: hash("c"),
      },
      excerpt: "The final sample included N = 184 participants.",
      reason: "The completed AnalysisRun reports N = 181.",
      suggestion: "Review the formal result before editing.",
      findingHash: hash("d"),
      confidence: "HIGH",
      deterministic: true,
      highRisk: true,
      autoFixable: false,
      status: "OPEN",
      knownStatus: true,
      lockVersion: 1,
      evidence: [
        {
          id: id("60"),
          type: "ANALYSIS_RESULT",
          objectType: "analysis_result",
          objectId: id("61"),
          excerpt: null,
          hash: hash("e"),
          metadata: { match: "EXACT_MISMATCH" },
          readScope: "AVAILABLE",
        },
      ],
      allowedActions: allowed([
        "manuscript_issue.read",
        "manuscript_issue.accept",
        "manuscript_issue.reject",
      ]),
    },
    {
      id: id("7"),
      projectId: id("1"),
      checkRunId: id("5"),
      versionId: id("4"),
      issueType: "PUNCTUATION_ISSUE",
      severity: "LOW",
      locator: { schema: "reca.manuscript.locator.v1", paragraph: 4 },
      excerpt: "Results  were stable.",
      reason: "Repeated whitespace.",
      suggestion: "Collapse repeated whitespace.",
      findingHash: hash("f"),
      confidence: "HIGH",
      deterministic: true,
      highRisk: false,
      autoFixable: true,
      status: "ACCEPTED",
      knownStatus: true,
      lockVersion: 2,
      evidence: [],
      allowedActions: allowed(["manuscript_issue.read"]),
    },
  ],
  selectedIssue: null,
  transformation: {
    id: id("8"),
    projectId: id("1"),
    inputVersionId: id("4"),
    issueIds: [id("7")],
    inputArtifactHash: hash("b"),
    preview: {
      changes: [
        { paragraph: 4, before: "Results  were", after: "Results were" },
      ],
    },
    previewHash: hash("1"),
    approvalId: id("80"),
    approvalStatus: "APPROVED",
    approvalKnown: true,
    approvalStale: false,
    outputVersionId: null,
    payloadHash: hash("2"),
    lockVersion: 4,
    jobId: null,
    errorCode: null,
    status: "APPROVED",
    knownStatus: true,
    allowedActions: allowed([
      "manuscript_fix_plan.read",
      "manuscript_fix_plan.execute",
    ]),
  },
  revisionAudit: {
    id: id("9"),
    projectId: id("1"),
    manuscriptId: id("2"),
    beforeVersionId: id("3"),
    afterVersionId: id("4"),
    beforeSourceHash: hash("a"),
    afterSourceHash: hash("b"),
    resultHash: hash("3"),
    findings: [
      {
        code: "CLAIM_NUMERIC_MISMATCH",
        knownCode: true,
        severity: "HIGH",
        locator: { paragraph: 12 },
        detail: { before: "N=181", after: "N=184" },
      },
    ],
    limitations: ["Complex semantic qualifier drift was not model-assisted."],
    jobId: id("90"),
    errorCode: null,
    status: "COMPLETED",
    knownStatus: true,
    allowedActions: allowed(["manuscript_revision_audit.read"]),
  },
  claim: {
    id: id("10"),
    projectId: id("1"),
    claimType: "STATISTICAL_RESULT",
    text: "The association was statistically significant.",
    normalizedClaim: "the association was statistically significant.",
    scopeStatement: "Within the analyzed sample",
    sourceObjectType: "manuscript_version",
    sourceObjectId: id("4"),
    sourceLocation: {
      schema: "reca.manuscript.locator.v1",
      paragraph: 12,
      text_hash: hash("4"),
    },
    sourceHash: hash("b"),
    textHash: hash("4"),
    status: "SUPPORTED",
    knownStatus: true,
    confidence: "HIGH",
    approvalId: null,
    approvalStatus: null,
    approvalKnown: true,
    approvalStale: false,
    lockVersion: 2,
    readOnly: false,
    allowedActions: allowed([
      "claim.read",
      "claim.update",
      "claim.request_confirmation",
    ]),
  },
  job: {
    id: id("50"),
    projectId: id("1"),
    resourceType: "manuscript_check_run",
    resourceId: id("5"),
    progress: 100,
    retryable: false,
    errorCode: null,
    status: "COMPLETED",
    knownStatus: true,
  },
  checkDefinitions: [
    "CITATION",
    "NUMERIC_CONSISTENCY",
    "CAUSALITY",
    "TERMINOLOGY",
    "BASIC_FORMAT",
  ].map((value) => ({
    value,
    label: value,
    allowed: true,
    disabledReason: null,
  })),
  revisionReferences: [
    {
      value: id("3"),
      label: "Version 1",
      sourceHash: hash("a"),
      versionNumber: 1,
      allowed: true,
      disabledReason: null,
    },
    {
      value: id("4"),
      label: "Version 2",
      sourceHash: hash("b"),
      versionNumber: 2,
      allowed: true,
      disabledReason: null,
    },
  ],
  claimTypeDefinitions: [
    "LITERATURE_SUMMARY",
    "CONSENSUS",
    "CONTROVERSY",
    "EVIDENCE_GAP",
    "TOPIC_RATIONALE",
    "DATA_DESCRIPTION",
    "STATISTICAL_RESULT",
    "INTERPRETATION",
    "MANUSCRIPT_STATEMENT",
  ].map((value) => ({
    value,
    label: value,
    allowed: true,
    disabledReason: null,
  })),
  claimStatusTransitions: [
    "NEEDS_EVIDENCE",
    "CONFLICTED",
    "INSUFFICIENT",
    "REJECTED",
  ].map((value) => ({
    value,
    label: value,
    allowed: true,
    disabledReason: null,
  })),
  degraded: false,
  capabilities: {
    permissionsKnown: true,
    uploadManuscript: capability(true),
    startCheck: capability(true),
    retryJob: capability(false),
    cancelJob: capability(false),
    acceptIssue: capability(false),
    rejectIssue: capability(false),
    createFixPlan: capability(true),
    previewFixPlan: capability(false),
    requestFixApproval: capability(false),
    executeFixPlan: capability(true),
    startRevisionAudit: capability(true),
    createClaim: capability(true),
    updateClaim: capability(true),
    requestClaimConfirmation: capability(true),
    downloadVersion: capability(true),
  },
}

export type ManuscriptWorkspaceFixture = {
  id: string
  viewport: "desktop" | "tablet" | "mobile"
  theme: "light" | "dark"
  content: Loadable<ManuscriptWorkspaceViewModel>
  pendingAction: ManuscriptWorkspaceEvent["action"] | null
  mutationError: UiErrorViewModel | null
  initialView: ManuscriptWorkspaceRouteView
}

const uiError = (value: Partial<UiErrorViewModel> = {}): UiErrorViewModel => ({
  title: "Request failed",
  message: "The server did not accept this operation.",
  code: "WORKSPACE_OPERATION_FAILED",
  requestId: "req-m6-fixture",
  retryable: false,
  forbidden: false,
  notFound: false,
  conflict: false,
  ...value,
})

const workspace = (
  patch: Partial<ManuscriptWorkspaceViewModel> = {},
): ManuscriptWorkspaceViewModel => ({
  ...base,
  ...patch,
  capabilities: { ...base.capabilities, ...patch.capabilities },
})

const ready = (
  fixtureId: string,
  patch: Partial<ManuscriptWorkspaceViewModel> = {},
  props: Partial<Omit<ManuscriptWorkspaceFixture, "id" | "content">> = {},
): ManuscriptWorkspaceFixture => ({
  id: fixtureId,
  viewport: fixtureId.includes("mobile")
    ? "mobile"
    : fixtureId.includes("tablet")
      ? "tablet"
      : "desktop",
  theme: fixtureId.includes("dark") ? "dark" : "light",
  content: { state: "ready", data: workspace(patch) },
  pendingAction: null,
  mutationError: null,
  initialView: "manuscript",
  ...props,
})

const loadError = (
  fixtureId: string,
  value: Partial<UiErrorViewModel> = {},
): ManuscriptWorkspaceFixture => ({
  id: fixtureId,
  viewport: "desktop",
  theme: "light",
  content: { state: "error", error: uiError(value) },
  pendingAction: null,
  mutationError: null,
  initialView: "manuscript",
})

const closedCapabilities = (upload = false) => ({
  ...base.capabilities,
  uploadManuscript: capability(upload),
  startCheck: capability(false),
  retryJob: capability(false),
  cancelJob: capability(false),
  acceptIssue: capability(false),
  rejectIssue: capability(false),
  createFixPlan: capability(false),
  previewFixPlan: capability(false),
  requestFixApproval: capability(false),
  executeFixPlan: capability(false),
  startRevisionAudit: capability(false),
  createClaim: capability(false),
  updateClaim: capability(false),
  requestClaimConfirmation: capability(false),
  downloadVersion: capability(false),
})

const noManuscript = (
  upload = true,
): Partial<ManuscriptWorkspaceViewModel> => ({
  discoveryState: "NONE",
  manuscript: null,
  versions: [],
  selectedVersion: null,
  checkRun: null,
  issues: [],
  selectedIssue: null,
  transformation: null,
  revisionAudit: null,
  claim: null,
  job: null,
  revisionReferences: [],
  claimStatusTransitions: [],
  capabilities: closedCapabilities(upload),
})

const checkFixture = (
  fixtureId: string,
  status: string,
  jobStatus: string,
  progress: number,
  retryable: boolean,
  errorCode: string | null = null,
) => {
  const cancellable = ["QUEUED", "RUNNING"].includes(jobStatus)
  return ready(
    fixtureId,
    {
      checkRun: base.checkRun && {
        ...base.checkRun,
        status,
        knownStatus: true,
        lowConfidence: status === "LOW_CONFIDENCE",
        errorCode,
        allowedActions: allowed(["manuscript_check_run.read"]),
      },
      job: base.job && {
        ...base.job,
        status: jobStatus,
        knownStatus: true,
        progress,
        retryable,
        errorCode,
      },
      capabilities: {
        ...base.capabilities,
        retryJob: capability(jobStatus === "FAILED" && retryable),
        cancelJob: capability(cancellable),
      },
    },
    { initialView: "checks" },
  )
}

const issueFixture = (
  fixtureId: string,
  issueType: string,
  severity: string,
  status: string,
  highRisk: boolean,
  autoFixable: boolean,
  excerpt = "A precisely located manuscript excerpt.",
) => {
  const actionable = ["OPEN", "ACKNOWLEDGED"].includes(status)
  const issue = {
    ...base.issues[0],
    id: id(`6${fixtureId.length}`),
    issueType,
    severity,
    status,
    knownStatus: true,
    highRisk,
    autoFixable: autoFixable && !highRisk,
    excerpt,
    evidence: [
      {
        ...base.issues[0].evidence[0],
        id: id(`7${fixtureId.length}`),
        readScope: "AVAILABLE" as const,
      },
    ],
    allowedActions: allowed(
      actionable
        ? [
            "manuscript_issue.read",
            "manuscript_issue.accept",
            "manuscript_issue.reject",
          ]
        : ["manuscript_issue.read"],
    ),
  }
  return ready(
    fixtureId,
    {
      issues: [issue],
      selectedIssue: issue,
      capabilities: {
        ...base.capabilities,
        acceptIssue: capability(actionable),
        rejectIssue: capability(actionable),
        createFixPlan: capability(status === "ACCEPTED" && issue.autoFixable),
      },
    },
    { initialView: "issues" },
  )
}

const evidenceFixture = (
  fixtureId: string,
  readScope: "AVAILABLE" | "DENIED" | "MISSING" | "STALE" | "UNKNOWN",
  excerpt: string | null,
  evidenceHash: string,
) => {
  const issue = {
    ...base.issues[0],
    evidence: [
      {
        ...base.issues[0].evidence[0],
        readScope,
        excerpt,
        hash: evidenceHash,
        metadata: {
          expectedHash: hash("e"),
          observedHash: evidenceHash,
        },
      },
    ],
  }
  return ready(
    fixtureId,
    { issues: [issue], selectedIssue: issue },
    { initialView: "issues" },
  )
}

const transformationFixture = (
  fixtureId: string,
  status: string,
  approvalStatus: string | null,
  approvalStale: boolean,
  jobStatus: string | null,
  outputVersionId: string | null,
  errorCode: string | null = null,
) => {
  const pending = ["QUEUED", "RUNNING"].includes(status)
  return ready(
    fixtureId,
    {
      transformation: base.transformation && {
        ...base.transformation,
        status,
        approvalStatus,
        approvalStale,
        outputVersionId,
        jobId: jobStatus ? id("81") : null,
        errorCode,
        allowedActions: allowed(
          fixtureId === "fix-preview"
            ? [
                "manuscript_fix_plan.read",
                "manuscript_fix_plan.request_approval",
              ]
            : status === "DRAFT"
              ? ["manuscript_fix_plan.read", "manuscript_fix_plan.preview"]
              : approvalStatus === "APPROVED" && !approvalStale
                ? ["manuscript_fix_plan.read", "manuscript_fix_plan.execute"]
                : ["manuscript_fix_plan.read"],
        ),
      },
      job: jobStatus
        ? {
            ...base.job,
            id: id("81"),
            projectId: base.projectId,
            resourceId: id("8"),
            resourceType: "manuscript_transformation",
            status: jobStatus,
            knownStatus: true,
            progress:
              jobStatus === "COMPLETED"
                ? 100
                : jobStatus === "RUNNING"
                  ? 55
                  : 0,
            retryable: jobStatus === "FAILED",
            errorCode,
          }
        : null,
      capabilities: {
        ...base.capabilities,
        previewFixPlan: capability(
          status === "DRAFT" && fixtureId !== "fix-preview",
        ),
        requestFixApproval: capability(fixtureId === "fix-preview"),
        executeFixPlan: capability(
          approvalStatus === "APPROVED" && !approvalStale && !pending,
        ),
      },
    },
    { initialView: "fixes" },
  )
}

const auditFixture = (
  fixtureId: string,
  status: string,
  findings: readonly RevisionFindingViewModel[],
  limitations: readonly string[],
  jobStatus: string,
  errorCode: string | null = null,
) =>
  ready(
    fixtureId,
    {
      revisionAudit: base.revisionAudit && {
        ...base.revisionAudit,
        status,
        findings,
        limitations,
        errorCode,
        resultHash: status === "COMPLETED" ? hash("3") : null,
      },
      job: {
        ...base.job,
        id: id("90"),
        projectId: base.projectId,
        resourceId: id("9"),
        resourceType: "audit_result",
        status: jobStatus,
        knownStatus: true,
        progress:
          jobStatus === "COMPLETED" ? 100 : jobStatus === "RUNNING" ? 45 : 0,
        retryable: jobStatus === "FAILED",
        errorCode,
      },
      capabilities: {
        ...base.capabilities,
        retryJob: capability(jobStatus === "FAILED"),
        cancelJob: capability(["QUEUED", "RUNNING"].includes(jobStatus)),
      },
    },
    { initialView: "audits" },
  )

const claimFixture = (
  fixtureId: string,
  status: string,
  approvalStatus: string | null,
  readOnly: boolean,
  approvalStale = false,
) => {
  const canUpdate =
    !readOnly && !["CONFIRMED", "REJECTED", "INVALIDATED"].includes(status)
  const canConfirm = status === "SUPPORTED" && approvalStatus === null
  return ready(
    fixtureId,
    {
      claim: base.claim && {
        ...base.claim,
        status,
        approvalId: approvalStatus ? id("101") : null,
        approvalStatus,
        approvalStale,
        readOnly,
        allowedActions: allowed([
          "claim.read",
          ...(canUpdate ? ["claim.update"] : []),
          ...(canConfirm ? ["claim.request_confirmation"] : []),
        ]),
      },
      claimStatusTransitions: canUpdate
        ? [
            "NEEDS_EVIDENCE",
            "SUPPORTED",
            "CONFLICTED",
            "INSUFFICIENT",
            "REJECTED",
          ]
            .filter((value) => value !== status)
            .map((value) => ({
              value,
              label: value,
              allowed: true,
              disabledReason: null,
            }))
        : [],
      capabilities: {
        ...base.capabilities,
        updateClaim: capability(canUpdate),
        requestClaimConfirmation: capability(canConfirm),
      },
    },
    { initialView: "claims" },
  )
}

const loading: ManuscriptWorkspaceFixture = {
  id: "loading",
  viewport: "desktop",
  theme: "light",
  content: { state: "loading", label: "Loading manuscript workspace" },
  pendingAction: null,
  mutationError: null,
  initialView: "manuscript",
}

const empty: ManuscriptWorkspaceFixture = {
  id: "empty",
  viewport: "desktop",
  theme: "light",
  content: { state: "empty", message: "No authorized manuscript facts." },
  pendingAction: null,
  mutationError: null,
  initialView: "manuscript",
}

export const manuscriptWorkspaceFixtures = [
  loading,
  empty,
  loadError("error"),
  loadError("load-error", { code: "WORKSPACE_LOAD_FAILED", retryable: true }),
  loadError("forbidden", {
    code: "RESOURCE_NOT_FOUND",
    retryable: false,
    forbidden: true,
    notFound: true,
  }),
  ready(
    "mutation-conflict",
    {},
    {
      mutationError: uiError({ code: "PRECONDITION_FAILED", conflict: true }),
    },
  ),
  ready(
    "mutation-validation-error",
    {},
    {
      mutationError: uiError({ code: "VALIDATION_ERROR" }),
    },
  ),
  ready(
    "mutation-forbidden",
    {},
    {
      mutationError: uiError({
        code: "RESOURCE_NOT_FOUND",
        forbidden: true,
        notFound: true,
      }),
    },
  ),
  ready(
    "mutation-retryable-error",
    {},
    {
      mutationError: uiError({
        code: "EXTERNAL_CAPABILITY_UNAVAILABLE",
        retryable: true,
      }),
    },
  ),
  ready(
    "mutation-non-retryable-error",
    {},
    {
      mutationError: uiError({ code: "UNSUPPORTED_DOCX", retryable: false }),
    },
  ),
  ready("no-manuscript", noManuscript()),
  ready("upload-available", noManuscript()),
  ready("upload-forbidden", noManuscript(false)),
  ready("upload-pending", noManuscript(), {
    pendingAction: "upload-manuscript",
  }),
  ready("invalid-docx", noManuscript(), {
    mutationError: uiError({ code: "UNSUPPORTED_DOCX", retryable: false }),
  }),
  ready("original-ready", {
    versions: [base.versions[0]],
    selectedVersion: base.versions[0],
    revisionReferences: [base.revisionReferences[0]],
  }),
  ready("multiple-versions"),
  ready("archived-manuscript", {
    discoveryState: "ARCHIVED",
    manuscript: base.manuscript && { ...base.manuscript, status: "ARCHIVED" },
    selectedVersion: null,
    capabilities: closedCapabilities(true),
  }),
  ready("invalidated-manuscript", {
    discoveryState: "INVALIDATED",
    manuscript: base.manuscript && {
      ...base.manuscript,
      status: "INVALIDATED",
    },
    selectedVersion: null,
    capabilities: closedCapabilities(true),
  }),
  ready("long-filename-hash-title", {
    manuscript: base.manuscript && {
      ...base.manuscript,
      title:
        "A very long manuscript title with DOI 10.1234/example.2026.0000000000000000000000000000000000000000000000000000000000000000 and an_unbroken_filename_that_must_wrap_without_disclosing_private_content.docx",
    },
  }),
  ready("unknown-version-status", {
    selectedVersion: base.selectedVersion && {
      ...base.selectedVersion,
      status: "FUTURE_VERSION_STATE",
      knownStatus: false,
      allowedActions: allowed([]),
    },
    capabilities: {
      ...base.capabilities,
      startCheck: capability(false),
      downloadVersion: capability(false),
    },
  }),
  checkFixture("check-queued", "QUEUED", "QUEUED", 0, false),
  checkFixture("check-parsing", "PARSING", "RUNNING", 18, false),
  checkFixture("check-rules", "CHECKING_RULES", "RUNNING", 48, false),
  checkFixture(
    "check-project-consistency",
    "CHECKING_PROJECT_CONSISTENCY",
    "RUNNING",
    72,
    false,
  ),
  checkFixture("check-needs-review", "NEEDS_REVIEW", "COMPLETED", 100, false),
  checkFixture("check-completed", "COMPLETED", "COMPLETED", 100, false),
  checkFixture(
    "check-failed-retryable",
    "FAILED",
    "FAILED",
    62,
    true,
    "WORKER_TRANSIENT_FAILURE",
  ),
  checkFixture(
    "check-failed-non-retryable",
    "FAILED",
    "FAILED",
    62,
    false,
    "UNSUPPORTED_DOCX",
  ),
  checkFixture(
    "check-low-confidence",
    "LOW_CONFIDENCE",
    "COMPLETED",
    100,
    false,
    "LOW_CONFIDENCE",
  ),
  checkFixture(
    "check-cancelled",
    "CANCELLED",
    "CANCELLED",
    30,
    false,
    "CANCELLED",
  ),
  ready(
    "check-pending",
    {},
    { pendingAction: "start-check", initialView: "checks" },
  ),
  issueFixture(
    "issues-mixed-severity",
    "SAMPLE_SIZE_MISMATCH",
    "HIGH",
    "OPEN",
    true,
    false,
  ),
  issueFixture(
    "citation",
    "IN_TEXT_CITATION_MISSING_REFERENCE",
    "MEDIUM",
    "OPEN",
    true,
    false,
  ),
  issueFixture(
    "numeric-mismatch",
    "STATISTIC_MISMATCH",
    "HIGH",
    "OPEN",
    true,
    false,
  ),
  issueFixture("causal-risk", "CAUSAL_OVERCLAIM", "HIGH", "OPEN", true, false),
  issueFixture(
    "terminology",
    "TERMINOLOGY_INCONSISTENCY",
    "LOW",
    "OPEN",
    false,
    false,
  ),
  issueFixture(
    "format-only",
    "PUNCTUATION_ISSUE",
    "LOW",
    "ACCEPTED",
    false,
    true,
  ),
  issueFixture(
    "resolved",
    "PUNCTUATION_ISSUE",
    "LOW",
    "RESOLVED",
    false,
    false,
  ),
  issueFixture(
    "rejected",
    "TERMINOLOGY_INCONSISTENCY",
    "LOW",
    "REJECTED",
    false,
    false,
  ),
  issueFixture(
    "invalidated",
    "CITATION_METADATA_MISMATCH",
    "MEDIUM",
    "INVALIDATED",
    true,
    false,
  ),
  issueFixture(
    "long-excerpt",
    "POPULATION_OVERGENERALIZATION",
    "HIGH",
    "OPEN",
    true,
    false,
    "A ".repeat(800),
  ),
  ready(
    "accept-pending",
    {},
    { pendingAction: "accept-issue", initialView: "issues" },
  ),
  ready(
    "reject-pending",
    {},
    { pendingAction: "reject-issue", initialView: "issues" },
  ),
  evidenceFixture("evidence-available", "AVAILABLE", "N = 181", hash("e")),
  evidenceFixture("evidence-denied", "DENIED", null, hash("e")),
  evidenceFixture("evidence-missing", "MISSING", null, hash("0")),
  evidenceFixture(
    "evidence-stale",
    "STALE",
    "Previously authorized excerpt",
    hash("e"),
  ),
  evidenceFixture("evidence-hash-mismatch", "STALE", null, hash("9")),
  ready("read-only", {
    capabilities: {
      ...base.capabilities,
      updateClaim: capability(false),
      executeFixPlan: capability(false),
    },
  }),
  ready("permissions-unknown", {
    ...noManuscript(false),
    permissionsKnown: false,
    capabilities: { ...closedCapabilities(false), permissionsKnown: false },
    checkDefinitions: base.checkDefinitions.map((item) => ({
      ...item,
      allowed: false,
      disabledReason: "Permissions are unknown",
    })),
    claimTypeDefinitions: base.claimTypeDefinitions.map((item) => ({
      ...item,
      allowed: false,
      disabledReason: "Permissions are unknown",
    })),
  }),
  ready("degraded-unknown", {
    discoveryState: "FUTURE_DISCOVERY_STATE",
    discoveryKnown: false,
    degraded: true,
    checkRun: base.checkRun && {
      ...base.checkRun,
      status: "FUTURE_CHECK_STATE",
      knownStatus: false,
      allowedActions: allowed([]),
    },
    capabilities: closedCapabilities(false),
  }),
  transformationFixture("fix-preview", "DRAFT", null, false, null, null),
  transformationFixture(
    "approval-pending",
    "NEEDS_APPROVAL",
    "PENDING",
    false,
    null,
    null,
  ),
  transformationFixture(
    "approval-approved",
    "APPROVED",
    "APPROVED",
    false,
    null,
    null,
  ),
  transformationFixture(
    "approval-stale",
    "APPROVED",
    "APPROVED",
    true,
    null,
    null,
  ),
  transformationFixture(
    "approval-rejected",
    "REJECTED",
    "REJECTED",
    false,
    null,
    null,
  ),
  transformationFixture(
    "execute-pending",
    "RUNNING",
    "APPROVED",
    false,
    "RUNNING",
    null,
  ),
  transformationFixture(
    "execute-failed",
    "FAILED",
    "APPROVED",
    false,
    "FAILED",
    null,
    "FIX_EXECUTION_FAILED",
  ),
  transformationFixture(
    "execute-success-new-version",
    "COMPLETED",
    "APPROVED",
    false,
    "COMPLETED",
    id("11"),
  ),
  ready(
    "preview-pending",
    {},
    { pendingAction: "preview-fix-plan", initialView: "fixes" },
  ),
  ready(
    "approval-request-pending",
    {},
    { pendingAction: "request-fix-approval", initialView: "fixes" },
  ),
  ready(
    "execute-action-pending",
    {},
    { pendingAction: "execute-fix-plan", initialView: "fixes" },
  ),
  auditFixture("revision-audit-running", "RUNNING", [], [], "RUNNING"),
  auditFixture(
    "revision-audit-completed-mixed",
    "COMPLETED",
    [
      ...base.revisionAudit!.findings,
      {
        code: "CLAIM_CAUSAL_OVERSTATEMENT",
        knownCode: true,
        severity: "HIGH",
        locator: { paragraph: 4 },
        detail: { before: "associated", after: "caused" },
      },
    ],
    [],
    "COMPLETED",
  ),
  auditFixture(
    "revision-audit-insufficient",
    "COMPLETED",
    [],
    ["No stable source locator was available for one changed paragraph."],
    "COMPLETED",
  ),
  auditFixture(
    "revision-audit-failed",
    "FAILED",
    [],
    ["Audit output is unavailable."],
    "FAILED",
    "AUDIT_INPUT_STALE",
  ),
  ready(
    "audit-pending",
    {},
    { pendingAction: "start-revision-audit", initialView: "audits" },
  ),
  claimFixture("claim-draft", "DRAFT", null, false),
  claimFixture("claim-needs-evidence", "NEEDS_EVIDENCE", null, false),
  claimFixture("claim-supported", "SUPPORTED", null, false),
  claimFixture("claim-conflicted", "CONFLICTED", null, false),
  claimFixture("claim-insufficient", "INSUFFICIENT", null, false),
  claimFixture("claim-approval-pending", "SUPPORTED", "PENDING", false),
  claimFixture("claim-confirmed", "CONFIRMED", "APPROVED", true),
  claimFixture("claim-read-only", "REJECTED", null, true),
  ready(
    "claim-permissions-unknown",
    {
      permissionsKnown: false,
      claim: base.claim && {
        ...base.claim,
        readOnly: true,
        allowedActions: allowed([]),
      },
      claimStatusTransitions: [],
      capabilities: { ...closedCapabilities(false), permissionsKnown: false },
    },
    { initialView: "claims" },
  ),
  ready(
    "claim-create-pending",
    {},
    { pendingAction: "create-claim", initialView: "claims" },
  ),
  ready(
    "claim-update-pending",
    {},
    { pendingAction: "update-claim", initialView: "claims" },
  ),
  ready(
    "claim-confirmation-pending",
    {},
    { pendingAction: "request-claim-confirmation", initialView: "claims" },
  ),
  ready("desktop-light"),
  ready("desktop-dark"),
  ready("tablet-light"),
  ready("tablet-dark"),
  ready("mobile-light"),
  ready("mobile-dark"),
  ready("long-content", {
    manuscript: base.manuscript && {
      ...base.manuscript,
      title: "Long title ".repeat(80),
    },
    issues: base.issues.map((issue) => ({
      ...issue,
      excerpt: "Long scientific excerpt ".repeat(120),
    })),
  }),
] satisfies readonly ManuscriptWorkspaceFixture[]
