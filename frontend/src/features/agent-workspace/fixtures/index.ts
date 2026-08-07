import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { AgentWorkspaceViewModel, ToolCallViewModel } from "../model"
import type { AgentWorkspaceEvent } from "../ui/contracts"

const id = (suffix: string) =>
  `00000000-0000-4000-8000-${suffix.padStart(12, "0")}`
const action = (allowed: boolean, reason: string | null = null) => ({
  allowed,
  reason,
})

const tool = (patch: Partial<ToolCallViewModel> = {}): ToolCallViewModel => ({
  id: id("20"),
  runId: id("10"),
  name: "get_project_state",
  version: "1.0",
  status: "COMPLETED",
  knownStatus: true,
  category: "READ_ONLY",
  confirmation: "NONE",
  factKind: "SYSTEM_FACT",
  inputSummary: "Read the current project state.",
  outputSummary: "Project state is available.",
  approval: null,
  job: null,
  sourceLink: null,
  retryable: false,
  errorCode: null,
  allowedActions: new Set(),
  disabledReason: null,
  ...patch,
})

const base = (): AgentWorkspaceViewModel => ({
  projectId: id("1"),
  projectName: "M8 research project",
  projectStage: "EVIDENCE",
  permissionsKnown: true,
  readOnly: false,
  routeFallback: false,
  selectedToolCallId: null,
  run: {
    id: id("10"),
    status: "COMPLETED",
    knownStatus: true,
    state: "completed",
    snapshotCurrent: true,
    safeGoal: "Review the project and explain the next safe action.",
    lockVersion: 4,
    failureCode: null,
    degradationCode: null,
    retryable: false,
    createdAt: "2026-08-06T08:00:00Z",
    completedAt: "2026-08-06T08:00:05Z",
  },
  blockers: [],
  allowedNextActions: [],
  planSteps: [
    {
      id: id("20"),
      label: "get_project_state",
      status: "COMPLETED",
      knownStatus: true,
    },
  ],
  timeline: [
    {
      id: id("30"),
      sequence: 1,
      kind: "ASSISTANT_SUMMARY",
      factKind: "AGENT_SUGGESTION",
      text: "Review the available project facts.",
      createdAt: "2026-08-06T08:00:05Z",
    },
  ],
  toolCalls: [tool()],
  modelInvocations: [
    {
      id: id("40"),
      toolCallId: null,
      status: "SUCCEEDED",
      knownStatus: true,
      inputTokens: 120,
      outputTokens: 80,
      totalTokens: 200,
      requestCount: 1,
      latencyMs: 450,
      errorCode: null,
      degraded: false,
    },
  ],
  job: {
    id: id("50"),
    status: "COMPLETED",
    knownStatus: true,
    progress: 100,
    retryable: false,
    errorCode: null,
  },
  providerDegraded: false,
  schemaInvalid: false,
  promptInjectionBlocked: false,
  toolDenied: false,
  approvalStale: false,
  sourceState: "available",
  capabilities: {
    permissionsKnown: true,
    createRun: action(true),
    sendMessage: action(false, "RUN_NOT_WAITING_FOR_INPUT"),
    cancelRun: action(false, "RUN_TERMINAL"),
    retryOrRestart: action(false, "RETRY_NOT_AVAILABLE"),
  },
})

export type AgentWorkspaceFixture = {
  id: string
  viewport: "desktop" | "tablet" | "mobile"
  theme: "light" | "dark"
  content: Loadable<AgentWorkspaceViewModel>
  pendingAction: AgentWorkspaceEvent["action"] | null
  mutationError: UiErrorViewModel | null
  selectedToolCallId: string | null
}

const ready = (
  fixtureId: string,
  change: (workspace: AgentWorkspaceViewModel) => void = () => undefined,
  props: Partial<Omit<AgentWorkspaceFixture, "id" | "content">> = {},
): AgentWorkspaceFixture => {
  const workspace = base()
  change(workspace)
  return {
    id: fixtureId,
    viewport: fixtureId.includes("mobile")
      ? "mobile"
      : fixtureId.includes("tablet")
        ? "tablet"
        : "desktop",
    theme: fixtureId.includes("dark") ? "dark" : "light",
    content: { state: "ready", data: workspace },
    pendingAction: null,
    mutationError: null,
    selectedToolCallId: workspace.selectedToolCallId,
    ...props,
  }
}

