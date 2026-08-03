import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { LiteratureWorkspaceViewModel } from "../model"

export type LiteratureEvent =
  | {
      action: "search"
      input: { queryPlanId: string; pageSize: number; useCache: boolean }
    }
  | {
      action: "import-candidates"
      input: { searchRunId: string; candidateIds: string[] }
    }
  | { action: "import-doi"; input: { doi: string } }
  | { action: "retry-job"; input: { jobId: string } }

export type LiteratureWorkspaceProps = {
  content: Loadable<LiteratureWorkspaceViewModel>
  pendingAction: LiteratureEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: LiteratureEvent) => void
}
