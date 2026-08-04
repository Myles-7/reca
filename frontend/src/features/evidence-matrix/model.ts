import type { SemanticTone } from "../projects/model"

export const literatureFieldCodes = [
  "TITLE",
  "AUTHORS",
  "YEAR",
  "RESEARCH_OBJECT",
  "SAMPLE_SIZE",
  "CORE_VARIABLES",
  "RESEARCH_DESIGN",
  "ANALYSIS_METHOD",
  "MAIN_CONCLUSION",
  "LIMITATION",
] as const

export type LiteratureFieldCode = (typeof literatureFieldCodes)[number]
export type LiteratureDecision = "INCLUDED" | "EXCLUDED" | "UNCERTAIN"

export type EvidenceLocationViewModel = {
  evidenceSpanId: string
  documentId: string
  pageNumber: number
  sourceText: string
  sourceTextHash: string
  boundingBoxes: readonly Record<string, unknown>[]
  hasCoordinates: boolean
  parserType: string | null
  parserCoverage: string
  locationStatus: string
  reviewStatus: string
  readScope: string
  knownStatus: boolean
  tone: SemanticTone
  permissionsKnown: boolean
  canVerify: boolean
  canReject: boolean
  verifyDisabledReason: string | null
}

export type EvidenceMatrixFieldViewModel = {
  fieldId: string | null
  code: LiteratureFieldCode
  valueText: string | null
  valueJson: Record<string, unknown> | readonly unknown[] | null
  confidenceLevel: string
  confidenceScore: number | null
  confirmationStatus: string
  evidenceStatus: string
  evidenceSpanId: string | null
  evidenceLimitations: string | null
  lockVersion: number | null
  knownStatus: boolean
  tone: SemanticTone
  permissionsKnown: boolean
  canCorrect: boolean
  canConfirm: boolean
  correctionDisabledReason: string | null
}

export type EvidenceMatrixRowViewModel = {
  literatureRecordId: string
  documentId: string | null
  extractionId: string | null
  extractionStatus: string | null
  extractionStatusKnown: boolean
  title: string
  authors: string | null
  year: number | null
  decision: LiteratureDecision
  fields: readonly EvidenceMatrixFieldViewModel[]
  permissionsKnown: boolean
  canCreateExtraction: boolean
  canCreateEvidence: boolean
  canDecide: boolean
}

export type EvidenceMatrixViewModel = {
  rows: readonly EvidenceMatrixRowViewModel[]
  fixedFieldCodes: typeof literatureFieldCodes
  permissionsKnown: boolean
  allowedActions: readonly string[]
  page: number
  pageSize: number
  total: number
  degraded: boolean
}

export type PdfEvidenceViewerViewModel = {
  documentId: string
  authorizedPdfUrl: string | null
  selectedPage: number
  selectedSpan: EvidenceLocationViewModel | null
  pageText: string | null
  parserType: string | null
  hasTextLayer: boolean
  degradedReason: string | null
}