const errorFixture = (
  fixtureId: string,
  code: string,
  status: "forbidden" | "error",
) =>
  ({
    id: fixtureId,
    viewport: "desktop" as const,
    theme: "light" as const,
    content: {
      state: "error" as const,
      error: {
        title: status === "forbidden" ? "Access denied" : "Request failed",
        message: "The Agent workspace is unavailable.",
        code,
        requestId: `req-${fixtureId}`,
        retryable: status === "error",
        forbidden: status === "forbidden",
        notFound: false,
        conflict: false,
      },
    },
    pendingAction: null,
    mutationError: null,
    selectedToolCallId: null,
  }) satisfies AgentWorkspaceFixture

export const agentWorkspaceFixtures: AgentWorkspaceFixture[] = [
  {
    id: "loading",
    viewport: "desktop",
    theme: "light",
    content: { state: "loading", label: "Loading Agent workspace" },
    pendingAction: null,
    mutationError: null,
    selectedToolCallId: null,
  },
  {
    id: "empty-no-run",
    viewport: "desktop",
    theme: "light",
    content: { state: "empty", message: "No AgentRun has been started." },
    pendingAction: null,
    mutationError: null,
    selectedToolCallId: null,
  },
  errorFixture("load-error", "NETWORK_ERROR", "error"),
  errorFixture("forbidden", "PERMISSION_DENIED", "forbidden"),
  ready("create-available", (w) => {
    w.run = null
    w.timeline = []
    w.toolCalls = []
    w.planSteps = []
    w.modelInvocations = []
    w.job = null
  }),
  ready("create-unavailable", (w) => {
    w.run = null
    w.capabilities.createRun = action(false, "PROJECT_ARCHIVED")
    w.readOnly = true
  }),
  ready("permissions-unknown", (w) => {
    w.permissionsKnown = false
    w.capabilities = {
      permissionsKnown: false,
      createRun: action(false, "PERMISSIONS_UNKNOWN"),
      sendMessage: action(false, "PERMISSIONS_UNKNOWN"),
      cancelRun: action(false, "PERMISSIONS_UNKNOWN"),
      retryOrRestart: action(false, "PERMISSIONS_UNKNOWN"),
    }
  }),
  ready("route-fallback", (w) => {
    w.routeFallback = true
    w.run = null
    w.toolCalls = []
    w.planSteps = []
  }),
  ready("read-only", (w) => {
    w.readOnly = true
    w.capabilities.createRun = action(false, "PROJECT_ARCHIVED")
  }),
  ready("planning", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "PLANNING",
        state: "planning",
        completedAt: null,
      })
    w.job = { ...w.job!, status: "RUNNING", progress: 15 }
  }),
  ready("running", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "CALLING_TOOL",
        state: "running",
        completedAt: null,
      })
    w.toolCalls = [tool({ status: "RUNNING" })]
    w.job = { ...w.job!, status: "RUNNING", progress: 55 }
  }),
  ready("running-cancellable", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "CALLING_TOOL",
        state: "running",
        completedAt: null,
      })
    w.toolCalls = [tool({ status: "RUNNING" })]
    w.capabilities.cancelRun = action(true)
  }),
  ready(
    "running-cancel-pending",
    (w) => {
      if (w.run)
        Object.assign(w.run, {
          status: "CALLING_TOOL",
          state: "running",
          completedAt: null,
        })
      w.toolCalls = [tool({ status: "RUNNING" })]
      w.capabilities.cancelRun = action(true)
    },
    { pendingAction: "cancel-run" },
  ),
  ready("waiting-user-input", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "WAITING_USER_INPUT",
        state: "waiting-user-input",
        completedAt: null,
      })
    w.capabilities.sendMessage = action(true)
  }),
  ready("resume-pending", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "WAITING_USER_INPUT",
        state: "waiting-user-input",
        completedAt: null,
      })
    w.timeline.push({
      id: id("36"),
      sequence: 2,
      kind: "USER_MESSAGE",
      factKind: "USER_CONFIRMATION",
      text: "Continue intent accepted; runtime resume is pending.",
      createdAt: "2026-08-06T08:00:06Z",
    })
    w.capabilities.sendMessage = action(false, "AGENT_RESUME_PENDING")
  }),
  ready("waiting-approval", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "WAITING_APPROVAL",
        state: "waiting-approval",
        completedAt: null,
      })
    w.toolCalls = [
      tool({
        status: "WAITING_APPROVAL",
        category: "SIDE_EFFECT",
        confirmation: "FORMAL_APPROVAL",
        factKind: "FORMAL_APPROVAL",
        approval: {
          id: id("60"),
          status: "PENDING",
          knownStatus: true,
          stale: false,
          expiresAt: null,
        },
      }),
    ]
  }),
  ready("structured-plan", (w) => {
    w.planSteps = ["get_project_state", "retrieve_evidence", "audit_claim"].map(
      (label, i) => ({
        id: id(String(70 + i)),
        label,
        status: i === 0 ? "COMPLETED" : "REQUESTED",
        knownStatus: true,
      }),
    )
  }),
  ready("multi-step-running", (w) => {
    w.planSteps.push({
      id: id("74"),
      label: "audit_claim",
      status: "RUNNING",
      knownStatus: true,
    })
    w.toolCalls.push(
      tool({
        id: id("21"),
        name: "audit_claim",
        status: "RUNNING",
        category: "SUGGESTION",
        factKind: "AGENT_SUGGESTION",
      }),
    )
  }),
  ready("long-content", (w) => {
    if (w.run)
      w.run.safeGoal =
        "Review the complete research context, preserve every source distinction, explain limitations, and propose only actions currently allowed by server policy. ".repeat(
          8,
        )
  }),
  ready(
    "read-only-tool-completed",
    (w) => {
      w.selectedToolCallId = id("20")
    },
    { selectedToolCallId: id("20") },
  ),
  ready("suggestion-not-adopted", (w) => {
    w.toolCalls = [
      tool({
        name: "suggest_next_steps",
        category: "SUGGESTION",
        factKind: "AGENT_SUGGESTION",
        outputSummary: "Consider validating the evidence matrix.",
      }),
    ]
  }),
  ready("side-effect-requested", (w) => {
    w.toolCalls = [
      tool({
        name: "request_export",
        category: "SIDE_EFFECT",
        confirmation: "FORMAL_APPROVAL",
        factKind: "FORMAL_APPROVAL",
        status: "REQUESTED",
      }),
    ]
  }),
  ready("side-effect-running", (w) => {
    w.toolCalls = [
      tool({
        name: "request_export",
        category: "SIDE_EFFECT",
        confirmation: "FORMAL_APPROVAL",
        factKind: "FORMAL_APPROVAL",
        status: "RUNNING",
        job: {
          id: id("51"),
          status: "RUNNING",
          knownStatus: true,
          progress: 40,
          retryable: false,
          errorCode: null,
        },
      }),
    ]
  }),
  ready("side-effect-job-completed", (w) => {
    w.toolCalls = [
      tool({
        name: "request_export",
        category: "SIDE_EFFECT",
        status: "COMPLETED",
        sourceLink: { objectType: "export", objectId: id("90") },
        job: {
          id: id("51"),
          status: "COMPLETED",
          knownStatus: true,
          progress: 100,
          retryable: false,
          errorCode: null,
        },
      }),
    ]
  }),
  ready("side-effect-job-failed", (w) => {
    w.toolCalls = [
      tool({
        name: "request_export",
        category: "SIDE_EFFECT",
        status: "FAILED",
        retryable: true,
        errorCode: "JOB_FAILED",
        job: {
          id: id("51"),
          status: "FAILED",
          knownStatus: true,
          progress: 40,
          retryable: true,
          errorCode: "JOB_FAILED",
        },
      }),
    ]
  }),
  ready("tool-denied", (w) => {
    w.toolDenied = true
    w.toolCalls = [tool({ status: "DENIED", errorCode: "TOOL_POLICY_DENIED" })]
  }),
  ready("tool-unknown", (w) => {
    w.toolCalls = [
      tool({
        status: "FUTURE_STATUS",
        knownStatus: false,
        category: "UNKNOWN",
        confirmation: "UNKNOWN",
        allowedActions: new Set(),
      }),
    ]
  }),
  ready("tool-timeout", (w) => {
    w.toolCalls = [
      tool({ status: "FAILED", errorCode: "TOOL_TIMEOUT", retryable: true }),
    ]
  }),
  ready("tool-cancelled", (w) => {
    w.toolCalls = [tool({ status: "CANCELLED", errorCode: null })]
  }),
  ready("tool-failed-retryable", (w) => {
    w.toolCalls = [
      tool({
        status: "FAILED",
        errorCode: "PROVIDER_TIMEOUT",
        retryable: true,
      }),
    ]
  }),
  ready("tool-failed-retry-allowed", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "FAILED",
        state: "failed",
        failureCode: "TOOL_FAILED",
        retryable: true,
      })
    w.toolCalls = [
      tool({
        status: "FAILED",
        errorCode: "PROVIDER_TIMEOUT",
        retryable: true,
      }),
    ]
    w.capabilities.retryOrRestart = action(true)
  }),
  ready(
    "tool-retry-pending",
    (w) => {
      if (w.run)
        Object.assign(w.run, {
          status: "FAILED",
          state: "failed",
          failureCode: "TOOL_FAILED",
          retryable: true,
        })
      w.toolCalls = [
        tool({
          status: "FAILED",
          errorCode: "PROVIDER_TIMEOUT",
          retryable: true,
        }),
      ]
      w.capabilities.retryOrRestart = action(true)
    },
    { pendingAction: "retry-or-restart" },
  ),
  ready("tool-failed-non-retryable", (w) => {
    w.toolCalls = [
      tool({
        status: "FAILED",
        errorCode: "TOOL_SCHEMA_INVALID",
        retryable: false,
      }),
    ]
  }),
  ready("approval-pending", (w) => {
    w.toolCalls[0].approval = {
      id: id("60"),
      status: "PENDING",
      knownStatus: true,
      stale: false,
      expiresAt: null,
    }
  }),
  ready("approval-approved", (w) => {
    w.toolCalls[0].approval = {
      id: id("60"),
      status: "APPROVED",
      knownStatus: true,
      stale: false,
      expiresAt: null,
    }
  }),
  ready("approval-rejected", (w) => {
    w.toolCalls[0].approval = {
      id: id("60"),
      status: "REJECTED",
      knownStatus: true,
      stale: false,
      expiresAt: null,
    }
  }),
  ready("approval-expired", (w) => {
    w.toolCalls[0].approval = {
      id: id("60"),
      status: "EXPIRED",
      knownStatus: true,
      stale: true,
      expiresAt: "2026-08-05T08:00:00Z",
    }
    w.approvalStale = true
  }),
  ready("approval-stale", (w) => {
    w.toolCalls[0].approval = {
      id: id("60"),
      status: "APPROVED",
      knownStatus: true,
      stale: true,
      expiresAt: null,
    }
    w.approvalStale = true
  }),
  ready("approval-hash-mismatch", (w) => {
    w.toolCalls[0].approval = {
      id: id("60"),
      status: "APPROVED",
      knownStatus: true,
      stale: true,
      expiresAt: null,
    }
    w.toolCalls[0].errorCode = "APPROVAL_HASH_MISMATCH"
    w.approvalStale = true
  }),
  ready("agent-completed", () => undefined),
  ready("agent-failed", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "FAILED",
        state: "failed",
        failureCode: "ORCHESTRATION_FAILED",
        retryable: true,
      })
    w.capabilities.retryOrRestart = action(false, "RETRYABLE_TOOL_REQUIRED")
  }),
  ready("agent-cancelled", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "CANCELLED",
        state: "cancelled",
        failureCode: null,
      })
  }),
  ready("max-turn-reached", (w) => {
    if (w.run)
      Object.assign(w.run, {
        status: "FAILED",
        state: "failed",
        failureCode: "MAX_TURNS_REACHED",
        retryable: true,
      })
  }),
  ready("provider-degraded", (w) => {
    w.providerDegraded = true
    if (w.run) w.run.degradationCode = "PROVIDER_UNAVAILABLE"
  }),
  ready("schema-invalid", (w) => {
    w.schemaInvalid = true
    if (w.run) w.run.failureCode = "INVALID_OUTPUT"
  }),
  ready("prompt-injection-blocked", (w) => {
    w.promptInjectionBlocked = true
    if (w.run) w.run.failureCode = "PROMPT_INJECTION_BLOCKED"
  }),
  ready("source-denied", (w) => {
    w.sourceState = "denied"
    w.toolCalls = []
  }),
  ready("source-missing", (w) => {
    w.sourceState = "missing"
    w.toolCalls[0].errorCode = "SOURCE_MISSING"
  }),
  ready("source-stale", (w) => {
    w.sourceState = "stale"
    if (w.run) w.run.snapshotCurrent = false
    w.capabilities.cancelRun = action(false, "STALE_PROJECT_CONTEXT")
  }),
  ready("source-invalidated", (w) => {
    w.sourceState = "invalidated"
    w.toolCalls[0].errorCode = "SOURCE_INVALIDATED"
  }),
  ready("idempotent-replay", (w) => {
    w.timeline.push({
      id: id("31"),
      sequence: 2,
      kind: "CONTINUE_INTENT",
      factKind: "USER_CONFIRMATION",
      text: "Duplicate request replayed without a second operation.",
      createdAt: "2026-08-06T08:00:06Z",
    })
  }),
  ready("mutation-pending", () => undefined, { pendingAction: "send-message" }),
  ready("mutation-conflict", () => undefined, {
    mutationError: {
      title: "Conflict",
      message: "The project snapshot changed.",
      code: "IDEMPOTENCY_CONFLICT",
      requestId: "req-conflict",
      retryable: false,
      forbidden: false,
      notFound: false,
      conflict: true,
    },
  }),
  ready("mutation-error", () => undefined, {
    mutationError: {
      title: "Request failed",
      message: "The provider is unavailable.",
      code: "PROVIDER_UNAVAILABLE",
      requestId: "req-error",
      retryable: true,
      forbidden: false,
      notFound: false,
      conflict: false,
    },
  }),
  ready("fact-separation", (w) => {
    w.timeline = [
      {
        id: id("31"),
        sequence: 1,
        kind: "SYSTEM_FACT",
        factKind: "SYSTEM_FACT",
        text: "Two approvals are pending.",
        createdAt: "2026-08-06T08:00:00Z",
      },
      {
        id: id("32"),
        sequence: 2,
        kind: "DETERMINISTIC_RESULT",
        factKind: "DETERMINISTIC_RESULT",
        text: "The deterministic audit completed.",
        createdAt: "2026-08-06T08:00:01Z",
      },
      {
        id: id("33"),
        sequence: 3,
        kind: "ASSISTANT_SUMMARY",
        factKind: "AGENT_SUGGESTION",
        text: "Consider reviewing the audit.",
        createdAt: "2026-08-06T08:00:02Z",
      },
      {
        id: id("34"),
        sequence: 4,
        kind: "USER_MESSAGE",
        factKind: "USER_CONFIRMATION",
        text: "Open the audit.",
        createdAt: "2026-08-06T08:00:03Z",
      },
      {
        id: id("35"),
        sequence: 5,
        kind: "APPROVAL",
        factKind: "FORMAL_APPROVAL",
        text: "Approval remains external and pending.",
        createdAt: "2026-08-06T08:00:04Z",
      },
    ]
  }),
  ready("desktop-dark", (w) => {
    w.projectName = "Desktop dark acceptance"
  }),
  ready("tablet-light", (w) => {
    w.projectName = "Tablet light acceptance"
  }),
  ready("mobile-dark", (w) => {
    w.projectName = "Mobile dark acceptance"
  }),
]

export const agentWorkspaceFixtureById = Object.fromEntries(
  agentWorkspaceFixtures.map((fixture) => [fixture.id, fixture]),
) as Record<string, AgentWorkspaceFixture>
