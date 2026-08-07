import { useQuery } from "@tanstack/react-query"

import { AgentRunsApi, ApiError, ProjectsApi } from "@/api/adapter"

import { mapAgentWorkspace } from "./mappers"
import type { AgentWorkspaceRouteSearch } from "./route-contract"

export const agentWorkspaceKeys = {
  workspace: (projectId: string, search: AgentWorkspaceRouteSearch) =>
    ["projects", projectId, "agent-workspace", search] as const,
}

function noDisclosure(message: string): never {
  throw new ApiError(
    404,
    "NOT_FOUND",
    message,
    "AGENT_WORKSPACE_ROUTE_MISMATCH",
  )
}

async function loadSelected(
  projectId: string,
  search: AgentWorkspaceRouteSearch,
) {
  const project = (await ProjectsApi.get(projectId)).data
  if (project.id !== projectId)
    noDisclosure("The Project response is inconsistent.")
  if (
    !search.run &&
    (search.tool || search.sourceId || search.approval || search.job)
  )
    noDisclosure("The Agent workspace link is incomplete.")
  if (!search.run)
    return mapAgentWorkspace({ project, run: null, toolCalls: [] })
  const [runEnvelope, toolsEnvelope, selectedToolEnvelope] = await Promise.all([
    AgentRunsApi.get(search.run),
    AgentRunsApi.toolCalls(search.run, { page: 1, page_size: 100 }),
    search.tool ? AgentRunsApi.toolCall(search.tool) : null,
  ])
  const run = runEnvelope.data
  const toolCalls = toolsEnvelope.data
  if (run.project_id !== projectId)
    noDisclosure("The AgentRun is not available in this project.")
  if (
    toolCalls.some(
      (tool) => tool.project_id !== projectId || tool.agent_run_id !== run.id,
    )
  )
    noDisclosure("The ToolCall list contains an unrelated resource.")
  if (selectedToolEnvelope) {
    const selected = selectedToolEnvelope.data
    if (selected.project_id !== projectId || selected.agent_run_id !== run.id)
      noDisclosure("The ToolCall is not part of the selected AgentRun.")
    if (!toolCalls.some((tool) => tool.id === selected.id))
      toolCalls.push(selected)
  }
  if (
    search.approval &&
    !toolCalls.some((tool) => tool.approval?.id === search.approval)
  )
    noDisclosure("The Approval is not linked to this AgentRun.")
  if (
    search.job &&
    run.job?.id !== search.job &&
    !toolCalls.some((tool) => tool.job?.id === search.job)
  )
    noDisclosure("The Job is not linked to this AgentRun.")
  if (
    search.sourceType &&
    search.sourceId &&
    !toolCalls.some(
      (tool) =>
        tool.output_object_type === search.sourceType &&
        tool.output_object_id === search.sourceId,
    )
  )
    noDisclosure("The source is not linked to this AgentRun.")
  return mapAgentWorkspace({
    project,
    run,
    toolCalls,
    selectedToolCallId: selectedToolEnvelope?.data.id ?? null,
  })
}

export async function loadAgentWorkspace(
  projectId: string,
  search: AgentWorkspaceRouteSearch,
) {
  try {
    return await loadSelected(projectId, search)
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 404 &&
      (search.run ||
        search.tool ||
        search.sourceId ||
        search.approval ||
        search.job)
    ) {
      const fallback = await loadSelected(projectId, {})
      return { ...fallback, routeFallback: true }
    }
    throw error
  }
}

export function useAgentWorkspaceQuery(
  projectId: string,
  search: AgentWorkspaceRouteSearch,
) {
  return useQuery({
    queryKey: agentWorkspaceKeys.workspace(projectId, search),
    queryFn: () => loadAgentWorkspace(projectId, search),
    refetchInterval: (query) => {
      const state = query.state.data?.run?.state
      return state && ["accepted", "planning", "running"].includes(state)
        ? 2000
        : false
    },
    retry: (count, error) =>
      !(error instanceof ApiError && [401, 403, 404].includes(error.status)) &&
      count < 2,
  })
}
