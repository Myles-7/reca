import type {
  ApprovalViewModel,
  ArtifactViewModel,
  AuditViewModel,
  JobViewModel,
  MemberViewModel,
  OverviewViewModel,
  ProjectViewModel,
  UiErrorViewModel,
  WorkspacePermissions,
} from "../model"
import type {
  ApprovalsPanelProps,
  ArtifactsPanelProps,
  AuditPanelProps,
  JobsPanelProps,
  MembersPanelProps,
  OverviewPanelProps,
} from "../ui/contracts"
import type { ProjectWorkspaceDesignFixture } from "./types"

const noRetry = () => undefined
const noUpload = (_file: File) => undefined
const noDownload = (_artifactId: string) => undefined
const noMemberAdd: MembersPanelProps["onAddMember"] = () => undefined
const noRoleChange: MembersPanelProps["onChangeRole"] = () => undefined
const noOwnershipTransfer: MembersPanelProps["onTransferOwnership"] = () =>
  undefined
const noMemberRemove: MembersPanelProps["onRemoveMember"] = () => undefined
const noJobAction: JobsPanelProps["onAction"] = () => undefined
const noApprovalAction: ApprovalsPanelProps["onAction"] = () => undefined

const project = {
  id: "design-project",
  ownerId: "design-owner",
  name: "Evidence synthesis workspace",
  description: "A typed design surface backed only by formal UI contracts.",
  discipline: "Medicine",
  researchDirection: "Systematic review of reproducible interventions",
  stage: "INTENT",
  status: "ACTIVE",
  knownStatus: true,
  permissionsKnown: true,
  allowedActions: new Set(["project.read", "project.update", "project.delete"]),
  type: "RESEARCH",
  updatedAt: "Aug 1, 2026, 10:30 AM",
  lockVersion: 4,
  canUpdate: true,
  canDelete: true,
} satisfies ProjectViewModel

const permissions = {
  permissionsKnown: true,
  actions: new Set([
    "project.manage_members",
    "artifact.upload",
    "job.retry",
    "job.cancel",
  ]),
  canManageMembers: true,
  canUploadArtifact: true,
  canRetryJob: true,
  canCancelJob: true,
} satisfies WorkspacePermissions

const overviewData = {
  stage: "INTENT",
  foundationCounts: [
    { label: "Members", value: 4 },
    { label: "Artifacts", value: 12 },
    { label: "Active jobs", value: 1 },
    { label: "Pending approvals", value: 1 },
    { label: "Audit events", value: 48 },
  ],
  capabilities: [
    {
      key: "research_question",
      label: "Research question",
      availability: "AVAILABLE",
      value: 1,
      tone: "success",
    },
    {
      key: "literature",
      label: "Literature",
      availability: "NOT_AVAILABLE",
      value: null,
      tone: "neutral",
    },
    {
      key: "evidence",
      label: "Evidence",
      availability: "DEGRADED",
      value: null,
      tone: "degraded",
    },
  ],
  researchQuestion: null,
  evidenceCompleteness: null,
  pendingActionCount: 1,
} satisfies OverviewViewModel

const members = [
  {
    id: "member-owner",
    userId: "design-owner",
    displayName: "Dr. Morgan Chen",
    email: "morgan@example.test",
    role: "OWNER",
    joinedAt: "Jul 28, 2026, 9:00 AM",
    removed: false,
    isCurrentUser: true,
    isOwner: true,
  },
  {
    id: "member-reviewer",
    userId: "design-reviewer",
    displayName: "Alex Rivera",
    email: "alex@example.test",
    role: "REVIEWER",
    joinedAt: "Jul 30, 2026, 2:15 PM",
    removed: false,
    isCurrentUser: false,
    isOwner: false,
  },
] satisfies MemberViewModel[]

const artifacts = [
  {
    id: "artifact-protocol",
    filename: "review-protocol.pdf",
    kind: "PDF_DOCUMENT",
    origin: "ORIGINAL",
    status: "AVAILABLE",
    size: "2.4 MB",
    sha256: "62f9c84f9a14f3f7d4021080dca2a68e4b13a432b91dc72ba52358be04034c80",
    createdAt: "Jul 31, 2026, 4:20 PM",
    canDownload: true,
    immutable: true,
    tone: "neutral",
  },
] satisfies ArtifactViewModel[]

