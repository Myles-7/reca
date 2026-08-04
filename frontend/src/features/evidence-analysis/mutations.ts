import { useMutation, useQueryClient } from "@tanstack/react-query"

import { EvidenceApi, JobsApi } from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import { mapEvidenceSearch } from "./mappers"
import type {
  EvidenceAnalysisCapabilitiesViewModel,
  EvidenceAnalysisViewModel,
} from "./model"
import { evidenceAnalysisKeys } from "./queries"
import type { EvidenceAnalysisEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

export function canExecuteEvidenceAnalysisEvent(
  summary: EvidenceAnalysisViewModel | null,
  capabilities: EvidenceAnalysisCapabilitiesViewModel | null,
  event: EvidenceAnalysisEvent,
) {
  if (event.action === "search-evidence")
    return (
      capabilities?.permissionsKnown === true &&
      capabilities.canSearchEvidence &&
      event.input.query.trim().length > 0
    )
  if (event.action === "create-summary")
    return (
      capabilities?.permissionsKnown === true &&
      capabilities.canCreateSummary &&
      event.input.includedLiteratureIds.length > 0
    )
  if (!summary?.knownStatus || !summary.permissionsKnown) return false
  if (event.action === "generate-topic")
    return (
      summary.canGenerateTopics && summary.summaryId === event.input.summaryId
    )
  return (
    summary.canRetry &&
    summary.jobId !== null &&
    summary.jobId === event.input.jobId
  )
}

async function execute(projectId: string, event: EvidenceAnalysisEvent) {
  if (event.action === "search-evidence")
    return mapEvidenceSearch(
      await EvidenceApi.search(projectId, event.input.request),
    )
  if (event.action === "create-summary")
    return EvidenceApi.createSummary(
      projectId,
      {
        included_literature_ids: event.input.includedLiteratureIds,
        summary_types: event.input.summaryTypes,
        require_evidence_spans: event.input.requireEvidenceSpans,
      },
      key(),
    )
  if (event.action === "generate-topic")
    return EvidenceApi.generateTopics(
      projectId,
      {
        research_question_version_id: event.input.researchQuestionVersionId,
        evidence_set_summary_id: event.input.summaryId,
        candidate_count: 3,
        user_constraints: event.input.userConstraints,
      },
      key(),
    )
  return JobsApi.retry(event.input.jobId, key())
}

export function useEvidenceAnalysisMutation(projectId: string) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: (event: EvidenceAnalysisEvent) => execute(projectId, event),
    onSuccess: (result, event) => {
      if (event.action === "create-summary" && result && "data" in result)
        void client.invalidateQueries({
          queryKey: evidenceAnalysisKeys.summary(result.data.id),
        })
      if (event.action === "retry-job")
        void client.invalidateQueries({
          queryKey: ["evidence-set-summaries"],
        })
    },
  })
  return {
    mutate: mutation.mutate,
    pendingAction: mutation.isPending
      ? (mutation.variables?.action ?? null)
      : null,
    uiError: mutation.error ? mapUiError(mutation.error) : null,
  }
}
