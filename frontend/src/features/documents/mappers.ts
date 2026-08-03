import type {
  DocumentPagePublic,
  DocumentPublic,
  JobPublic,
  ProjectPublic,
} from "@/api/adapter"

import type {
  DocumentJobViewModel,
  DocumentPageViewModel,
  DocumentViewModel,
} from "./model"

const statuses = new Set([
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

function statusTone(status: string, known: boolean): DocumentViewModel["tone"] {
  if (!known) return "degraded"
  if (status === "COMPLETED") return "success"
  if (status === "FAILED" || status === "DISPATCH_FAILED") return "danger"
  if (status === "NEEDS_REVIEW") return "warning"
  return "info"
}

export function mapDocument(value: DocumentPublic): DocumentViewModel {
  const knownStatus = statuses.has(value.parse_status)
  const lowConfidence =
    value.parse_confidence === "LOW" || value.parser_type === "PYPDF"
  return {
    id: value.id,
    projectId: value.project_id,
    artifactId: value.artifact_id,
    literatureRecordId: value.literature_record_id,
    documentType: value.document_type,
    parserType: value.parser_type ?? "NONE",
    parseStatus: value.parse_status,
    knownStatus,
    tone:
      !knownStatus || lowConfidence
        ? "degraded"
        : statusTone(value.parse_status, true),
    parseConfidence: value.parse_confidence ?? "UNKNOWN",
    pageCount: value.page_count,
    language: value.language,
    isScanned: value.is_scanned,
    permissions: {
      canParse:
        Array.isArray(value.allowed_actions) &&
        value.allowed_actions.includes("document.parse"),
    },
    updatedAt: value.updated_at,
  }
}

export function mapDocumentPage(
  value: DocumentPagePublic,
): DocumentPageViewModel {
  return {
    pageNumber: value.page_number,
    printedPageLabel: value.printed_page_label,
    textContent: value.text_content,
  }
}

export function mapDocumentJob(
  value: JobPublic,
  document: DocumentPublic,
  project: ProjectPublic | null,
): DocumentJobViewModel {
  const knownStatus = statuses.has(value.status)
  const documentKnownStatus = statuses.has(document.parse_status)
  const matchesDocument =
    value.project_id === document.project_id &&
    value.resource_type === "document" &&
    value.resource_id === document.id
  const retryPermissionKnown =
    project !== null &&
    project.id === document.project_id &&
    ["ACTIVE", "ARCHIVED", "DELETED"].includes(project.status) &&
    Array.isArray(project.allowed_actions)
  const retryable = matchesDocument && knownStatus && value.retryable
  const canRetry =
    documentKnownStatus &&
    knownStatus &&
    (value.status === "FAILED" || value.status === "DISPATCH_FAILED") &&
    retryable &&
    retryPermissionKnown &&
    project.allowed_actions.includes("job.retry")
  const retryDisabledReason = canRetry
    ? null
    : !matchesDocument
      ? "Job projection does not match this Document."
      : !documentKnownStatus
        ? "Document parse status is unknown; retry remains disabled."
        : !knownStatus
          ? "Job status is unknown; retry remains disabled."
          : !retryPermissionKnown
            ? "Job retry permission is unknown; retry remains disabled."
            : !retryable
              ? "The server marked this Job as non-retryable."
              : value.status !== "FAILED" && value.status !== "DISPATCH_FAILED"
                ? "Only failed Jobs can be retried."
                : "Current permissions do not allow Job retry."
  return {
    id: value.id,
    status: value.status,
    knownStatus,
    tone: statusTone(value.status, knownStatus),
    progressPercent: value.progress_percent,
    currentStep: value.current_step,
    retryable,
    retryPermissionKnown,
    canRetry,
    retryDisabledReason,
    errorCode: value.error?.code ?? null,
    errorMessage: value.error?.message ?? null,
  }
}
