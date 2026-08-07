import type { ComponentType } from "react"

import type {
  AgentWorkspaceRouteSearch,
  AgentWorkspaceRouteView,
} from "../route-contract"
import type { AgentWorkspaceEvent, AgentWorkspaceProps } from "../ui/contracts"
import { useAgentWorkspaceController } from "./useAgentWorkspaceController"

type AgentWorkspaceViewProps = AgentWorkspaceProps & {
  initialSurface?: AgentWorkspaceRouteView
  onSurfaceChange?: (surface: AgentWorkspaceRouteView) => void
}

export function AgentWorkspaceContainer({
  projectId,
  search,
  View,
  onIntent,
  onToolSelectionChange,
  onSurfaceChange,
  onMutationSuccess,
}: {
  projectId: string
  search: AgentWorkspaceRouteSearch
  View: ComponentType<AgentWorkspaceViewProps>
  onIntent?: AgentWorkspaceProps["onEvent"]
  onToolSelectionChange?: (toolCallId: string | null) => void
  onSurfaceChange?: (surface: AgentWorkspaceRouteView) => void
  onMutationSuccess?: (event: AgentWorkspaceEvent, result: unknown) => void
}) {
  const props = useAgentWorkspaceController(
    projectId,
    search,
    onIntent,
    onToolSelectionChange,
    onMutationSuccess,
  )
  return (
    <View
      {...props}
      initialSurface={search.view}
      onSurfaceChange={onSurfaceChange}
    />
  )
}
