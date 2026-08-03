import type { UiErrorViewModel } from "../../projects/model"
import type { LiteratureWorkspaceProps } from "../ui/contracts"

const noop = () => undefined
const ready = {
  records: [
    {
      id: "literature-design",
      title: "Generative AI and student engagement",
      authors: "Li; Smith",
      year: 2025,
      doi: "10.1000/reca.1",
      sourceType: "OPENALEX",
      verificationStatus: "VERIFIED",
      decision: "UNCERTAIN",
      documentId: null,
      canUploadDocument: true,
    },
  ],
  activeSearch: {
    id: "search-design",
    queryPlanId: "query-plan-design",
    status: "COMPLETED",
    knownStatus: true,
    tone: "success",
    progressJobId: "job-design",
    resultCount: 1,
    cacheHit: false,
    cacheStale: false,
    degraded: false,
    limitations: [],
    errorCode: null,
    fetchedAt: "2026-08-01T04:10:00Z",
    retryabilityKnown: true,
    retryPermissionKnown: true,
    retryable: false,
    canRetry: false,
    retryDisabledReason: "The server marked this Job as non-retryable.",
  },
  candidates: [
    {
      id: "candidate-design",
      title: "Generative AI and student engagement",
      authors: "Li; Smith",
      year: 2025,
      doi: "10.1000/reca.1",
      verificationStatus: "VERIFIED",
      degraded: false,
      importedRecordId: null,
      canImport: true,
    },
  ],
  permissionsKnown: true,
  permissions: { canSearch: true, canImport: true, canImportDoi: true },
} as const

const loadError = {
  title: "Literature unavailable",
  message: "Literature records and search results could not be loaded.",
  code: "LITERATURE_LOAD_FAILED",
  requestId: "request-literature-load",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const forbiddenError = {
  title: "Access denied",
  message: "You do not have access to this project's literature workspace.",
  code: "PROJECT_ACCESS_DENIED",
  requestId: "request-literature-forbidden",
  retryable: false,
  forbidden: true,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

const mutationError = {
  title: "Import failed",
  message: "The import intent failed; no literature record was created.",
  code: "LITERATURE_IMPORT_FAILED",
  requestId: "request-literature-import",
  retryable: true,
  forbidden: false,
  notFound: false,
  conflict: false,
} satisfies UiErrorViewModel

export const literatureReadyFixture = {
  content: { state: "ready", data: ready },
  pendingAction: null,
  mutationError: null,
  onRetry: noop,
  onEvent: noop,
} satisfies LiteratureWorkspaceProps

export const literatureLoadingFixture = {
  ...literatureReadyFixture,
  content: { state: "loading", label: "Loading literature" },
} satisfies LiteratureWorkspaceProps

export const literatureNoActiveSearchFixture = {
  ...literatureReadyFixture,
  content: {
    state: "ready",
    data: { ...ready, activeSearch: null, candidates: [] },
  },
} satisfies LiteratureWorkspaceProps

export const literatureEmptyResultFixture = {
  ...literatureReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      activeSearch: { ...ready.activeSearch, resultCount: 0 },
      candidates: [],
      records: [],
    },
  },
} satisfies LiteratureWorkspaceProps

export const literatureLoadErrorFixture = {
  ...literatureReadyFixture,
  content: { state: "error", error: loadError },
} satisfies LiteratureWorkspaceProps

export const literatureForbiddenFixture = {
  ...literatureReadyFixture,
  content: { state: "error", error: forbiddenError },
} satisfies LiteratureWorkspaceProps

export const literatureReadOnlyFixture = {
  ...literatureReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      records: ready.records.map((record) => ({
        ...record,
        canUploadDocument: false,
      })),
      candidates: ready.candidates.map((candidate) => ({
        ...candidate,
        canImport: false,
      })),
      permissions: { canSearch: false, canImport: false, canImportDoi: false },
    },
  },
} satisfies LiteratureWorkspaceProps

export const literaturePermissionsUnknownFixture = {
  ...literatureReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      records: ready.records.map((record) => ({
        ...record,
        canUploadDocument: false,
      })),
      candidates: ready.candidates.map((candidate) => ({
        ...candidate,
        canImport: false,
      })),
      permissionsKnown: false,
      permissions: { canSearch: false, canImport: false, canImportDoi: false },
    },
  },
} satisfies LiteratureWorkspaceProps

export const literatureSearchPendingFixture = {
  ...literatureReadyFixture,
  pendingAction: "search",
} satisfies LiteratureWorkspaceProps

export const literatureCandidateImportPendingFixture = {
  ...literatureReadyFixture,
  pendingAction: "import-candidates",
} satisfies LiteratureWorkspaceProps