const jobs = [
  {
    id: "job-parse",
    taskLabel: "DOCUMENT PARSE",
    status: "RUNNING",
    progress: 64,
    step: "EXTRACTING SECTIONS",
    retryable: false,
    retryCount: 0,
    maxRetries: 3,
    error: null,
    resultUrl: null,
    createdAt: "Aug 1, 2026, 10:10 AM",
    active: true,
    tone: "info",
  },
] satisfies JobViewModel[]

const approvals = [
  {
    id: "approval-question",
    type: "RESEARCH QUESTION CONFIRMATION",
    target: "ResearchQuestion · rq-design-1",
    status: "PENDING",
    requester: "USER · design-owner",
    requestedAt: "Aug 1, 2026, 10:25 AM",
    expiresAt: null,
    payloadHash:
      "de9b372ec84388a2fb26f0b744b7c0b7b77a733f0e7aa91ecf32ea1001cc8794",
    allowedActions: new Set([
      "approval.approve",
      "approval.reject",
      "approval.cancel",
    ]),
    stale: false,
    tone: "info",
  },
] satisfies ApprovalViewModel[]

const audit = [
  {
    id: "audit-created",
    actor: "Dr. Morgan Chen",
    action: "PROJECT CREATED",
    target: "Evidence synthesis workspace",
    occurredAt: "Jul 28, 2026, 9:00 AM",
    requestId: "request-design-001",
    outcome: "SUCCEEDED",
    summary: null,
    tone: "success",
  },
] satisfies AuditViewModel[]

