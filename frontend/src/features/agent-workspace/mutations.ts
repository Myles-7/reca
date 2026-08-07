import { useMutation, useQueryClient } from "@tanstack/react-query"

import { AgentRunsApi } from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import type { AgentWorkspaceViewModel } from "./model"
import type { AgentWorkspaceEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

export function canExecuteAgentWorkspaceEvent(
  workspace: AgentWorkspaceViewModel | null,
  event: AgentWorkspaceEvent,
) {
  if (event.action === "refresh") return true
  if (!workspace?.permissionsKnown) return false
  switch (event.action) {
    case "create-run":
      return (
        workspace.capabilities.createRun.allowed &&
        event.input.goal.trim().length > 0
      )
    case "send-message":
      return (
        workspace.capabilities.sendMessage.allowed &&
        workspace.run?.id === event.input.runId &&
        workspace.run.state === "waiting-user-input" &&
        event.input.message.trim().length > 0
      )
    case "cancel-run":
      return (
        workspace.capabilities.cancelRun.allowed &&
        workspace.run?.id === event.input.runId
      )
    case "retry-or-restart":
      return (
        workspace.capabilities.retryOrRestart.allowed &&
        workspace.run?.id === event.input.runId &&
        workspace.run.retryable &&
        workspace.toolCalls.some(
          (tool) => tool.knownStatus && tool.retryable,
        ) &&
        event.input.goal.trim().length > 0
      )
    case "open-approval":
      return workspace.toolCalls.some(
        (tool) =>
          tool.approval?.id === event.input.approvalId &&
          tool.approval.knownStatus,
      )
    case "open-source":
      return workspace.toolCalls.some(
        (tool) =>
          tool.sourceLink?.objectType === event.input.objectType &&
          tool.sourceLink.objectId === event.input.objectId &&
          tool.knownStatus,
      )
  }
}

async function execute(projectId: string, event: AgentWorkspaceEvent) {
  switch (event.action) {
    case "create-run":
      return AgentRunsApi.create(
        projectId,
        {
          goal: event.input.goal,
          mode: event.input.mode,
          allow_tool_calls: event.input.allowToolCalls,
        },
        key(),
      )
    case "send-message":
      return AgentRunsApi.message(event.input.runId, event.input.message, key())
    case "cancel-run":
      return AgentRunsApi.cancel(event.input.runId, key())
    case "retry-or-restart":
      return AgentRunsApi.create(
        projectId,
        {
          goal: event.input.goal,
          mode: "PLAN_AND_EXPLAIN",
          allow_tool_calls: true,
        },
        key(),
      )
    case "refresh":
    case "open-source":
    case "open-approval":
      return null
  }
}

export function useAgentWorkspaceMutation(
  projectId: string,
  workspace: AgentWorkspaceViewModel | null,
  onSuccess?: (event: AgentWorkspaceEvent, result: unknown) => void,
) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: async (event: AgentWorkspaceEvent) => {
      if (!canExecuteAgentWorkspaceEvent(workspace, event))
        throw new Error("The event is not allowed by current server facts.")
      return { event, result: await execute(projectId, event) }
    },
    onSuccess: async ({ event, result }) => {
      await client.invalidateQueries({
        queryKey: ["projects", projectId, "agent-workspace"],
      })
      onSuccess?.(event, result)
    },
  })
  return {
    mutate: mutation.mutate,
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
