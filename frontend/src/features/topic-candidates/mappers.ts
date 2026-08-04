import type { TopicCandidatesViewModel, TopicRunProjection } from "./model"

const runStatuses = new Set([
  "DRAFT",
  "QUEUED",
  "RUNNING",
  "NEEDS_REVIEW",
  "COMPLETED",
  "FAILED",
  "CANCEL_REQUESTED",
  "CANCELLED",
  "DISPATCH_FAILED",
])
const candidateStatuses = new Set([
  "PROPOSED",
  "SHORTLISTED",
  "REJECTED",
  "ADOPTED",
])

export function mapTopicCandidates(
  run: TopicRunProjection,
): TopicCandidatesViewModel {
  const orders = run.candidates.map((item) => item.candidate_order)
  const exactlyThree =
    run.candidates.length === 3 &&
    new Set(orders).size === 3 &&
    orders.every((order) => [1, 2, 3].includes(order))
  const sourcesValid = run.candidates.every(
    (candidate) =>
      candidate.sources.length > 0 &&
      candidate.sources.every(
        (source) =>
          (source.literature_record_id == null) !==
          (source.evidence_span_id == null),
      ),
  )
  const knownStatus = runStatuses.has(run.status)
  const permissionsKnown = Array.isArray(run.allowed_actions)
  return {
    runId: run.id,
    researchQuestionVersionId: run.research_question_version_id,
    evidenceSummaryId: run.evidence_summary_id ?? "",
    status: run.status,
    knownStatus,
    tone:
      !knownStatus || !exactlyThree || !sourcesValid
        ? "degraded"
        : run.status === "COMPLETED"
          ? "success"
          : run.status === "FAILED" || run.status === "DISPATCH_FAILED"
            ? "danger"
            : "info",
    candidates: run.candidates
      .slice()
      .sort((a, b) => a.candidate_order - b.candidate_order)
      .map((candidate) => ({
        id: candidate.id,
        order: candidate.candidate_order as 1 | 2 | 3,
        question: candidate.question_text,
        researchObject: candidate.research_object,
        variables: candidate.variables,
        literatureBasis: candidate.literature_basis,
        possibleInnovation: candidate.possible_innovation,
        dataRequirements: candidate.data_requirements,
        recommendedMethod: candidate.recommended_method,
        literatureBasisLevel: candidate.literature_basis_level,
        dataAvailability: candidate.data_availability,
        methodDifficulty: candidate.method_difficulty,
        timeFeasibility: candidate.time_feasibility,
        ethicalRisk: candidate.ethical_risk,
        majorRisks: candidate.major_risks ?? [],
        limitations: candidate.limitations ?? [],
        supervisorConfirmationItems:
          candidate.supervisor_confirmation_items ?? [],
        status: candidate.status,
        knownStatus: candidateStatuses.has(candidate.status),
        sources: candidate.sources.map((source) => ({
          literatureRecordId: source.literature_record_id ?? null,
          evidenceSpanId: source.evidence_span_id ?? null,
          relationType: source.relation_type,
          explanation: source.explanation ?? null,
        })),
      })),
    exactlyThree,
    sourcesValid,
    permissionsKnown,
    canGenerate:
      permissionsKnown &&
      (run.allowed_actions?.includes("topic_generation.create") ?? false),
    failureReason: !knownStatus
      ? "Topic run status is unknown."
      : !exactlyThree
        ? "The server projection does not contain exactly three ordered candidates."
        : !sourcesValid
          ? "At least one candidate has invalid or missing sources."
          : null,
  }
}
