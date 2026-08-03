import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type {
  ResearchQuestionCapabilityAvailability,
  ResearchQuestionFields,
  ResearchQuestionViewModel,
} from "../model"

export type ResearchQuestionCreateEvent = {
  rawInput: string
}

export type ResearchQuestionSaveVersionEvent = {
  questionId: string
  basedOnVersionId: string
  changeReason: string
  fields: ResearchQuestionFields
}

export type ResearchQuestionMarkReadyEvent = {
  versionId: string
  reason: string | null
}

export type ResearchQuestionRequestConfirmationEvent = {
  versionId: string
}

export type ResearchQuestionEvent =
  | { action: "create"; input: ResearchQuestionCreateEvent }
  | { action: "save-version"; input: ResearchQuestionSaveVersionEvent }
  | { action: "mark-ready"; input: ResearchQuestionMarkReadyEvent }
  | {
      action: "request-confirmation"
      input: ResearchQuestionRequestConfirmationEvent
    }

export type ResearchQuestionPendingAction =
  | ResearchQuestionEvent["action"]
  | null

export type ResearchQuestionWorkspaceProps = {
  content: Loadable<ResearchQuestionViewModel>
  canCreate: boolean
  capabilities: ResearchQuestionCapabilityAvailability
  pendingAction: ResearchQuestionPendingAction
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: ResearchQuestionEvent) => void
}
