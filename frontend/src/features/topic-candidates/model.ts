import type { SemanticTone } from "../projects/model"

export type TopicCandidateSourceViewModel = {
  literatureRecordId: string | null
  evidenceSpanId: string | null
  relationType: string
  explanation: string | null
}

export type TopicCandidateViewModel = {
  id: string
  order: 1 | 2 | 3
  question: string
  researchObject: string | null
  variables: Record<string, unknown> | null
  literatureBasis: string | null
  possibleInnovation: string | null
  dataRequirements: Record<string, unknown> | null
  recommendedMethod: string | null
  literatureBasisLevel: string | null
  dataAvailability: string | null
  methodDifficulty: string | null
  timeFeasibility: string | null
  ethicalRisk: string | null
  majorRisks: readonly string[]
  limitations: readonly string[]
  supervisorConfirmationItems: readonly string[]
  status: string
  knownStatus: boolean
  sources: readonly TopicCandidateSourceViewModel[]
}

export type TopicCandidatesViewModel = {
  runId: string
  researchQuestionVersionId: string
  evidenceSummaryId: string
  status: string
  knownStatus: boolean
  tone: SemanticTone
  candidates: readonly TopicCandidateViewModel[]
  exactlyThree: boolean
  sourcesValid: boolean
  permissionsKnown: boolean
  canGenerate: boolean
  failureReason: string | null
}

export type TopicRunProjection = {
  id: string
  project_id: string
  research_question_version_id: string
  evidence_summary_id: string | null
  status: string
  allowed_actions?: readonly string[]
  candidates: ReadonlyArray<{
    id: string
    candidate_order: number
    question_text: string
    research_object: string | null
    variables: Record<string, unknown> | null
    literature_basis: string | null
    possible_innovation: string | null
    data_requirements: Record<string, unknown> | null
    recommended_method: string | null
    literature_basis_level: string | null
    data_availability: string | null
    method_difficulty: string | null
    time_feasibility: string | null
    ethical_risk: string | null
    major_risks: readonly string[] | null
    limitations: readonly string[]
    supervisor_confirmation_items: readonly string[] | null
    status: string
    sources: ReadonlyArray<{
      literature_record_id?: string | null
      evidence_span_id?: string | null
      relation_type: string
      explanation?: string | null
    }>
  }>
}
