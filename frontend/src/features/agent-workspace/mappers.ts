import type {
  AgentRunPublic,
  ProjectPublic,
  ToolCallLinkPublic,
} from "@/api/adapter"

import type {
  ActionCapability,
  AgentRunState,
  AgentWorkspaceViewModel,
  FactKind,
  ToolCallViewModel,
} from "./model"

const knownRunStatuses = new Set([
  "CREATED",
  "PLANNING",
  "WAITING_USER_INPUT",
  "WAITING_APPROVAL",
  "CALLING_TOOL",
  "REVIEWING",
  "COMPLETED",
  "FAILED",
  "CANCELLED",
])

const capability = (
  actions: ReadonlySet<string>,
  action: string,
  reason: string | null,
): ActionCapability => ({ allowed: actions.has(action), reason })

function runState(status: string, known: boolean): AgentRunState {
  if (!known || !knownRunStatuses.has(status)) return "unknown"
  if (status === "CREATED") return "accepted"
  if (status === "PLANNING") return "planning"
  if (["CALLING_TOOL", "REVIEWING"].includes(status)) return "running"
  if (status === "WAITING_USER_INPUT") return "waiting-user-input"
  if (status === "WAITING_APPROVAL") return "waiting-approval"
  return status.toLowerCase() as AgentRunState
}

function toolFactKind(tool: ToolCallLinkPublic): FactKind {
  if (tool.confirmation === "FORMAL_APPROVAL") return "FORMAL_APPROVAL"
  if (tool.category === "SUGGESTION") return "AGENT_SUGGESTION"
  return tool.category === "READ_ONLY" ? "SYSTEM_FACT" : "DETERMINISTIC_RESULT"
}

export function mapToolCall(tool: ToolCallLinkPublic): ToolCallViewModel {
  const known = tool.known_status
  const actions = known ? new Set(tool.allowed_actions) : new Set<string>()
  return {
    id: tool.id,
    runId: tool.agent_run_id,
    name: tool.tool_name,
    version: tool.tool_version,
    status: tool.status,
    knownStatus: known,
    category: ["READ_ONLY", "SUGGESTION", "SIDE_EFFECT"].includes(tool.category)
      ? (tool.category as ToolCallViewModel["category"])
      : "UNKNOWN",
    confirmation: [
      "NONE",
      "LIGHT_CONFIRMATION",
      "FORMAL_APPROVAL",
      "PROHIBITED",
    ].includes(tool.confirmation)
      ? (tool.confirmation as ToolCallViewModel["confirmation"])
      : "UNKNOWN",
    factKind: toolFactKind(tool),
    inputSummary: tool.safe_input_summary.text ?? null,
    outputSummary: tool.safe_output_summary?.text ?? null,
    approval: tool.approval
      ? {
          id: tool.approval.id,
          status: tool.approval.status,
          knownStatus: tool.approval.known_status,
          stale: tool.approval.stale,
          expiresAt: tool.approval.expires_at,
        }
      : null,
    job: tool.job
      ? {
          id: tool.job.id,
          status: tool.job.status,
          knownStatus: tool.job.known_status,
          progress: tool.job.progress_percent,
          retryable: tool.job.retryable,
          errorCode: tool.job.error_code,
        }
      : null,
    sourceLink:
      tool.output_object_type && tool.output_object_id
        ? {
            objectType: tool.output_object_type,
            objectId: tool.output_object_id,
          }
        : null,
    retryable: known && tool.retryable,
    errorCode: tool.error_code,
    allowedActions: actions,
    disabledReason: tool.disabled_reason_code,
  }
}

