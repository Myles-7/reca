import type { UiErrorViewModel } from "../../projects/model"
import type {
  EvidenceMatrixViewModel,
  LiteratureFieldCode,
  PdfEvidenceViewerViewModel,
} from "../model"
import type { EvidenceMatrixWorkspaceProps } from "../ui/contracts"

const noop = () => undefined
const noEvent: EvidenceMatrixWorkspaceProps["onEvent"] = () => undefined
const error = (
  code: string,
  forbidden = false,
  conflict = false,
): UiErrorViewModel => ({
  title: code,
  message: "Contract fixture error.",
  code,
  requestId: `request-${code.toLowerCase()}`,
  retryable: !forbidden && !conflict,
  forbidden,
  notFound: false,
  conflict,
})

const fieldSeeds: ReadonlyArray<
  readonly [LiteratureFieldCode, string, string, string, string, string | null]
> = [
  [
    "TITLE",
    "Generative AI and learning engagement",
    "HIGH",
    "LOCATED",
    "CONFIRMED",
    "span-title",
  ],
  ["AUTHORS", "Li; Smith", "HIGH", "LOCATED", "CONFIRMED", "span-authors"],
  ["YEAR", "2025", "MEDIUM", "LOCATION_UNCERTAIN", "UNREVIEWED", "span-year"],
  [
    "RESEARCH_OBJECT",
    "Teacher education students",
    "HIGH",
    "LOCATED",
    "CONFIRMED",
    "span-object",
  ],
  ["SAMPLE_SIZE", "n=248", "LOW", "NO_LOCATED_EVIDENCE", "UNREVIEWED", null],
  [
    "CORE_VARIABLES",
    "AI use; learning engagement",
    "MEDIUM",
    "LOCATED",
    "UNREVIEWED",
    "span-variables",
  ],
  [
    "RESEARCH_DESIGN",
    "Cross-sectional survey",
    "HIGH",
    "LOCATED",
    "CONFIRMED",
    "span-design",
  ],
  [
    "ANALYSIS_METHOD",
    "Multiple regression",
    "MEDIUM",
    "LOCATED",
    "UNREVIEWED",
    "span-analysis",
  ],
  [
    "MAIN_CONCLUSION",
    "Positive association in the current sample",
    "MEDIUM",
    "LOCATED",
    "UNREVIEWED",
    "span-conclusion",
  ],
  [
    "LIMITATION",
    "Single institution and self-report measures",
    "HIGH",
    "LOCATED",
    "CONFIRMED",
    "span-limitation",
  ],
]
const fields: EvidenceMatrixViewModel["rows"][number]["fields"] =
  fieldSeeds.map(
    (
      [
        code,
        valueText,
        confidenceLevel,
        evidenceStatus,
        confirmationStatus,
        evidenceSpanId,
      ],
      index,
    ) => ({
      fieldId: `field-${index + 1}`,
      code,
      valueText,
      valueJson: null,
      confidenceLevel,
      confidenceScore:
        confidenceLevel === "HIGH"
          ? 0.91
          : confidenceLevel === "MEDIUM"
            ? 0.68
            : 0.34,
      confirmationStatus,
      evidenceStatus,
      evidenceSpanId,
      evidenceLimitations:
        evidenceStatus === "NO_LOCATED_EVIDENCE"
          ? "NO_LOCATED_EVIDENCE"
          : evidenceStatus === "LOCATION_UNCERTAIN"
            ? "Repeated year text on page."
            : null,
      lockVersion: 2,
      knownStatus: true,
      tone:
        evidenceStatus === "NO_LOCATED_EVIDENCE"
          ? "danger"
          : evidenceStatus === "LOCATION_UNCERTAIN" || confidenceLevel === "LOW"
            ? "warning"
            : confirmationStatus === "CONFIRMED"
              ? "success"
              : "info",
      permissionsKnown: true,
      canCorrect: true,
      canConfirm: true,
      correctionDisabledReason: null,
    }),
  )

const readyModel: EvidenceMatrixViewModel = {
  rows: [
    {
      literatureRecordId: "literature-1",
      documentId: "document-1",
      extractionId: "extraction-1",
      extractionStatus: "NEEDS_REVIEW",
      extractionStatusKnown: true,
      title: "Generative AI and learning engagement",
      authors: "Li; Smith",
      year: 2025,
      decision: "INCLUDED",
      fields,
      permissionsKnown: true,
      canCreateExtraction: false,
      canCreateEvidence: true,
      canDecide: true,
    },
    {
      literatureRecordId: "literature-2",
      documentId: "document-2",
      extractionId: "extraction-2",
      extractionStatus: "CONFIRMED",
      extractionStatusKnown: true,
      title: "Counterevidence from a longitudinal cohort",
      authors: "Rivera; Patel",
      year: 2024,
      decision: "EXCLUDED",
      fields,
      permissionsKnown: true,
      canCreateExtraction: false,
      canCreateEvidence: true,
      canDecide: true,
    },
    {
      literatureRecordId: "literature-3",
      documentId: null,
      extractionId: null,
      extractionStatus: null,
      extractionStatusKnown: true,
      title: "Methods comparison awaiting full text",
      authors: null,
      year: null,
      decision: "UNCERTAIN",
      fields,
      permissionsKnown: true,
      canCreateExtraction: false,
      canCreateEvidence: false,
      canDecide: true,
    },
  ],
  fixedFieldCodes: [
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
  ],
  permissionsKnown: true,
  allowedActions: ["literature_decision.create"],
  page: 1,
  pageSize: 20,
  total: 3,
  degraded: false,
}

