import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { AgentWorkspaceViewModel } from "../model"

export type AgentWorkspaceEvent =
  | {
      action: "create-run"
      input: {
        goal: string
        mode: "PLAN_AND_EXPLAIN"
        allowToolCalls: boolean
      }
    }
  | { action: "send-message"; input: { runId: string; message: string } }
  | { action: "cancel-run"; input: { runId: string } }
  | { action: "refresh" }
  | { action: "open-source"; input: { objectType: string; objectId: string } }
  | { action: "open-approval"; input: { approvalId: string } }
  | { action: "retry-or-restart"; input: { runId: string; goal: string } }

export type AgentWorkspaceProps = {
  content: Loadable<AgentWorkspaceViewModel>
  pendingAction: AgentWorkspaceEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: AgentWorkspaceEvent) => void
  selectedToolCallId?: string | null
  onToolSelectionChange?: (toolCallId: string | null) => void
}
