import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type { TopicCandidatesViewModel } from "../model"

export type TopicCandidatesEvent =
  | {
      action: "generate-topic"
      input: {
        researchQuestionVersionId: string
        summaryId: string
        candidateCount: 3
        userConstraints: Record<string, unknown>
      }
    }
  | {
      action: "open-source"
      input: {
        candidateId: string
        literatureRecordId: string | null
        evidenceSpanId: string | null
      }
    }

export type TopicCandidatesWorkspaceProps = {
  content: Loadable<TopicCandidatesViewModel>
  pendingAction: TopicCandidatesEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: TopicCandidatesEvent) => void
}
