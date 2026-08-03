import type {
  JobPublic,
  LiteratureCandidatePublic,
  LiteratureRecordPublic,
  LiteratureSearchRunPublic,
  ProjectPublic,
} from "@/api/adapter"

import type {
  LiteratureCandidateViewModel,
  LiteratureRecordViewModel,
  LiteratureSearchRunViewModel,
} from "./model"

const knownJobStatuses = new Set([
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

export function mapLiteratureSearchRun(
  run: LiteratureSearchRunPublic,
  job: JobPublic | null = null,
  project: ProjectPublic | null = null,
): LiteratureSearchRunViewModel {
  const knownStatus = knownJobStatuses.has(run.status)
  const jobMatchesRun =
    job !== null &&
    job.id === run.job_id &&
    job.project_id === run.project_id &&
    job.resource_type === "literature_search_run" &&
    job.resource_id === run.id
  const projectMatchesRun = project !== null && project.id === run.project_id
  const retryabilityKnown = run.job_id === null || jobMatchesRun
  const retryPermissionKnown =
    projectMatchesRun &&
    ["ACTIVE", "ARCHIVED", "DELETED"].includes(project.status) &&
    Array.isArray(project.allowed_actions)
  const retryable = jobMatchesRun && job.retryable
  const canRetry =
    knownStatus &&
    (run.status === "FAILED" || run.status === "DISPATCH_FAILED") &&
    retryabilityKnown &&
    retryPermissionKnown &&
    retryable &&
    project.allowed_actions.includes("job.retry")
  const retryDisabledReason = canRetry
    ? null
    : run.job_id === null
      ? "Search Run does not expose a retry Job."
      : !knownStatus
        ? "The Search Run status is unknown; retry remains disabled."
        : !retryabilityKnown
          ? "Job retryability is unavailable or does not match this Search Run."
          : !retryPermissionKnown
            ? "Job retry permission is unknown; retry remains disabled."
            : !retryable
              ? "The server marked this Job as non-retryable."
              : run.status !== "FAILED" && run.status !== "DISPATCH_FAILED"
                ? "Only failed Jobs can be retried."
                : "Current permissions do not allow Job retry."
  const tone =
    !knownStatus || run.degraded || run.cache_stale
      ? "degraded"
      : run.status === "COMPLETED"
        ? "success"
        : run.status === "FAILED" || run.status === "DISPATCH_FAILED"
          ? "danger"
          : "info"
  return {
    id: run.id,
    queryPlanId: run.query_plan_id,
    status: run.status,
    knownStatus,
    tone,
    progressJobId: run.job_id,
    resultCount: run.result_count,
    cacheHit: run.cache_hit,
    cacheStale: run.cache_stale,
    degraded: run.degraded || !knownStatus,
    limitations: run.limitations,
    errorCode: run.error_code,
    fetchedAt: run.fetched_at,
    retryabilityKnown,
    retryPermissionKnown,
    retryable,
    canRetry,
    retryDisabledReason,
  }
}

export function mapLiteratureCandidate(
  value: LiteratureCandidatePublic,
): LiteratureCandidateViewModel {
  return {
    id: value.id,
    title: value.title,
    authors: value.authors_text,
    year: value.publication_year,
    doi: value.doi,
    verificationStatus: value.verification_status,
    degraded: value.degraded,
    importedRecordId: value.imported_literature_record_id,
    canImport:
      Array.isArray(value.allowed_actions) &&
      value.allowed_actions.includes("literature_candidate.import"),
  }
}

export function mapLiteratureRecord(
  value: LiteratureRecordPublic,
): LiteratureRecordViewModel {
  return {
    id: value.id,
    title: value.title,
    authors: value.authors_text,
    year: value.publication_year,
    doi: value.doi,
    sourceType: value.source_type,
    verificationStatus: value.verification_status,
    decision: value.current_decision,
    documentId: value.document_id,
    canUploadDocument:
      Array.isArray(value.allowed_actions) &&
      value.allowed_actions.includes("document.upload"),
  }
}