export const literatureDoiImportPendingFixture = {
  ...literatureReadyFixture,
  pendingAction: "import-doi",
} satisfies LiteratureWorkspaceProps

export const literatureMutationErrorFixture = {
  ...literatureReadyFixture,
  mutationError,
} satisfies LiteratureWorkspaceProps

export const literatureLongMetadataFixture = {
  ...literatureReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      records: [
        {
          ...ready.records[0],
          title:
            "Responsible use of generative artificial intelligence across multi-institutional teacher education programs with heterogeneous digital learning policies",
          authors:
            "Alexandra-Marguerite Rivera-Santos; Christopher-Lee van der Meer; Research Methods Consortium for Technology-Mediated Learning",
          doi: "10.5555/reca.extremely.long.provider.metadata.identifier.2026.00000001",
          sourceType: "OPENALEX_PYALEX_RECORDED_PROVIDER_RESPONSE",
        },
      ],
      candidates: [
        {
          ...ready.candidates[0],
          title:
            "Longitudinal associations between assessment-specific large language model use and multidimensional student engagement in undergraduate education",
          authors:
            "Alexandra-Marguerite Rivera-Santos; Christopher-Lee van der Meer; International Evidence Synthesis Working Group",
          doi: "10.5555/reca.extremely.long.candidate.identifier.2026.00000002",
          verificationStatus: "PROVIDER_METADATA_REQUIRES_MANUAL_VERIFICATION",
        },
      ],
    },
  },
} satisfies LiteratureWorkspaceProps

export const literatureDegradedFixture = {
  ...literatureReadyFixture,
  content: {
    state: "ready",
    data: {
      ...ready,
      activeSearch: {
        ...ready.activeSearch,
        status: "FUTURE_SEARCH_STATE",
        knownStatus: false,
        tone: "degraded",
        degraded: true,
      },
      permissionsKnown: false,
      permissions: { canSearch: false, canImport: false, canImportDoi: false },
    },
  },
} satisfies LiteratureWorkspaceProps

export const literatureFixtures = [
  {
    id: "ready",
    label: "Ready",
    behavior:
      "Renders verified candidates and formal records as separate concepts.",
    props: literatureReadyFixture,
  },
  {
    id: "loading",
    label: "Loading",
    behavior:
      "Keeps the three-pane workspace stable while literature data loads.",
    props: literatureLoadingFixture,
  },
  {
    id: "no-active-search",
    label: "No active search",
    behavior:
      "Shows records without inventing a Search Run or query-plan binding.",
    props: literatureNoActiveSearchFixture,
  },
  {
    id: "empty-result",
    label: "Empty result",
    behavior:
      "Shows a completed zero-result run without fake candidates or records.",
    props: literatureEmptyResultFixture,
  },
  {
    id: "load-error",
    label: "Load error",
    behavior: "Offers retry only for the retryable load failure path.",
    props: literatureLoadErrorFixture,
  },
  {
    id: "forbidden",
    label: "Forbidden",
    behavior: "Shows project access denial without mutation controls.",
    props: literatureForbiddenFixture,
  },
  {
    id: "read-only",
    label: "Read-only",
    behavior:
      "Disables search and import actions from explicit mapped permissions.",
    props: literatureReadOnlyFixture,
  },
  {
    id: "permissions-unknown",
    label: "Permissions unknown",
    behavior:
      "Keeps mapped literature data visible while all writes fail closed.",
    props: literaturePermissionsUnknownFixture,
  },
  {
    id: "search-pending",
    label: "Search pending",
    behavior:
      "Prevents duplicate literature actions while search intent is pending.",
    props: literatureSearchPendingFixture,
  },
  {
    id: "candidate-import-pending",
    label: "Candidate import pending",
    behavior:
      "Marks candidate import intent pending without creating a formal record.",
    props: literatureCandidateImportPendingFixture,
  },
  {
    id: "doi-import-pending",
    label: "DOI import pending",
    behavior:
      "Marks DOI import intent pending without claiming import success.",
    props: literatureDoiImportPendingFixture,
  },
  {
    id: "mutation-error",
    label: "Mutation error",
    behavior:
      "Surfaces an import failure while preserving the prior server projection.",
    props: literatureMutationErrorFixture,
  },
  {
    id: "long-metadata",
    label: "Long metadata",
    behavior:
      "Exercises title, DOI, author, provider, and verification wrapping.",
    props: literatureLongMetadataFixture,
  },
  {
    id: "degraded",
    label: "Degraded",
    behavior:
      "Fails closed for unknown search status and permission projection.",
    props: literatureDegradedFixture,
  },
] as const satisfies ReadonlyArray<{
  id: string
  label: string
  behavior: string
  props: LiteratureWorkspaceProps
}>
