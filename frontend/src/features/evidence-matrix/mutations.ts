import { useMutation, useQueryClient } from "@tanstack/react-query"

import { EvidenceApi } from "@/api/adapter"

import { mapUiError } from "../projects/mappers"
import type {
  EvidenceLocationViewModel,
  EvidenceMatrixViewModel,
} from "./model"
import { evidenceMatrixKeys } from "./queries"
import type { EvidenceMatrixEvent } from "./ui/contracts"

const key = () => crypto.randomUUID()

export function canExecuteEvidenceMatrixEvent(
  matrix: EvidenceMatrixViewModel | null,
  event: EvidenceMatrixEvent,
  selectedSpan: EvidenceLocationViewModel | null = null,
) {
  if (!matrix?.permissionsKnown) return false
  if (
    event.action === "filter" ||
    event.action === "sort" ||
    event.action === "open-pdf-location"
  )
    return true
  const row = matrix.rows.find(
    (item) => item.literatureRecordId === event.input.literatureRecordId,
  )
  if (!row?.permissionsKnown) return false
  if (event.action === "verify-evidence")
    return (
      selectedSpan?.evidenceSpanId === event.input.evidenceSpanId &&
      selectedSpan.canVerify
    )
  if (event.action === "reject-evidence")
    return (
      selectedSpan?.evidenceSpanId === event.input.evidenceSpanId &&
      selectedSpan.canReject
    )
  if (event.action === "create-extraction") return row.canCreateExtraction
  if (event.action === "create-evidence") return row.canCreateEvidence
  if (event.action === "decide-literature") return row.canDecide
  if (event.action === "correct-field" || event.action === "confirm-field") {
    if (row.extractionId !== event.input.extractionId) return false
    const field = row.fields.find(
      (item) => item.fieldId === event.input.fieldId,
    )
    if (!field?.permissionsKnown) return false
    return event.action === "correct-field"
      ? field.canCorrect
      : field.canConfirm
  }
  return false
}

async function execute(event: EvidenceMatrixEvent) {
  if (event.action === "create-extraction") {
    return EvidenceApi.createExtraction(
      event.input.documentId,
      {
        literature_record_id: event.input.literatureRecordId,
        field_codes: [...event.input.fieldCodes],
      },
      key(),
    )
  }
  if (event.action === "correct-field" || event.action === "confirm-field") {
    return EvidenceApi.correctField(
      event.input.fieldId,
      event.input.lockVersion,
      {
        value_text: event.input.valueText,
        evidence_span_id: event.input.evidenceSpanId,
        correction_reason: event.input.reason,
        confirmation_status:
          event.action === "confirm-field" ? "CONFIRMED" : "UNREVIEWED",
      },
      key(),
    )
  }
  if (event.action === "create-evidence") {
    return EvidenceApi.createSpan(
      event.input.documentId,
      {
        page_number: event.input.pageNumber,
        source_text: event.input.sourceText,
        bounding_boxes: event.input.boundingBoxes,
        evidence_type: event.input.evidenceType,
        user_declared_read_scope: event.input.readScope,
      },
      key(),
    )
  }
  if (
    event.action === "verify-evidence" ||
    event.action === "reject-evidence"
  ) {
    return EvidenceApi.verifySpan(
      event.input.evidenceSpanId,
      {
        location_verification_status: event.input.locationStatus,
        user_declared_read_scope: event.input.readScope,
        reviewed_page_numbers: event.input.reviewedPages,
        note: event.input.note,
      },
      key(),
    )
  }
  if (event.action === "decide-literature") {
    return EvidenceApi.decide(
      event.input.literatureRecordId,
      {
        decision: event.input.decision,
        reason_code: event.input.reasonCode,
        reason_text: event.input.reasonText,
      },
      key(),
    )
  }
  return null
}

export function useEvidenceMatrixMutation(projectId: string) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: execute,
    onSuccess: async (_result, event) => {
      const invalidations: Promise<unknown>[] = [
        client.invalidateQueries({
          queryKey: ["projects", projectId, "evidence-matrix"],
        }),
      ]
      if (
        event.action === "correct-field" ||
        event.action === "confirm-field"
      ) {
        invalidations.push(
          client.invalidateQueries({
            queryKey: evidenceMatrixKeys.extraction(event.input.extractionId),
          }),
        )
      }
      if (
        event.action === "verify-evidence" ||
        event.action === "reject-evidence"
      ) {
        invalidations.push(
          client.invalidateQueries({
            queryKey: evidenceMatrixKeys.span(event.input.evidenceSpanId),
          }),
        )
      }
      await Promise.all(invalidations)
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