const pdf: PdfEvidenceViewerViewModel = {
  documentId: "document-1",
  authorizedPdfUrl: "/dev-only/authorized.pdf",
  selectedPage: 4,
  selectedSpan: {
    evidenceSpanId: "span-title",
    documentId: "document-1",
    pageNumber: 4,
    sourceText:
      "Generative AI use was positively associated with learning engagement.",
    sourceTextHash: "a".repeat(64),
    boundingBoxes: [{ page: 4, x: 0.12, y: 0.22, width: 0.58, height: 0.04 }],
    hasCoordinates: true,
    parserType: "PDFJS",
    parserCoverage: "FULL_TEXT",
    locationStatus: "VERIFIED",
    reviewStatus: "CONFIRMED",
    readScope: "SECTIONS",
    knownStatus: true,
    tone: "success",
    permissionsKnown: true,
    canVerify: false,
    canReject: true,
    verifyDisabledReason: "Already verified.",
  },
  pageText:
    "Generative AI use was positively associated with learning engagement.",
  parserType: "PDFJS",
  hasTextLayer: true,
  degradedReason: null,
}

const base: EvidenceMatrixWorkspaceProps = {
  content: { state: "ready", data: readyModel },
  pdfViewer: pdf,
  pendingAction: null,
  mutationError: null,
  onRetry: noop,
  onEvent: noEvent,
}
const make = (
  id: string,
  label: string,
  props: EvidenceMatrixWorkspaceProps,
  behavior: string,
) => ({ id, label, behavior, props })

export const evidenceMatrixFixtures = [
  make(
    "ready",
    "Ready",
    base,
    "Fixed ten-field matrix with all decision states.",
  ),
  make(
    "loading",
    "Loading",
    {
      ...base,
      content: { state: "loading", label: "Loading evidence matrix" },
    },
    "Stable loading contract.",
  ),
  make(
    "empty",
    "Empty",
    {
      ...base,
      content: { state: "empty", message: "No literature is available." },
      pdfViewer: null,
    },
    "No fabricated rows.",
  ),
  make(
    "error",
    "Error",
    {
      ...base,
      content: { state: "error", error: error("MATRIX_LOAD_FAILED") },
      pdfViewer: null,
    },
    "Retryable load error.",
  ),
  make(
    "forbidden",
    "Forbidden",
    {
      ...base,
      content: { state: "error", error: error("PROJECT_NOT_FOUND", true) },
      pdfViewer: null,
    },
    "No-disclosure access state.",
  ),
  make(
    "read-only",
    "Read-only",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...readyModel,
          rows: readyModel.rows.map((row) => ({
            ...row,
            canCreateEvidence: false,
            canDecide: false,
            fields: row.fields.map((field) => ({
              ...field,
              canCorrect: false,
              canConfirm: false,
              correctionDisabledReason: "Read-only access.",
            })),
          })),
        },
      },
    },
    "All write actions disabled.",
  ),
  make(
    "permissions-unknown",
    "Permissions unknown",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...readyModel,
          permissionsKnown: false,
          degraded: true,
          rows: readyModel.rows.map((row) => ({
            ...row,
            permissionsKnown: false,
            canCreateEvidence: false,
            canDecide: false,
          })),
        },
      },
    },
    "Unknown permissions fail closed.",
  ),
  make(
    "pending",
    "Pending",
    { ...base, pendingAction: "correct-field" },
    "Intent pending without optimistic success.",
  ),
  make(
    "conflict",
    "Conflict",
    { ...base, mutationError: error("STALE_IF_MATCH", false, true) },
    "Server version conflict.",
  ),
  make(
    "degraded",
    "Degraded",
    {
      ...base,
      content: { state: "ready", data: { ...readyModel, degraded: true } },
    },
    "Partial projection remains visible.",
  ),
  make(
    "unknown",
    "Unknown status",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...readyModel,
          degraded: true,
          rows: readyModel.rows.map((row, index) =>
            index
              ? row
              : {
                  ...row,
                  extractionStatus: "FUTURE_STATE",
                  extractionStatusKnown: false,
                  permissionsKnown: false,
                  canDecide: false,
                },
          ),
        },
      },
    },
    "Unknown status fails closed.",
  ),
  make(
    "long-content",
    "Long content",
    {
      ...base,
      content: {
        state: "ready",
        data: {
          ...readyModel,
          rows: readyModel.rows.map((row, index) =>
            index
              ? row
              : {
                  ...row,
                  title:
                    "A very long multi-institutional longitudinal investigation of heterogeneous generative artificial intelligence practices and multidimensional engagement outcomes across teacher education systems",
                },
          ),
        },
      },
    },
    "Long scientific content wraps.",
  ),
  make(
    "pdf-no-coordinates",
    "PDF no coordinates",
    {
      ...base,
      pdfViewer: {
        ...pdf,
        selectedSpan: pdf.selectedSpan
          ? {
              ...pdf.selectedSpan,
              boundingBoxes: [],
              hasCoordinates: false,
              parserType: "PYPDF",
              tone: "warning",
            }
          : null,
        parserType: "PYPDF",
        hasTextLayer: false,
        degradedReason: "Text is available without trusted coordinates.",
      },
    },
    "pypdf never invents boxes.",
  ),
] as const satisfies ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: EvidenceMatrixWorkspaceProps
}>