export function mapAgentWorkspace(input: {
  project: ProjectPublic
  run: AgentRunPublic | null
  toolCalls: ToolCallLinkPublic[]
  selectedToolCallId?: string | null
  routeFallback?: boolean
}): AgentWorkspaceViewModel {
  const { project, run } = input
  const projectKnown = ["ACTIVE", "ARCHIVED", "DELETED"].includes(
    project.status,
  )
  const permissionsKnown = projectKnown && (!run || run.known_status)
  const projectActions = permissionsKnown
    ? new Set(project.allowed_actions)
    : new Set<string>()
  const runActions =
    permissionsKnown && run ? new Set(run.allowed_actions) : new Set<string>()
  const toolCalls = input.toolCalls.map(mapToolCall)
  const hasRetryableTool = toolCalls.some(
    (tool) => tool.knownStatus && tool.retryable,
  )
  const degradation = run?.degradation_code ?? ""
  const createReason = projectActions.has("project.read")
    ? null
    : "PERMISSION_UNKNOWN_OR_DENIED"
  return {
    projectId: project.id,
    projectName: project.name,
    projectStage: project.current_stage,
    permissionsKnown,
    readOnly: !permissionsKnown || project.status !== "ACTIVE",
    routeFallback: input.routeFallback ?? false,
    selectedToolCallId: input.selectedToolCallId ?? null,
    run: run
      ? {
          id: run.id,
          status: run.status,
          knownStatus: run.known_status,
          state: runState(run.status, run.known_status),
          snapshotCurrent: run.snapshot_current,
          safeGoal: run.safe_input_summary.text ?? null,
          lockVersion: run.lock_version,
          failureCode: run.failure_code,
          degradationCode: run.degradation_code,
          retryable: run.known_status && run.retryable,
          createdAt: run.created_at,
          completedAt: run.completed_at,
        }
      : null,
    blockers:
      Number(run?.safe_snapshot_summary.blocking_issue_count ?? 0) > 0
        ? ["PROJECT_BLOCKING_ISSUES_PRESENT"]
        : [],
    allowedNextActions: run ? [...run.allowed_actions] : [],
    planSteps: toolCalls.map((tool) => ({
      id: tool.id,
      label: tool.name,
      status: tool.status,
      knownStatus: tool.knownStatus,
    })),
    timeline:
      run?.events.map((event) => ({
        id: event.id,
        sequence: event.sequence_number,
        kind: event.event_type,
        factKind:
          event.event_type === "USER_MESSAGE"
            ? "USER_CONFIRMATION"
            : event.event_type === "ASSISTANT_SUMMARY"
              ? "AGENT_SUGGESTION"
              : "SYSTEM_FACT",
        text: event.safe_summary.text ?? null,
        createdAt: event.created_at,
      })) ?? [],
    toolCalls,
    modelInvocations:
      run?.model_invocations.map((item) => ({
        id: item.id,
        toolCallId: item.tool_call_id,
        status: item.status,
        knownStatus: item.known_status,
        inputTokens: item.input_tokens,
        outputTokens: item.output_tokens,
        totalTokens: item.total_tokens,
        requestCount: item.request_count,
        latencyMs: item.latency_ms,
        errorCode: item.error_code,
        degraded: item.degraded,
      })) ?? [],
    job: run?.job
      ? {
          id: run.job.id,
          status: run.job.status,
          knownStatus: run.job.known_status,
          progress: run.job.progress_percent,
          retryable: run.job.retryable,
          errorCode: run.job.error_code,
        }
      : null,
    providerDegraded:
      degradation.includes("PROVIDER") || degradation.includes("LIVE"),
    schemaInvalid:
      degradation.includes("SCHEMA") || run?.failure_code === "INVALID_OUTPUT",
    promptInjectionBlocked: run?.failure_code === "PROMPT_INJECTION_BLOCKED",
    toolDenied: toolCalls.some((tool) => tool.status === "DENIED"),
    approvalStale: toolCalls.some((tool) => tool.approval?.stale),
    sourceState: run && !run.snapshot_current ? "stale" : "available",
    capabilities: {
      permissionsKnown,
      createRun: capability(projectActions, "project.read", createReason),
      sendMessage: capability(
        runActions,
        "agent_run.continue",
        run?.disabled_reasons["agent_run.continue"] ?? null,
      ),
      cancelRun: capability(
        runActions,
        "agent_run.cancel",
        run?.disabled_reasons["agent_run.cancel"] ?? null,
      ),
      retryOrRestart: {
        allowed: Boolean(
          permissionsKnown && run?.retryable && hasRetryableTool,
        ),
        reason:
          run?.retryable && !hasRetryableTool
            ? "RETRYABLE_TOOL_REQUIRED"
            : run?.retryable
              ? null
              : "RETRY_NOT_AVAILABLE",
      },
    },
  }
}
