import type { Loadable, UiErrorViewModel } from "../../projects/model"
import type {
  EvidenceMatrixViewModel,
  LiteratureDecision,
  LiteratureFieldCode,
  PdfEvidenceViewerViewModel,
} from "../model"

export type EvidenceMatrixEvent =
  | {
      action: "filter"
      input: { includedOnly: boolean; fieldCodes: LiteratureFieldCode[] }
    }
  | {
      action: "sort"
      input: {
        sort: "created_at" | "title" | "year" | "decision"
        order: "asc" | "desc"
      }
    }
  | {
      action: "open-pdf-location"
      input: {
        literatureRecordId: string
        documentId: string
        extractionId: string | null
        fieldCode: LiteratureFieldCode | null
        fieldId: string | null
        evidenceSpanId: string | null
        pageNumber: number | null
      }
    }
  | {
      action: "create-extraction"
      input: {
        literatureRecordId: string
        documentId: string
        fieldCodes: readonly LiteratureFieldCode[]
      }
    }
  | {
      action: "correct-field"
      input: {
        literatureRecordId: string
        extractionId: string
        fieldId: string
        lockVersion: number
        valueText: string | null
        evidenceSpanId: string | null
        reason: string
      }
    }
  | {
      action: "confirm-field"
      input: {
        literatureRecordId: string
        extractionId: string
        fieldId: string
        lockVersion: number
        valueText: string | null
        evidenceSpanId: string | null
        reason: string
      }
    }
  | {
      action: "create-evidence"
      input: {
        literatureRecordId: string
        documentId: string
        pageNumber: number
        sourceText: string
        boundingBoxes: Array<{
          page: number
          x: number
          y: number
          width: number
          height: number
        }>
        evidenceType:
          | "FIELD_SUPPORT"
          | "CLAIM_SUPPORT"
          | "CLAIM_CONTRADICTION"
          | "METHOD_DESCRIPTION"
          | "SAMPLE_DESCRIPTION"
          | "LIMITATION"
          | "OTHER"
        readScope: "UNKNOWN" | "ABSTRACT" | "SECTIONS" | "FULL_TEXT_DECLARED"
      }
    }
  | {
      action: "verify-evidence" | "reject-evidence"
      input: {
        literatureRecordId: string
        evidenceSpanId: string
        locationStatus:
          | "EXTRACTED"
          | "LOCATED"
          | "VERIFIED"
          | "LOCATION_UNCERTAIN"
        readScope: "UNKNOWN" | "ABSTRACT" | "SECTIONS" | "FULL_TEXT_DECLARED"
        reviewedPages: number[]
        note: string | null
      }
    }
  | {
      action: "decide-literature"
      input: {
        literatureRecordId: string
        decision: LiteratureDecision
        reasonCode:
          | "RELEVANT_OBJECT_AND_METHOD"
          | "OBJECT_MISMATCH"
          | "VARIABLE_MISMATCH"
          | "METHOD_MISMATCH"
          | "TYPE_MISMATCH"
          | "YEAR_MISMATCH"
          | "DUPLICATE"
          | "FULL_TEXT_UNAVAILABLE"
          | "QUALITY_ISSUE"
          | "OTHER"
          | null
        reasonText: string | null
      }
    }

export type EvidenceMatrixWorkspaceProps = {
  content: Loadable<EvidenceMatrixViewModel>
  pdfViewer: PdfEvidenceViewerViewModel | null
  selectedFieldId?: string
  pendingAction: EvidenceMatrixEvent["action"] | null
  mutationError: UiErrorViewModel | null
  onRetry: () => void
  onEvent: (event: EvidenceMatrixEvent) => void
}