const requestError = {
  title: "Request failed",
  message: "The design fixture simulates a recoverable service error.",
  code: "DESIGN_FIXTURE_ERROR",
  requestId: "request-design-error",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const forbiddenError = {
  title: "Access denied",
  message: "You do not have permission to view this project resource.",
  code: "PROJECT_ACCESS_DENIED",
  requestId: "request-design-forbidden",
  retryable: false,
  forbidden: true,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const readyPanels = {
  overview: {
    content: { state: "ready", data: overviewData },
    loadError: null,
    onRetry: noRetry,
  } satisfies OverviewPanelProps,
  members: {
    content: { state: "ready", data: { members, permissions } },
    submitting: false,
    loadError: null,
    mutationError: null,
    onRetry: noRetry,
    onAddMember: noMemberAdd,
    onChangeRole: noRoleChange,
    onTransferOwnership: noOwnershipTransfer,
    onRemoveMember: noMemberRemove,
  } satisfies MembersPanelProps,
  artifacts: {
    content: { state: "ready", data: artifacts },
    permissionsKnown: true,
    canUpload: true,
    uploading: false,
    loadError: null,
    mutationError: null,
    onRetry: noRetry,
    onUpload: noUpload,
    onDownload: noDownload,
  } satisfies ArtifactsPanelProps,
  jobs: {
    content: { state: "ready", data: jobs },
    permissions,
    streamState: "connected",
    submittingJobId: null,
    loadError: null,
    mutationError: null,
    onRetryLoad: noRetry,
    onAction: noJobAction,
  } satisfies JobsPanelProps,
  approvals: {
    content: { state: "ready", data: approvals },
    submittingApprovalId: null,
    loadError: null,
    mutationError: null,
    onRetry: noRetry,
    onAction: noApprovalAction,
  } satisfies ApprovalsPanelProps,
  audit: {
    content: { state: "ready", data: audit },
    loadError: null,
    onRetry: noRetry,
  } satisfies AuditPanelProps,
}

export const readyFixture = {
  id: "ready",
  label: "Ready",
  behavior:
    "Renders server-projected project panels with currently allowed actions.",
  project,
  ...readyPanels,
} satisfies ProjectWorkspaceDesignFixture

export const loadingFixture = {
  ...readyFixture,
  id: "loading",
  label: "Loading",
  behavior: "Keeps every project panel stable while its projection loads.",
  overview: {
    ...readyFixture.overview,
    content: { state: "loading", label: "Loading project overview" },
  },
  members: {
    ...readyFixture.members,
    content: { state: "loading", label: "Loading members" },
  },
  artifacts: {
    ...readyFixture.artifacts,
    content: { state: "loading", label: "Loading artifacts" },
  },
  jobs: {
    ...readyFixture.jobs,
    content: { state: "loading", label: "Loading jobs" },
    streamState: "idle",
  },
  approvals: {
    ...readyFixture.approvals,
    content: { state: "loading", label: "Loading approvals" },
  },
  audit: {
    ...readyFixture.audit,
    content: { state: "loading", label: "Loading audit history" },
  },
} satisfies ProjectWorkspaceDesignFixture

export const emptyFixture = {
  ...readyFixture,
  id: "empty",
  label: "Empty",
  behavior:
    "Shows explicit empty panel states without inventing domain objects.",
  overview: {
    ...readyFixture.overview,
    content: { state: "empty", message: "No overview is available." },
  },
  members: {
    ...readyFixture.members,
    content: { state: "empty", message: "No project members." },
  },
  artifacts: {
    ...readyFixture.artifacts,
    content: { state: "empty", message: "No artifacts have been uploaded." },
  },
  jobs: {
    ...readyFixture.jobs,
    content: {
      state: "empty",
      message: "No jobs have been created by M1 domain services.",
    },
    streamState: "idle",
  },
  approvals: {
    ...readyFixture.approvals,
    content: {
      state: "empty",
      message: "No approval requests require attention.",
    },
  },
  audit: {
    ...readyFixture.audit,
    content: { state: "empty", message: "No audit events are visible." },
  },
} satisfies ProjectWorkspaceDesignFixture

export const errorFixture = {
  ...readyFixture,
  id: "error",
  label: "Error",
  behavior: "Shows retryable load failures across the workspace panels.",
  overview: {
    ...readyFixture.overview,
    content: { state: "error", error: requestError },
  },
  members: {
    ...readyFixture.members,
    content: { state: "error", error: requestError },
  },
  artifacts: {
    ...readyFixture.artifacts,
    content: { state: "error", error: requestError },
  },
  jobs: {
    ...readyFixture.jobs,
    content: { state: "error", error: requestError },
    streamState: "degraded",
  },
  approvals: {
    ...readyFixture.approvals,
    content: { state: "error", error: requestError },
  },
  audit: {
    ...readyFixture.audit,
    content: { state: "error", error: requestError },
  },
} satisfies ProjectWorkspaceDesignFixture

export const forbiddenFixture = {
  ...errorFixture,
  id: "forbidden",
  label: "Forbidden",
  behavior: "Shows access denial and clears action permission projections.",
  overview: {
    ...errorFixture.overview,
    content: { state: "error", error: forbiddenError },
  },
  members: {
    ...errorFixture.members,
    content: { state: "error", error: forbiddenError },
  },
  artifacts: {
    ...errorFixture.artifacts,
    content: { state: "error", error: forbiddenError },
    permissionsKnown: false,
    canUpload: false,
  },
  jobs: {
    ...errorFixture.jobs,
    content: { state: "error", error: forbiddenError },
    permissions: null,
  },
  approvals: {
    ...errorFixture.approvals,
    content: { state: "error", error: forbiddenError },
  },
  audit: {
    ...errorFixture.audit,
    content: { state: "error", error: forbiddenError },
  },
} satisfies ProjectWorkspaceDesignFixture

export const degradedFixture = {
  ...readyFixture,
  id: "degraded",
  label: "Degraded",
  behavior: "Fails closed for unknown Artifact and Job lifecycle values.",
  artifacts: {
    ...readyFixture.artifacts,
    content: {
      state: "ready",
      data: [
        {
          ...artifacts[0],
          id: "artifact-unknown",
          filename: "future-format.bin",
          status: "FUTURE_ARTIFACT_STATE",
          canDownload: false,
          tone: "warning",
        },
      ],
    },
  },
  jobs: {
    ...readyFixture.jobs,
    content: {
      state: "ready",
      data: [
        {
          ...jobs[0],
          id: "job-unknown",
          status: "FUTURE_JOB_STATE",
          retryable: false,
          active: false,
          tone: "degraded",
        },
      ],
    },
    streamState: "degraded",
  },
} satisfies ProjectWorkspaceDesignFixture

export const longContentFixture = {
  ...readyFixture,
  id: "long-content",
  label: "Long content",
  behavior:
    "Exercises wrapping for long project, member, artifact, and audit metadata.",
  project: {
    ...project,
    name: "A multi-institutional evidence synthesis workspace with deliberately long project naming",
    description:
      "This description intentionally exercises wrapping across narrow and wide layouts while preserving the complete scientific context supplied by the design fixture.",
  },
  members: {
    ...readyFixture.members,
    content: {
      state: "ready",
      data: {
        permissions,
        members: [
          {
            ...members[1],
            displayName:
              "Professor Alexandra-Marguerite Rivera-Santos the Third",
            email:
              "alexandra.rivera-santos.long-address@international-research-consortium.example.test",
          },
        ],
      },
    },
  },
  artifacts: {
    ...readyFixture.artifacts,
    content: {
      state: "ready",
      data: [
        {
          ...artifacts[0],
          filename:
            "systematic-review-protocol-with-registration-amendments-and-complete-supplementary-material.pdf",
        },
      ],
    },
  },
  audit: {
    ...readyFixture.audit,
    content: {
      state: "ready",
      data: [
        {
          ...audit[0],
          action:
            "RESEARCH QUESTION VERSION SUBMITTED FOR MULTI-STAGE FORMAL APPROVAL",
          target:
            "Comparative effectiveness of reproducible intervention strategies across diverse clinical populations",
        },
      ],
    },
  },
} satisfies ProjectWorkspaceDesignFixture

export const pendingApprovalFixture = {
  ...readyFixture,
  id: "pending-approval",
  label: "Pending approval",
  behavior:
    "Disables duplicate approval actions while an intent is submitting.",
  approvals: {
    ...readyFixture.approvals,
    submittingApprovalId: approvals[0].id,
  },
} satisfies ProjectWorkspaceDesignFixture

export const failedRetryableJobFixture = {
  ...readyFixture,
  id: "failed-retryable-job",
  label: "Failed retryable Job",
  behavior: "Enables retry only for a failed Job projected as retryable.",
  jobs: {
    ...readyFixture.jobs,
    content: {
      state: "ready",
      data: [
        {
          ...jobs[0],
          id: "job-failed-retryable",
          status: "FAILED",
          progress: 72,
          step: "PERSISTING PARSE OUTPUT",
          retryable: true,
          retryCount: 1,
          error: "The service marked this failed Job as safe to retry.",
          active: false,
          tone: "danger",
        },
      ],
    },
  },
} satisfies ProjectWorkspaceDesignFixture

export const activeCancelableJobFixture = {
  ...readyFixture,
  id: "active-cancelable-job",
  label: "Active cancelable Job",
  behavior:
    "Enables cancel only for an active Job with mapped cancel permission.",
  jobs: {
    ...readyFixture.jobs,
    content: {
      state: "ready",
      data: [
        {
          ...jobs[0],
          id: "job-active-cancelable",
          status: "RUNNING",
          active: true,
          retryable: false,
        },
      ],
    },
  },
} satisfies ProjectWorkspaceDesignFixture

export const staleNoActionsApprovalFixture = {
  ...readyFixture,
  id: "stale-no-actions-approval",
  label: "Stale approval without actions",
  behavior:
    "Shows stale approval provenance while every action remains disabled.",
  approvals: {
    ...readyFixture.approvals,
    content: {
      state: "ready",
      data: [
        {
          ...approvals[0],
          id: "approval-stale-no-actions",
          status: "SUPERSEDED",
          allowedActions: new Set<string>(),
          stale: true,
          tone: "warning",
        },
      ],
    },
  },
} satisfies ProjectWorkspaceDesignFixture

export const projectUnknownStatusFixture = {
  ...readyFixture,
  id: "project-status-unknown",
  label: "Project status unknown",
  behavior:
    "Shows the raw project status while lifecycle and update actions fail closed.",
  project: {
    ...project,
    status: "FUTURE_PROJECT_STATE",
    knownStatus: false,
    allowedActions: new Set<string>(),
    canUpdate: false,
    canDelete: false,
  },
} satisfies ProjectWorkspaceDesignFixture

export const projectPermissionsUnknownFixture = {
  ...readyFixture,
  id: "project-permissions-unknown",
  label: "Project permissions unknown",
  behavior:
    "Preserves member and Artifact data while all writes remain disabled.",
  members: {
    ...readyFixture.members,
    content: {
      state: "ready",
      data: {
        members,
        permissions: {
          permissionsKnown: false,
          actions: new Set<string>(),
          canManageMembers: false,
          canUploadArtifact: false,
          canRetryJob: false,
          canCancelJob: false,
        },
      },
    },
  },
  artifacts: {
    ...readyFixture.artifacts,
    permissionsKnown: false,
    canUpload: false,
  },
} satisfies ProjectWorkspaceDesignFixture

export const projectWorkspaceFixtures = [
  readyFixture,
  loadingFixture,
  emptyFixture,
  errorFixture,
  forbiddenFixture,
  degradedFixture,
  longContentFixture,
  pendingApprovalFixture,
  failedRetryableJobFixture,
  activeCancelableJobFixture,
  staleNoActionsApprovalFixture,
  projectUnknownStatusFixture,
  projectPermissionsUnknownFixture,
] as const satisfies readonly ProjectWorkspaceDesignFixture[]

export type { ProjectWorkspaceDesignFixture } from "./types"
