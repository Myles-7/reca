import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { QueryPlanFieldsViewModel, QueryPlanViewModel } from "../model"

export type QueryPlanEvent =
  | {
      action: "create"
      input: QueryPlanFieldsViewModel & { researchQuestionVersionId: string }
    }
  | {
      action: "update"
      input: {
        queryPlanId: string
        lockVersion: number
        changeReason: string
        fields: QueryPlanFieldsViewModel
      }
    }
  | { action: "generate"; input: { queryPlanId: string } }

export type QueryPlanWorkspaceProps = {
  content: Loadable<QueryPlanViewModel>
  pendingAction: QueryPlanEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: QueryPlanEvent) => void
}
