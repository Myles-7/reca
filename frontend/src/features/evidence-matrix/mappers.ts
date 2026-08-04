import type {
  EvidenceSpanPublic,
  LiteratureExtractionPublic,
  LiteratureMatrixEnvelope,
} from "@/api/adapter"

import {
  type EvidenceLocationViewModel,
  type EvidenceMatrixFieldViewModel,
  type EvidenceMatrixViewModel,
  literatureFieldCodes,
} from "./model"

const extractionStatuses = new Set([
  "DRAFT",
  "EXTRACTING",
  "NEEDS_REVIEW",
  "CONFIRMED",
  "SUPERSEDED",
  "INVALIDATED",
  "FAILED",
])
const confidenceStatuses = new Set(["HIGH", "MEDIUM", "LOW", "UNKNOWN"])
const confirmationStatuses = new Set(["UNREVIEWED", "CONFIRMED", "REJECTED"])
const evidenceStatuses = new Set([
  "UNASSESSED",
  "LOCATED",
  "LOCATION_UNCERTAIN",
  "NO_LOCATED_EVIDENCE",
])

function disabledReason(permissionsKnown: boolean, canCorrect: boolean) {
  if (!permissionsKnown) return "Field permissions are unknown."
  return canCorrect ? null : "The server did not allow field correction."
}

export function mapMatrixField(
  field: LiteratureMatrixEnvelope["data"][number]["fields"][number],
  extraction: LiteratureExtractionPublic | null = null,
): EvidenceMatrixFieldViewModel {
  const detail = extraction?.fields.find(
    (item) => item.field_code === field.field_code,
  )
  const permissionsKnown = detail
    ? Array.isArray(detail.allowed_actions)
    : false
  const canCorrect =
    permissionsKnown &&
    (detail?.allowed_actions.includes("literature_extraction_field.update") ??
      false)
  const canConfirm =
    permissionsKnown &&
    (detail?.allowed_actions.includes("literature_extraction_field.update") ??
      false)
  const knownStatus =
    confidenceStatuses.has(field.confidence_level) &&
    confirmationStatuses.has(field.confirmation_status) &&
    evidenceStatuses.has(field.evidence_status)
  return {
    fieldId: detail?.id ?? null,
    code: field.field_code,
    valueText: field.value_text,
    valueJson: field.value_json,
    confidenceLevel: field.confidence_level,
    confidenceScore: field.confidence_score,
    confirmationStatus: field.confirmation_status,
    evidenceStatus: field.evidence_status,
    evidenceSpanId: field.evidence_span_id,
    evidenceLimitations: field.evidence_limitations,
    lockVersion: field.lock_version,
    knownStatus,
    tone: !knownStatus
      ? "degraded"
      : field.evidence_status === "NO_LOCATED_EVIDENCE"
        ? "danger"
        : field.evidence_status === "LOCATION_UNCERTAIN" ||
            field.confidence_level === "LOW"
          ? "warning"
          : field.confirmation_status === "CONFIRMED"
            ? "success"
            : "info",
    permissionsKnown,
    canCorrect,
    canConfirm,
    correctionDisabledReason: disabledReason(permissionsKnown, canCorrect),
  }
}

export function mapEvidenceMatrix(
  envelope: LiteratureMatrixEnvelope,
  extractions: readonly LiteratureExtractionPublic[] = [],
): EvidenceMatrixViewModel {
  const permissionsKnown = Array.isArray(envelope.allowed_actions)
  const rows = envelope.data.map((row) => {
    const extraction =
      extractions.find((item) => item.id === row.extraction_id) ?? null
    const rowPermissionsKnown = Array.isArray(row.allowed_actions)
    const extractionStatusKnown =
      row.extraction_status === null ||
      extractionStatuses.has(row.extraction_status)
    return {
      literatureRecordId: row.literature_record_id,
      documentId: row.document_id,
      extractionId: row.extraction_id,
      extractionStatus: row.extraction_status,
      extractionStatusKnown,
      title: row.title,
      authors: row.authors_text,
      year: row.publication_year,
      decision: row.current_decision,
      fields: literatureFieldCodes.map((code) => {
        const field = row.fields.find((item) => item.field_code === code)
        return mapMatrixField(
          field ?? {
            field_code: code,
            value_text: null,
            value_json: null,
            confidence_level: "UNKNOWN",
            confidence_score: null,
            confirmation_status: "UNREVIEWED",
            evidence_status: "UNASSESSED",
            evidence_span_id: null,
            evidence_limitations: null,
            lock_version: null,
          },
          extraction,
        )
      }),
      permissionsKnown: rowPermissionsKnown,
      canCreateExtraction:
        rowPermissionsKnown &&
        row.allowed_actions.includes("literature.extract"),
      canCreateEvidence:
        permissionsKnown &&
        envelope.allowed_actions.includes("evidence_span.create"),
      canDecide:
        rowPermissionsKnown &&
        row.allowed_actions.includes("literature.decide"),
    }
  })
  return {
    rows,
    fixedFieldCodes: literatureFieldCodes,
    permissionsKnown,
    allowedActions: permissionsKnown ? envelope.allowed_actions : [],
    page: envelope.pagination.page,
    pageSize: envelope.pagination.page_size,
    total: envelope.pagination.total,
    degraded:
      !permissionsKnown ||
      rows.some(
        (row) =>
          !row.permissionsKnown ||
          !row.extractionStatusKnown ||
          row.fields.some((field) => !field.knownStatus),
      ),
  }
}

export function mapEvidenceLocation(
  span: EvidenceSpanPublic,
): EvidenceLocationViewModel {
  const knownStatus =
    ["EXTRACTED", "LOCATED", "VERIFIED", "LOCATION_UNCERTAIN"].includes(
      span.location_verification_status,
    ) &&
    ["UNREVIEWED", "REVIEWED", "CONFIRMED", "REJECTED"].includes(
      span.review_status,
    )
  const permissionsKnown = Array.isArray(span.allowed_actions)
  const hasCoordinates = (span.bounding_boxes?.length ?? 0) > 0
  const canVerify =
    permissionsKnown &&
    span.allowed_actions.includes("evidence_span.verify") &&
    hasCoordinates &&
    span.parser_type !== "PYPDF"
  const canReject =
    permissionsKnown && span.allowed_actions.includes("evidence_span.reject")
  return {
    evidenceSpanId: span.id,
    documentId: span.document_id,
    pageNumber: span.page_number,
    sourceText: span.source_text,
    sourceTextHash: span.source_text_hash,
    boundingBoxes: span.bounding_boxes ?? [],
    hasCoordinates,
    parserType: span.parser_type,
    parserCoverage: span.parser_coverage,
    locationStatus: span.location_verification_status,
    reviewStatus: span.review_status,
    readScope: span.user_declared_read_scope,
    knownStatus,
    tone: !knownStatus
      ? "degraded"
      : span.location_verification_status === "VERIFIED"
        ? "success"
        : span.location_verification_status === "LOCATION_UNCERTAIN"
          ? "warning"
          : "info",
    permissionsKnown,
    canVerify,
    canReject,
    verifyDisabledReason: canVerify
      ? null
      : !permissionsKnown
        ? "Evidence permissions are unknown."
        : !hasCoordinates || span.parser_type === "PYPDF"
          ? "Trusted coordinates are required before location verification."
          : "The server did not allow evidence verification.",
  }
}
