import type { UiErrorViewModel } from "../../projects/model"
import type { DocumentWorkspaceProps } from "../ui/contracts"

const noop = () => undefined
const ready = {
  document: {
    id: "document-design",
    projectId: "project-design",
    artifactId: "artifact-design",
    literatureRecordId: "literature-design",
    documentType: "SCHOLARLY_PDF",
    parserType: "GROBID",
    parseStatus: "RUNNING",
    knownStatus: true,
    tone: "info",
    parseConfidence: "UNKNOWN",
    pageCount: null,
    language: null,
    isScanned: null,
    permissions: { canParse: false },
    updatedAt: "2026-08-01T04:20:00Z",
  },
  pages: [],
  job: {
    id: "job-design",
    status: "RUNNING",
    knownStatus: true,
    tone: "info",
    progressPercent: 45,
    currentStep: "Converting TEI",
    retryable: false,
    retryPermissionKnown: true,
    canRetry: false,
    retryDisabledReason: "Only failed Jobs can be retried.",
    errorCode: null,
    errorMessage: null,
  },
  permissionsKnown: true,
  canUpload: true,
} as const

const loadError = {
  title: "Document unavailable",
  message: "The document projection could not be loaded.",
  code: "DOCUMENT_LOAD_FAILED",
  requestId: "request-document-load",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const forbiddenError = {
  title: "Access denied",
  message: "You do not have access to this document.",
  code: "PROJECT_ACCESS_DENIED",
  requestId: "request-document-forbidden",
  retryable: false,
  forbidden: true,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const parseError = {
  title: "Parse request failed",
  message: "The parse intent failed; the document status has not changed.",
  code: "DOCUMENT_PARSE_FAILED",
  requestId: "request-document-parse",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

export const documentReadyFixture = {
  content: { state: "ready", data: ready },
  pendingAction: null,
  mutationError: null,
  onRetry: noop,
  onEvent: noop,
} satisfies DocumentWorkspaceProps

export const documentLoadingFixture = {
  ...documentReadyFixture,
  content: { state: "loading", label: "Loading document" },
} satisfies DocumentWorkspaceProps

export const documentDraftFixture = {
  ...documentReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      document: {
        ...ready.document,
        literatureRecordId: null,
        parseStatus: "DRAFT",
        tone: "neutral",
        permissions: { canParse: true },
      },
      job: null,
    },
  },
} satisfies DocumentWorkspaceProps

export const documentQueuedFixture = {
  ...documentReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      document: { ...ready.document, parseStatus: "QUEUED" },
      job: {
        ...ready.job,
        status: "QUEUED",
        progressPercent: 0,
        currentStep: "Waiting for parser",
      },
    },
  },
} satisfies DocumentWorkspaceProps

export const documentCompletedFixture = {
  ...documentReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      document: {
        ...ready.document,
        parseStatus: "COMPLETED",
        tone: "success",
        parseConfidence: "HIGH",
        pageCount: 3,
        language: "en",
        isScanned: false,
      },
      pages: [
        {
          pageNumber: 1,
          printedPageLabel: "1",
          textContent:
            "Abstract and introduction from the server-projected page text.",
        },
        {
          pageNumber: 2,
          printedPageLabel: "2",
          textContent:
            "Methods and reproducibility details from the parsed document.",
        },
        {
          pageNumber: 3,
          printedPageLabel: "3",
          textContent:
            "Results, limitations, and references from the parsed document.",
        },
      ],
      job: {
        ...ready.job,
        status: "COMPLETED",
        tone: "success",
        progressPercent: 100,
        currentStep: "Completed",
      },
    },
  },
} satisfies DocumentWorkspaceProps

export const documentFailedRetryableFixture = {
  ...documentReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      document: { ...ready.document, parseStatus: "FAILED", tone: "danger" },
      job: {
        ...ready.job,
        status: "FAILED",
        tone: "danger",
        progressPercent: 62,
        currentStep: "Extracting structured text",
        retryable: true,
        canRetry: true,
        retryDisabledReason: null,
        errorCode: "GROBID_TIMEOUT",
        errorMessage:
          "GROBID timed out before producing a complete TEI document.",
      },
    },
  },
} satisfies DocumentWorkspaceProps

export const documentFailedNonRetryableFixture = {
  ...documentFailedRetryableFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      document: { ...ready.document, parseStatus: "FAILED", tone: "danger" },
      job: {
        ...ready.job,
        status: "FAILED",
        tone: "danger",
        progressPercent: 18,
        currentStep: "Validating input",
        retryable: false,
        canRetry: false,
        retryDisabledReason: "The server marked this Job as non-retryable.",
        errorCode: "PDF_CORRUPT",
        errorMessage:
          "The service classified this parse failure as non-retryable.",
      },
    },
  },
} satisfies DocumentWorkspaceProps

export const documentLoadErrorFixture = {
  ...documentReadyFixture,
  content: { state: "error", error: loadError },
} satisfies DocumentWorkspaceProps

export const documentForbiddenFixture = {
  ...documentReadyFixture,
  content: { state: "error", error: forbiddenError },
} satisfies DocumentWorkspaceProps

