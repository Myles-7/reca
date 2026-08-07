import type { Loadable, UiErrorViewModel } from "../projects/model"

export type AgentRunState =
  | "accepted"
  | "planning"
  | "running"
  | "waiting-user-input"
  | "waiting-approval"
  | "completed"
  | "failed"
  | "cancelled"
  | "unknown"

export type FactKind =
  | "AGENT_SUGGESTION"
  | "SYSTEM_FACT"
  | "DETERMINISTIC_RESULT"
  | "USER_CONFIRMATION"
  | "FORMAL_APPROVAL"

export type ActionCapability = {
  allowed: boolean
  reason: string | null
}

export type AgentEventViewModel = {
  id: string
  sequence: number
  kind: string
  factKind: FactKind
  text: string | null
  createdAt: string
}

export type JobLinkViewModel = {
  id: string
  status: string
  knownStatus: boolean
  progress: number
  retryable: boolean
  errorCode: string | null
}

export type ApprovalLinkViewModel = {
  id: string
  status: string
  knownStatus: boolean
  stale: boolean
  expiresAt: string | null
}

export type ModelInvocationViewModel = {
  id: string
  toolCallId: string | null
  status: string
  knownStatus: boolean
  inputTokens: number | null
  outputTokens: number | null
  totalTokens: number | null
  requestCount: number | null
  latencyMs: number | null
  errorCode: string | null
  degraded: boolean
}

export type ToolCallViewModel = {
  id: string
  runId: string
  name: string
  version: string
  status: string
  knownStatus: boolean
  category: "READ_ONLY" | "SUGGESTION" | "SIDE_EFFECT" | "UNKNOWN"
  confirmation:
    | "NONE"
    | "LIGHT_CONFIRMATION"
    | "FORMAL_APPROVAL"
    | "PROHIBITED"
    | "UNKNOWN"
  factKind: FactKind
  inputSummary: string | null
  outputSummary: string | null
  approval: ApprovalLinkViewModel | null
  job: JobLinkViewModel | null
  sourceLink: { objectType: string; objectId: string } | null
  retryable: boolean
  errorCode: string | null
  allowedActions: ReadonlySet<string>
  disabledReason: string | null
}

export type AgentWorkspaceCapabilities = {
  permissionsKnown: boolean
  createRun: ActionCapability
  sendMessage: ActionCapability
  cancelRun: ActionCapability
  retryOrRestart: ActionCapability
}

export type AgentWorkspaceViewModel = {
  projectId: string
  projectName: string
  projectStage: string
  permissionsKnown: boolean
  readOnly: boolean
  routeFallback: boolean
  selectedToolCallId: string | null
  run: {
    id: string
    status: string
    knownStatus: boolean
    state: AgentRunState
    snapshotCurrent: boolean
    safeGoal: string | null
    lockVersion: number
    failureCode: string | null
    degradationCode: string | null
    retryable: boolean
    createdAt: string
    completedAt: string | null
  } | null
  blockers: string[]
  allowedNextActions: string[]
  planSteps: Array<{
    id: string
    label: string
    status: string
    knownStatus: boolean
  }>
  timeline: AgentEventViewModel[]
  toolCalls: ToolCallViewModel[]
  modelInvocations: ModelInvocationViewModel[]
  job: JobLinkViewModel | null
  providerDegraded: boolean
  schemaInvalid: boolean
  promptInjectionBlocked: boolean
  toolDenied: boolean
  approvalStale: boolean
  sourceState:
    | "available"
    | "denied"
    | "missing"
    | "stale"
    | "invalidated"
    | "unknown"
  capabilities: AgentWorkspaceCapabilities
}

export type AgentWorkspaceLoadable = Loadable<AgentWorkspaceViewModel>
export type AgentWorkspaceMutationError = UiErrorViewModel | null
