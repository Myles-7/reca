import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type {
  EvidenceAnalysisCapabilitiesViewModel,
  EvidenceAnalysisViewModel,
  EvidenceSearchViewModel,
} from "../model"

export type EvidenceSearchIntent = {
  query: string
  document_ids?: string[]
  top_k?: number
  retrieval_mode?: "KEYWORD" | "HYBRID"
  include_uncertain_literature?: boolean
}

export type EvidenceAnalysisEvent =
  | {
      action: "search-evidence"
      input: { query: string; request: EvidenceSearchIntent }
    }
  | {
      action: "create-summary"
      input: {
        includedLiteratureIds: string[]
        summaryTypes: Array<
          | "CONSENSUS"
          | "CONTROVERSY"
          | "EVIDENCE_GAP"
          | "COUNTEREXAMPLE"
          | "METHOD_DIFFERENCE"
          | "SAMPLE_DIFFERENCE"
          | "MISSING_LITERATURE"
        >
        requireEvidenceSpans: boolean
      }
    }
  | {
      action: "generate-topic"
      input: {
        summaryId: string
        researchQuestionVersionId: string
        userConstraints: Record<string, unknown>
      }
    }
  | { action: "retry-job"; input: { jobId: string } }

export type EvidenceAnalysisWorkspaceProps = {
  content: Loadable<EvidenceAnalysisViewModel>
  capabilities: EvidenceAnalysisCapabilitiesViewModel
  searchResult: EvidenceSearchViewModel | null
  pendingAction: EvidenceAnalysisEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: EvidenceAnalysisEvent) => void
}