export const documentReadOnlyFixture = {
  ...documentCompletedFixture,
  content: {
    state: "ready",
    data: {
      ...documentCompletedFixture.content.data,
      document: {
        ...documentCompletedFixture.content.data.document,
        permissions: { canParse: false },
      },
      canUpload: false,
    },
  },
} satisfies DocumentWorkspaceProps

export const documentUploadPendingFixture = {
  ...documentDraftFixture,
  pendingAction: "upload",
} satisfies DocumentWorkspaceProps

export const documentParsePendingFixture = {
  ...documentDraftFixture,
  pendingAction: "parse",
} satisfies DocumentWorkspaceProps

export const documentRetryPendingFixture = {
  ...documentFailedRetryableFixture,
  pendingAction: "retry-job",
} satisfies DocumentWorkspaceProps

export const documentMutationErrorFixture = {
  ...documentDraftFixture,
  mutationError: parseError,
} satisfies DocumentWorkspaceProps

export const documentScannedFixture = {
  ...documentCompletedFixture,
  content: {
    state: "ready",
    data: {
      ...documentCompletedFixture.content.data,
      document: {
        ...documentCompletedFixture.content.data.document,
        parseConfidence: "LOW",
        tone: "degraded",
        isScanned: true,
      },
      pages: [
        { pageNumber: 1, printedPageLabel: "1", textContent: null },
        {
          pageNumber: 2,
          printedPageLabel: "2",
          textContent:
            "Limited extracted text supplied by the server projection.",
        },
      ],
    },
  },
} satisfies DocumentWorkspaceProps

export const documentFallbackFixture = {
  ...documentCompletedFixture,
  content: {
    state: "ready",
    data: {
      ...documentCompletedFixture.content.data,
      document: {
        ...documentCompletedFixture.content.data.document,
        parserType: "PYPDF",
        tone: "degraded",
        parseConfidence: "LOW",
      },
    },
  },
} satisfies DocumentWorkspaceProps

export const documentDegradedFixture = {
  ...documentReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      document: {
        ...ready.document,
        parseStatus: "FUTURE_PARSE_STATE",
        knownStatus: false,
        tone: "degraded",
        permissions: { canParse: false },
      },
      job: null,
      permissionsKnown: false,
      canUpload: false,
    },
  },
} satisfies DocumentWorkspaceProps

export const documentFixtures = [
  {
    id: "running",
    label: "Running",
    behavior: "Shows current parse progress without implying completion.",
    props: documentReadyFixture,
  },
  {
    id: "loading",
    label: "Loading",
    behavior: "Keeps the three-pane reader stable while document facts load.",
    props: documentLoadingFixture,
  },
  {
    id: "draft",
    label: "DRAFT",
    behavior: "Shows a parseable draft with no fabricated Job projection.",
    props: documentDraftFixture,
  },
  {
    id: "queued",
    label: "QUEUED",
    behavior:
      "Shows a queued parse and zero progress from the existing Job projection.",
    props: documentQueuedFixture,
  },
  {
    id: "grobid-completed",
    label: "GROBID completed",
    behavior: "Renders completed GROBID output with server-projected pages.",
    props: documentCompletedFixture,
  },
  {
    id: "failed-retryable",
    label: "Failed retryable",
    behavior: "Enables retry only when the projected Job is retryable.",
    props: documentFailedRetryableFixture,
  },
  {
    id: "failed-non-retryable",
    label: "Failed non-retryable",
    behavior:
      "Explains why retry remains disabled for a non-retryable failure.",
    props: documentFailedNonRetryableFixture,
  },
  {
    id: "load-error",
    label: "Load error",
    behavior: "Offers reload only for the retryable document load path.",
    props: documentLoadErrorFixture,
  },
  {
    id: "forbidden",
    label: "Forbidden",
    behavior: "Shows access denial without document mutation controls.",
    props: documentForbiddenFixture,
  },
  {
    id: "read-only",
    label: "Read-only",
    behavior:
      "Keeps completed pages readable while upload and parse remain disabled.",
    props: documentReadOnlyFixture,
  },
  {
    id: "upload-pending",
    label: "Upload pending",
    behavior:
      "Disables duplicate document actions while upload intent is pending.",
    props: documentUploadPendingFixture,
  },
  {
    id: "parse-pending",
    label: "Parse pending",
    behavior: "Shows parse submission pending without changing parse status.",
    props: documentParsePendingFixture,
  },
  {
    id: "retry-pending",
    label: "Retry pending",
    behavior:
      "Shows retry submission pending without claiming a new attempt succeeded.",
    props: documentRetryPendingFixture,
  },
  {
    id: "mutation-error",
    label: "Mutation error",
    behavior:
      "Surfaces a parse mutation error while preserving the prior document state.",
    props: documentMutationErrorFixture,
  },
  {
    id: "scanned",
    label: "Scanned PDF",
    behavior:
      "Displays the formal scanned-document warning and limited page text.",
    props: documentScannedFixture,
  },
  {
    id: "pypdf-fallback",
    label: "pypdf fallback",
    behavior:
      "Distinguishes low-confidence fallback output from GROBID completion.",
    props: documentFallbackFixture,
  },
  {
    id: "degraded",
    label: "Degraded",
    behavior:
      "Fails closed for unknown parse status and permission projection.",
    props: documentDegradedFixture,
  },
] as const satisfies ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: DocumentWorkspaceProps
}>
