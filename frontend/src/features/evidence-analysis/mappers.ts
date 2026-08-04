import type {
  EvidenceSearchEnvelope,
  EvidenceSetSummaryPublic,
  LiteratureMatrixEnvelope,
} from "@/api/adapter"

import type {
  EvidenceAnalysisCapabilitiesViewModel,
  EvidenceAnalysisItemViewModel,
  EvidenceAnalysisViewModel,
  EvidenceSearchViewModel,
} from "./model"

export function mapEvidenceAnalysisCapabilities(
  envelope: LiteratureMatrixEnvelope,
): EvidenceAnalysisCapabilitiesViewModel {
  const permissionsKnown = Array.isArray(envelope.allowed_actions)
  const canSearchEvidence =
    permissionsKnown && envelope.allowed_actions.includes("evidence.search")
  const canCreateSummary =
    permissionsKnown &&
    envelope.allowed_actions.includes("evidence_summary.create")
  return {
    permissionsKnown,
    canSearchEvidence,
    canCreateSummary,
    disabledReason: !permissionsKnown
      ? "Evidence analysis permissions are unknown."
      : canSearchEvidence || canCreateSummary
        ? null
        : "The server did not allow evidence analysis creation.",
  }
}

const jobStatuses = new Set([
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

type SummaryItem = NonNullable<
  NonNullable<EvidenceSetSummaryPublic["result"]>["consensus_items"]
>[number]

function mapItem(
  kind: EvidenceAnalysisItemViewModel["kind"],
  item: SummaryItem,
): EvidenceAnalysisItemViewModel {
  return {
    kind,
    claim: item.claim_text,
    strength: item.strength ?? "UNKNOWN",
    limitations: item.limitations ?? [],
    sources: {
      literatureRecordIds: item.supporting_literature_ids ?? [],
      contradictingLiteratureRecordIds: item.contradicting_literature_ids ?? [],
      evidenceSpanIds: item.evidence_span_ids ?? [],
    },
  }
}

export function mapEvidenceSummary(
  summary: EvidenceSetSummaryPublic,
): EvidenceAnalysisViewModel {
  const knownStatus = jobStatuses.has(summary.status)
  const permissionsKnown = Array.isArray(summary.allowed_actions)
  const result = summary.result
  const groups: Array<
    [EvidenceAnalysisItemViewModel["kind"], readonly SummaryItem[]]
  > = result
    ? [
        ["CONSENSUS", result.consensus_items ?? []],
        ["CONTROVERSY", result.controversy_items ?? []],
        ["EVIDENCE_GAP", result.evidence_gap_items ?? []],
        ["COUNTEREXAMPLE", result.counterexamples ?? []],
        ["METHOD_DIFFERENCE", result.method_difference_items ?? []],
        ["SAMPLE_DIFFERENCE", result.sample_difference_items ?? []],
        ["MISSING_LITERATURE", result.missing_literature ?? []],
      ]
    : []
  const canGenerateTopics =
    permissionsKnown &&
    summary.allowed_actions.includes("topic_generation.create")
  const canRetry =
    permissionsKnown && summary.allowed_actions.includes("job.retry")
  return {
    summaryId: summary.id,
    jobId: summary.job_id,
    status: summary.status,
    knownStatus,
    tone: !knownStatus
      ? "degraded"
      : summary.status === "COMPLETED"
        ? "success"
        : summary.status === "FAILED" || summary.status === "DISPATCH_FAILED"
          ? "danger"
          : "info",
    scopeStatement: summary.scope_statement,
    includedLiteratureIds: summary.included_literature_ids,
    items: groups.flatMap(([kind, items]) =>
      items.map((item) => mapItem(kind, item)),
    ),
    missingInformation: result?.missing_information ?? [],
    limitations: result?.limitations ?? [],
    permissionsKnown,
    canSearchEvidence: false,
    canCreateSummary: false,
    canGenerateTopics,
    canRetry: canRetry && summary.job_id !== null,
    actionDisabledReason: !knownStatus
      ? "Summary status is unknown."
      : !permissionsKnown
        ? "Summary permissions are unknown."
        : canGenerateTopics
          ? null
          : "The server did not allow topic generation.",
  }
}

export function mapEvidenceSearch(
  envelope: EvidenceSearchEnvelope,
): EvidenceSearchViewModel {
  return {
    query: envelope.data.query,
    retrievalRunId: envelope.data.retrieval_run_id,
    candidates: envelope.data.candidates.map((candidate) => ({
      candidateId: candidate.candidate_id,
      literatureRecordId: candidate.literature_record_id,
      documentId: candidate.document_id,
      pageNumber: candidate.page_number,
      sourceText: candidate.source_text,
      sourceTextHash: candidate.source_text_hash,
      evidenceSpanId: null,
      hasCoordinates: (candidate.bounding_boxes?.length ?? 0) > 0,
      limitations: candidate.limitations ?? [],
    })),
    limitations: envelope.data.limitations,
  }
}
