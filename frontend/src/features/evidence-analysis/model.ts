import type { SemanticTone } from "../projects/model"

export type EvidenceSourceRefViewModel = {
  literatureRecordIds: readonly string[]
  contradictingLiteratureRecordIds: readonly string[]
  evidenceSpanIds: readonly string[]
}

export type EvidenceAnalysisItemViewModel = {
  kind:
    | "CONSENSUS"
    | "CONTROVERSY"
    | "EVIDENCE_GAP"
    | "COUNTEREXAMPLE"
    | "METHOD_DIFFERENCE"
    | "SAMPLE_DIFFERENCE"
    | "MISSING_LITERATURE"
  claim: string
  strength: string
  limitations: readonly string[]
  sources: EvidenceSourceRefViewModel
}

export type EvidenceSearchCandidateViewModel = {
  candidateId: string
  literatureRecordId: string
  documentId: string
  pageNumber: number
  sourceText: string
  sourceTextHash: string
  evidenceSpanId: null
  hasCoordinates: boolean
  limitations: readonly string[]
}

export type EvidenceAnalysisViewModel = {
  summaryId: string
  jobId: string | null
  status: string
  knownStatus: boolean
  tone: SemanticTone
  scopeStatement: string
  includedLiteratureIds: readonly string[]
  items: readonly EvidenceAnalysisItemViewModel[]
  missingInformation: readonly string[]
  limitations: readonly string[]
  permissionsKnown: boolean
  canSearchEvidence: boolean
  canCreateSummary: boolean
  canGenerateTopics: boolean
  canRetry: boolean
  actionDisabledReason: string | null
}

export type EvidenceSearchViewModel = {
  query: string
  retrievalRunId: string
  candidates: readonly EvidenceSearchCandidateViewModel[]
  limitations: readonly string[]
}

export type EvidenceAnalysisCapabilitiesViewModel = {
  permissionsKnown: boolean
  canSearchEvidence: boolean
  canCreateSummary: boolean
  disabledReason: string | null
}
