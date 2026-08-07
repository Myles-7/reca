import { createFileRoute } from "@tanstack/react-router"

import { AgentWorkspaceContainer } from "@/features/agent-workspace/containers/AgentWorkspaceContainer"
import {
  agentSourceWorkspaceHref,
  parseAgentWorkspaceSearch,
} from "@/features/agent-workspace/route-contract"
import { AgentWorkspace } from "@/features/agent-workspace/ui"
import type { AgentWorkspaceEvent } from "@/features/agent-workspace/ui/contracts"

export const Route = createFileRoute("/_layout/projects/$projectId_/agent")({
  validateSearch: parseAgentWorkspaceSearch,
  component: AgentWorkspaceRoute,
  head: () => ({ meta: [{ title: "Research Agent - RECA" }] }),
})

function AgentWorkspaceRoute() {
  const { projectId } = Route.useParams()
  const search = Route.useSearch()
  const navigate = Route.useNavigate()
  const updateSearch = (next: Partial<typeof search>) =>
    void navigate({ search: (previous) => ({ ...previous, ...next }) })

  const onIntent = (event: AgentWorkspaceEvent) => {
    if (event.action === "open-source") {
      const href = agentSourceWorkspaceHref(
        projectId,
        event.input.objectType,
        event.input.objectId,
      )
      if (href) window.location.assign(href)
      else
        updateSearch({
          sourceType: event.input.objectType,
          sourceId: event.input.objectId,
          view: "tools",
        })
    } else if (event.action === "open-approval") {
      void navigate({
        to: "/projects/$projectId",
        params: { projectId },
        search: { tab: "approvals", approval: event.input.approvalId },
      })
    }
  }

  const onMutationSuccess = (event: AgentWorkspaceEvent, result: unknown) => {
    if (event.action !== "create-run" && event.action !== "retry-or-restart")
      return
    const envelope =
      result && typeof result === "object"
        ? (result as Record<string, unknown>)
        : null
    const data =
      envelope?.data && typeof envelope.data === "object"
        ? (envelope.data as Record<string, unknown>)
        : null
    const run = typeof data?.id === "string" ? data.id : undefined
    if (run) updateSearch({ run, tool: undefined, view: "timeline" })
  }

  return (
    <AgentWorkspaceContainer
      projectId={projectId}
      search={search}
      View={AgentWorkspace}
      onIntent={onIntent}
      onToolSelectionChange={(tool) =>
        updateSearch({ tool: tool ?? undefined, view: "tools" })
      }
      onSurfaceChange={(view) => updateSearch({ view })}
      onMutationSuccess={onMutationSuccess}
    />
  )
}
