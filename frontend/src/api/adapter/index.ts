import { client } from "../generated/client.gen"
import {
  analysisCreateAnalysisPlanPostApiV1ProjectsProjectIdAnalysisPlans,
  analysisGetAnalysisPlanGetApiV1AnalysisPlansPlanId,
  analysisGetAnalysisResultsGetApiV1AnalysisRunsRunIdResults,
  analysisGetAnalysisRunGetApiV1AnalysisRunsRunId,
  analysisInvalidateAnalysisRunPostApiV1AnalysisRunsRunIdInvalidate,
  analysisRequestAnalysisApprovalPostApiV1AnalysisPlansPlanIdApprovalRequests,
  analysisRunAnalysisPlanPostApiV1AnalysisPlansPlanIdRuns,
  analysisUpdateAnalysisPlanPatchApiV1AnalysisPlansPlanId,
  analysisValidateAnalysisPlanPostApiV1AnalysisPlansPlanIdValidate,
  approvalsApprovePostApiV1ApprovalsApprovalIdApprove,
  approvalsCancelPostApiV1ApprovalsApprovalIdCancel,
  approvalsGetApprovalGetApiV1ApprovalsApprovalId,
  approvalsListProjectApprovalsGetApiV1ProjectsProjectIdApprovals,
  approvalsRejectPostApiV1ApprovalsApprovalIdReject,
  artifactsAuthorizeArtifactDownloadGetApiV1ArtifactsArtifactIdDownload,
  artifactsCompleteArtifactUploadPostApiV1ProjectsProjectIdArtifactsUploadsUploadIdComplete,
  artifactsInitiateArtifactUploadPostApiV1ProjectsProjectIdArtifactsUploads,
  artifactsListProjectArtifactsGetApiV1ProjectsProjectIdArtifacts,
  dataCleaningCompareDatasetVersionsGetApiV1DatasetsDatasetIdVersionComparison,
  dataCleaningCreateCleaningPlanPostApiV1DatasetVersionsVersionIdCleaningPlans,
  dataCleaningExecuteCleaningPlanPostApiV1CleaningPlansPlanIdExecute,
  dataCleaningGetCleaningPlanGetApiV1CleaningPlansPlanId,
  dataCleaningGetDataTransformationGetApiV1DataTransformationsTransformationId,
  dataCleaningPreviewCleaningPlanPostApiV1CleaningPlansPlanIdPreview,
  dataCleaningRequestCleaningPlanApprovalPostApiV1CleaningPlansPlanIdApprovalRequests,
  dataCleaningUpdateCleaningPlanPatchApiV1CleaningPlansPlanId,
  dataQualityAcknowledgeQualityIssuePostApiV1DataQualityIssuesIssueIdAcknowledge,
  dataQualityGetQualityRunGetApiV1DataQualityRunsRunId,
  dataQualityIgnoreQualityIssuePostApiV1DataQualityIssuesIssueIdIgnore,
  dataQualityListQualityIssuesGetApiV1DataQualityRunsRunIdIssues,
  dataQualityRequestQualityRunPostApiV1DatasetVersionsVersionIdQualityRuns,
  datasetsGetDatasetGetApiV1DatasetsDatasetId,
  datasetsGetDatasetVersionGetApiV1DatasetVersionsVersionId,
  datasetsGetWorksheetsGetApiV1DatasetVersionsVersionIdWorksheets,
  datasetsListDatasetColumnsGetApiV1DatasetVersionsVersionIdColumns,
  datasetsListDatasetsGetApiV1ProjectsProjectIdDatasets,
  datasetsListDatasetVersionsGetApiV1DatasetsDatasetIdVersions,
  datasetsPreviewDatasetVersionGetApiV1DatasetVersionsVersionIdPreview,
  datasetsSelectWorksheetPostApiV1DatasetVersionsVersionIdWorksheetSelection,
  datasetsUpdateDatasetColumnPatchApiV1DatasetColumnsColumnId,
  datasetsUpdateDatasetPatchApiV1DatasetsDatasetId,
  datasetsUploadDatasetPostApiV1ProjectsProjectIdDatasets,
  documentsGetDocumentGetApiV1DocumentsDocumentId,
  documentsGetDocumentPageGetApiV1DocumentsDocumentIdPagesPageNumber,
  documentsListDocumentPagesGetApiV1DocumentsDocumentIdPages,
  documentsParseDocumentPostApiV1DocumentsDocumentIdParse,
  documentsUploadDocumentPostApiV1ProjectsProjectIdDocuments,
  evidenceCreateEvidenceSetSummaryPostApiV1ProjectsProjectIdEvidenceSetSummaries,
  evidenceCreateEvidenceSpanPostApiV1DocumentsDocumentIdEvidenceSpans,
  evidenceCreateEvidenceSpanVerificationPostApiV1EvidenceSpansEvidenceSpanIdVerificationRecords,
  evidenceCreateLiteratureDecisionPostApiV1LiteratureLiteratureIdDecisions,
  evidenceCreateLiteratureExtractionPostApiV1DocumentsDocumentIdLiteratureExtractions,
  evidenceCreateTopicGenerationRunPostApiV1ProjectsProjectIdTopicGenerationRuns,
  evidenceGetEvidenceSetSummaryGetApiV1EvidenceSetSummariesSummaryId,
  evidenceGetEvidenceSpanGetApiV1EvidenceSpansEvidenceSpanId,
  evidenceGetLiteratureExtractionGetApiV1LiteratureExtractionsExtractionId,
  evidenceGetLiteratureMatrixGetApiV1ProjectsProjectIdLiteratureMatrix,
  evidenceGetTopicGenerationRunGetApiV1TopicGenerationRunsRunId,
  evidenceListLiteratureDecisionsGetApiV1LiteratureLiteratureIdDecisions,
  evidenceSearchProjectEvidencePostApiV1ProjectsProjectIdEvidenceSearch,
  evidenceUpdateLiteratureExtractionFieldPatchApiV1LiteratureExtractionFieldsFieldId,
  figuresCreateFigurePlanPostApiV1ProjectsProjectIdFigurePlans,
  figuresDownloadFigureFormatGetApiV1FiguresFigureIdDownloadsFormatName,
  figuresGetFigureGetApiV1FiguresFigureId,
  figuresGetFigurePlanGetApiV1FigurePlansPlanId,
  figuresGetFigureRecommendationsPostApiV1ProjectsProjectIdFigureRecommendations,
  figuresGetFigureRenderRunGetApiV1FigureRenderRunsRunId,
  figuresGetFigureValidationIssuesGetApiV1FiguresFigureIdValidationIssues,
  figuresRenderFigurePlanPostApiV1FigurePlansPlanIdRenderRuns,
  figuresRequestFigureConfirmationPostApiV1FiguresFigureIdApprovalRequests,
  healthDependenciesHealthGetApiV1HealthDependencies,
  healthLiveHealthGetApiV1HealthLive,
  healthReadyHealthGetApiV1HealthReady,
  jobsCancelJobPostApiV1JobsJobIdCancel,
  jobsGetJobGetApiV1JobsJobId,
  jobsListProjectJobsGetApiV1ProjectsProjectIdJobs,
  jobsRetryJobPostApiV1JobsJobIdRetry,
  literatureCreateSearchRunPostApiV1QueryPlansQueryPlanIdSearchRuns,
  literatureGetLiteratureGetApiV1LiteratureLiteratureId,
  literatureGetSearchResultsGetApiV1LiteratureSearchRunsSearchRunIdResults,
  literatureImportDoiPostApiV1ProjectsProjectIdLiteratureImportDoi,
  literatureImportSearchCandidatesPostApiV1ProjectsProjectIdLiteratureImport,
  literatureListLiteratureGetApiV1ProjectsProjectIdLiterature,
  loginLoginAccessTokenPostApiV1LoginAccessToken,
  loginRecoverPasswordPostApiV1PasswordRecoveryEmail,
  loginResetPasswordPostApiV1ResetPassword,
  projectsAddProjectMemberPostApiV1ProjectsProjectIdMembers,
  projectsArchiveProjectPostApiV1ProjectsProjectIdArchive,
  projectsCreateProjectPostApiV1Projects,
  projectsGetProjectGetApiV1ProjectsProjectId,
  projectsGetProjectOverviewGetApiV1ProjectsProjectIdOverview,
  projectsListProjectAuditLogsGetApiV1ProjectsProjectIdAuditLogs,
  projectsListProjectMembersGetApiV1ProjectsProjectIdMembers,
  projectsListProjectsGetApiV1Projects,
  projectsRemoveProjectMemberDeleteApiV1ProjectsProjectIdMembersMemberId,
  projectsRestoreProjectPostApiV1ProjectsProjectIdRestore,
  projectsUpdateProjectMemberPatchApiV1ProjectsProjectIdMembersMemberId,
  projectsUpdateProjectPatchApiV1ProjectsProjectId,
  queryPlansCreateQueryPlanPostApiV1ProjectsProjectIdQueryPlans,
  queryPlansGenerateQueryPlanPostApiV1QueryPlansQueryPlanIdGenerate,
  queryPlansGetQueryPlanGetApiV1QueryPlansQueryPlanId,
  queryPlansUpdateQueryPlanPatchApiV1QueryPlansQueryPlanId,
  researchQuestionsCreateResearchQuestionPostApiV1ProjectsProjectIdResearchQuestions,
  researchQuestionsCreateResearchQuestionVersionPostApiV1ResearchQuestionsResearchQuestionIdVersions,
  researchQuestionsGetCurrentProjectResearchQuestionGetApiV1ProjectsProjectIdResearchQuestion,
  researchQuestionsGetResearchQuestionGetApiV1ResearchQuestionsResearchQuestionId,
  researchQuestionsGetResearchQuestionVersionGetApiV1ResearchQuestionVersionsVersionId,
  researchQuestionsListResearchQuestionVersionsGetApiV1ResearchQuestionsResearchQuestionIdVersions,
  researchQuestionsMarkResearchQuestionVersionReadyPostApiV1ResearchQuestionVersionsVersionIdReady,
  researchQuestionsRequestResearchQuestionConfirmationPostApiV1ResearchQuestionVersionsVersionIdApprovalRequests,
  usersCreateUserPostApiV1Users,
  usersDeleteUserDeleteApiV1UsersUserId,
  usersDeleteUserMeDeleteApiV1UsersMe,
  usersReadUserMeGetApiV1UsersMe,
  usersReadUsersGetApiV1Users,
  usersRegisterUserPostApiV1UsersSignup,
  usersUpdatePasswordMePatchApiV1UsersMePassword,
  usersUpdateUserMePatchApiV1UsersMe,
  usersUpdateUserPatchApiV1UsersUserId,
} from "../generated/sdk.gen"

export type {
  AnalysisApprovalEnvelope,
  AnalysisApprovalPublic,
  AnalysisAssumptionPublic,
  AnalysisGoal,
  AnalysisInvalidate,
  AnalysisMethod,
  AnalysisParameters,
  AnalysisPlanCreate,
  AnalysisPlanEnvelope,
  AnalysisPlanPublic,
  AnalysisPlanStatus,
  AnalysisPlanUpdate,
  AnalysisResultPublic,
  AnalysisResultsEnvelope,
  AnalysisResultType,
  AnalysisRunCreate,
  AnalysisRunEnvelope,
  AnalysisRunPublic,
  AnalysisRunRequestEnvelope,
  AnalysisRunStatus,
  ApprovalDecisionRequest,
  ApprovalListEnvelope,
  ApprovalPublic,
  ApprovalRejectRequest,
  ApprovalStatus,
  ArtifactListEnvelope,
  ArtifactPublic,
  ArtifactType,
  ArtifactUploadComplete,
  ArtifactUploadInitiate,
  AssumptionCheckCode,
  AssumptionCheckStatus,
  AuditListEnvelope,
  BodyLoginLoginAccessTokenPostApiV1LoginAccessToken as Body_login_login_access_token_post_api_v1_login_access_token,
  CurrentResearchQuestionEnvelope,
  DependenciesHealthResponse,
  DependencyCheck,
  DependencyStatus,
  DocumentEnvelope,
  DocumentPageEnvelope,
  DocumentPageListEnvelope,
  DocumentPagePublic,
  DocumentParseRequest,
  DocumentPublic,
  DocumentType,
  DocumentUploadEnvelope,
  EvidenceCandidateDto,
  EvidenceSearchEnvelope,
  EvidenceSearchRequest,
  EvidenceSetSummaryCreate,
  EvidenceSetSummaryEnvelope,
  EvidenceSetSummaryPublic,
  EvidenceSpanPublic,
  EvidenceSpanVerificationCreate,
  FieldConfirmationStatus,
  FieldEvidenceStatus,
  FigureArtifactPublic,
  FigureChartType,
  FigurePlanCreate,
  FigurePlanEnvelope,
  FigurePlanPublic,
  FigurePlanStatus,
  FigurePublic,
  FigureRecommendationEnvelope,
  FigureRecommendationPublic,
  FigureRenderCreate,
  FigureRenderRequestEnvelope,
  FigureRenderRunEnvelope,
  FigureRenderRunPublic,
  FigureRenderRunStatus,
  FigureStatus,
  FigureValidationIssuePublic,
  JobListEnvelope,
  JobPublic,
  LiteratureCandidatePublic,
  LiteratureDecisionCreate,
  LiteratureDecisionStatus,
  LiteratureDoiImportRequest,
  LiteratureExtractionFieldCorrection,
  LiteratureExtractionFieldPublic,
  LiteratureExtractionPublic,
  LiteratureFieldCode,
  LiteratureImportEnvelope,
  LiteratureImportRequest,
  LiteratureMatrixEnvelope,
  LiteratureMatrixField,
  LiteratureMatrixRow,
  LiteratureRecordEnvelope,
  LiteratureRecordListEnvelope,
  LiteratureRecordPublic,
  LiteratureSearchAcceptedEnvelope,
  LiteratureSearchCreate,
  LiteratureSearchResultsEnvelope,
  LiteratureSearchRunPublic,
  LiveHealthResponse,
  MemberAdd,
  MemberListEnvelope,
  MemberUpdate,
  ProjectCreate,
  ProjectListEnvelope,
  ProjectMemberPublic,
  ProjectOverviewPublic,
  ProjectPublic,
  ProjectStage,
  ProjectStatus,
  ProjectType,
  ProjectUpdate,
  QueryPlanCreate,
  QueryPlanEnvelope,
  QueryPlanFields,
  QueryPlanPublic,
  QueryPlanUpdate,
  ReadyHealthResponse,
  ResearchQuestionCreate,
  ResearchQuestionData,
  ResearchQuestionMarkReady,
  ResearchQuestionVersionCreate,
  ResearchQuestionVersionPublic,
  Token,
  TopicGenerationCreate,
  UpdatePassword,
  UserCreate,
  UserPublic,
  UserRegister,
  UsersPublic,
  UserUpdate,
  UserUpdateMe,
} from "../generated/types.gen"

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly kind:
      | "NETWORK"
      | "TIMEOUT"
      | "UNAUTHORIZED"
      | "FORBIDDEN"
      | "NOT_FOUND"
      | "CONFLICT"
      | "VALIDATION"
      | "SERVER"
      | "SERVICE_UNAVAILABLE"
      | "UNKNOWN",
    message: string,
    public readonly code = "UNKNOWN_ERROR",
    public readonly requestId: string | null = null,
    public readonly details: Record<string, unknown> = {},
    public readonly fieldErrors: Array<Record<string, unknown>> = [],
    public readonly retryable = false,
    public readonly suggestedAction: string | null = null,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export function configureApi(baseUrl: string, getToken: () => string | null) {
  client.setConfig({
    baseUrl,
    auth: () => getToken() ?? undefined,
  })
}

type GeneratedResult<T> = {
  data?: T
  error?: unknown
  response?: Response
}

function errorKind(status: number): ApiError["kind"] {
  if (status === 0) return "NETWORK"
  if (status === 401) return "UNAUTHORIZED"
  if (status === 403) return "FORBIDDEN"
  if (status === 404) return "NOT_FOUND"
  if (status === 409) return "CONFLICT"
  if (status === 422) return "VALIDATION"
  if (status === 503) return "SERVICE_UNAVAILABLE"
  if (status >= 500) return "SERVER"
  return "UNKNOWN"
}

function defaultErrorMessage(status: number): string {
  if (status >= 500) return "The API reported a server error."
  if (status === 0) return "The API could not be reached."
  return "The API request could not be completed."
}

function objectValue(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null
}

function normalizedError(
  status: number,
  payload: unknown,
  response?: Response,
): ApiError {
  const root = objectValue(payload)
  const nested = objectValue(root?.error) ?? objectValue(root?.detail) ?? root
  const message =
    typeof nested?.message === "string"
      ? nested.message
      : typeof root?.detail === "string"
        ? root.detail
        : defaultErrorMessage(status)
  const code = typeof nested?.code === "string" ? nested.code : "UNKNOWN_ERROR"
  const requestId =
    (typeof nested?.request_id === "string" ? nested.request_id : null) ??
    (typeof root?.request_id === "string" ? root.request_id : null) ??
    response?.headers.get("x-request-id") ??
    null
  const details = objectValue(nested?.details) ?? {}
  const fieldErrors = Array.isArray(nested?.field_errors)
    ? nested.field_errors.filter(
        (item): item is Record<string, unknown> => objectValue(item) !== null,
      )
    : []
  return new ApiError(
    status,
    errorKind(status),
    message,
    code,
    requestId,
    details,
    fieldErrors,
    nested?.retryable === true,
    typeof nested?.suggested_action === "string"
      ? nested.suggested_action
      : null,
  )
}

async function unwrap<T>(request: Promise<GeneratedResult<T>>): Promise<T> {
  try {
    const result = await request
    const status = result.response?.status ?? 0
    if (result.error || !result.response?.ok || result.data === undefined) {
      throw normalizedError(status, result.error, result.response)
    }
    return result.data
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(0, "NETWORK", "The API could not be reached.")
  }
}

async function unwrapVoid(
  request: Promise<GeneratedResult<unknown>>,
): Promise<void> {
  try {
    const result = await request
    const status = result.response?.status ?? 0
    if (result.error || !result.response?.ok) {
      throw normalizedError(status, result.error, result.response)
    }
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(0, "NETWORK", "The API could not be reached.")
  }
}

export type PageQuery = { page?: number; page_size?: number }

export type DataEnvelope<T> = {
  data: T
  meta?: Record<string, unknown>
}

export type DatasetDto = {
  id: string
  project_id: string
  name: string
  description: string | null
  source_type: string
  publisher: string | null
  source_platform: string | null
  source_identifier: string | null
  doi: string | null
  acquired_at: string | null
  license_name: string | null
  license_status: string
  license_warning: string | null
  recommended_citation: string | null
  known_limitations: readonly string[] | null
  current_version_id: string | null
  status: string
  lock_version: number
  permissions?: {
    can_update?: boolean
    can_upload?: boolean
    can_confirm_columns?: boolean
  }
  created_at: string
  updated_at: string
}

export type WorksheetDto = {
  name: string
  ordinal: number
  visibility: string
  estimated_rows: number
  estimated_columns: number
  warnings?: readonly string[]
}

export type DatasetVersionDto = {
  id: string
  project_id: string
  dataset_id: string
  version_number: number
  parent_version_id: string | null
  artifact_id: string
  version_type: string
  row_count: number | null
  column_count: number | null
  file_format: string
  worksheet_manifest: readonly WorksheetDto[] | null
  selected_worksheet_name: string | null
  projection_hash: string | null
  schema_hash: string | null
  data_hash: string
  transformation_id: string | null
  status: string
  created_at: string
  invalidated_at: string | null
  invalidation_reason: string | null
}

export type DatasetColumnDto = {
  id: string
  project_id: string
  dataset_version_id: string
  source_name: string
  display_name: string | null
  column_order: number
  inferred_type: string
  confirmed_type: string | null
  semantic_role: string | null
  unit: string | null
  description: string | null
  missing_codes: readonly string[] | null
  category_mapping: Record<string, unknown> | null
  is_identifier: boolean
  is_sensitive: boolean
  confirmation_status: string
  unique_count: number | null
  missing_ratio: number | null
  example_values: readonly unknown[] | null
  inherited_from_column_id: string | null
  lock_version: number
  created_at: string
  updated_at: string
}

export type DatasetPreviewDto = {
  version_id: string
  offset: number
  limit: number
  columns: readonly string[]
  rows: readonly Record<string, unknown>[]
  returned: number
  total_rows: number | null
  truncated: boolean
}

export type DataQualityRunDto = {
  id: string
  project_id: string
  dataset_version_id: string
  ruleset_id: string
  ruleset_version: string
  ruleset_hash: string
  selected_rule_ids: readonly string[]
  include_sensitive_field_detection: boolean
  status: string
  issue_count: number
  high_issue_count: number
  processing_run_id: string | null
  job_id: string | null
  started_at: string | null
  completed_at: string | null
  error_code: string | null
  created_at: string
  allowed_actions?: readonly string[]
}

export type DataQualityIssueDto = {
  id: string
  project_id: string
  data_quality_run_id: string
  dataset_version_id: string
  rule_code: string
  issue_type: string
  severity: string
  column_id: string | null
  affected_row_count: number | null
  affected_rows: readonly unknown[] | null
  evidence: Record<string, unknown>
  description: string
  suggested_actions: readonly Record<string, unknown>[] | null
  requires_approval: boolean
  status: string
  created_at: string
  resolved_at: string | null
  allowed_actions?: readonly string[]
}

export type CleaningPlanDto = {
  id: string
  project_id: string
  dataset_version_id: string
  title: string
  rationale: string | null
  status: string
  actions: readonly Record<string, unknown>[]
  preview_summary: Record<string, unknown> | null
  preview_hash: string | null
  affected_row_count: number | null
  affected_column_count: number | null
  source_model_invocation_id: string | null
  approval_record_id: string | null
  payload_hash: string | null
  lock_version: number
  transformation_id: string | null
  job_id: string | null
  created_at: string
  updated_at: string
  allowed_actions?: readonly string[]
}

export type DataTransformationDto = {
  id: string
  project_id: string
  cleaning_plan_id: string
  approval_record_id: string
  source_dataset_version_id: string
  target_dataset_version_id: string | null
  status: string
  action_count: number
  affected_row_count: number | null
  affected_column_count: number | null
  parameters_hash: string
  output_artifact_id: string | null
  log_artifact_id: string | null
  processing_run_id: string | null
  started_at: string | null
  completed_at: string | null
  error_code: string | null
  created_at: string
}

export type VersionComparisonDto = {
  dataset_id: string
  base_version_id: string
  target_version_id: string
  row_count: { before: number | null; after: number | null; delta: number }
  column_count: { before: number | null; after: number | null; delta: number }
  missing_cells: { before: number; after: number }
  actions: readonly Record<string, unknown>[]
  affected_row_count: number | null
  affected_column_count: number | null
  lineage: {
    parent_version_id: string | null
    transformation_id: string | null
    output_artifact_id: string | null
  }
}

export type QualityIssuesEnvelope = DataEnvelope<
  readonly DataQualityIssueDto[]
> & {
  pagination: { page: number; page_size: number; total: number; pages: number }
}

function contractEnvelope<T>(value: unknown, label: string): DataEnvelope<T> {
  const root = objectValue(value)
  if (!root || !("data" in root)) {
    throw new ApiError(
      0,
      "UNKNOWN",
      `${label} did not match the frontend contract.`,
      "FRONTEND_CONTRACT_MISMATCH",
    )
  }
  return root as DataEnvelope<T>
}

function contractQualityIssues(value: unknown): QualityIssuesEnvelope {
  const envelope = contractEnvelope<readonly DataQualityIssueDto[]>(
    value,
    "Quality issues response",
  )
  const root = objectValue(value)
  const pagination = objectValue(root?.pagination)
  if (!pagination) {
    throw new ApiError(
      0,
      "UNKNOWN",
      "Quality issues pagination was unavailable.",
      "FRONTEND_CONTRACT_MISMATCH",
    )
  }
  return {
    ...envelope,
    pagination: pagination as QualityIssuesEnvelope["pagination"],
  }
}

export class ProjectsApi {
  static list = (query: PageQuery & { q?: string } = {}) =>
    unwrap(projectsListProjectsGetApiV1Projects({ query }))
  static get = (projectId: string) =>
    unwrap(
      projectsGetProjectGetApiV1ProjectsProjectId({
        path: { project_id: projectId },
      }),
    )
  static overview = (projectId: string) =>
    unwrap(
      projectsGetProjectOverviewGetApiV1ProjectsProjectIdOverview({
        path: { project_id: projectId },
      }),
    )
  static create = (
    body: import("../generated/types.gen").ProjectCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      projectsCreateProjectPostApiV1Projects({
        body,
        headers: { "Idempotency-Key": idempotencyKey },
      }),
    )
  static update = (
    projectId: string,
    body: import("../generated/types.gen").ProjectUpdate,
    lockVersion: number,
  ) =>
    unwrap(
      projectsUpdateProjectPatchApiV1ProjectsProjectId({
        path: { project_id: projectId },
        headers: { "If-Match": `"${lockVersion}"` },
        body,
      }),
    )
  static archive = (projectId: string) =>
    unwrap(
      projectsArchiveProjectPostApiV1ProjectsProjectIdArchive({
        path: { project_id: projectId },
      }),
    )
  static restore = (projectId: string) =>
    unwrap(
      projectsRestoreProjectPostApiV1ProjectsProjectIdRestore({
        path: { project_id: projectId },
      }),
    )
}

export class ResearchQuestionsApi {
  static current = (projectId: string) =>
    unwrap(
      researchQuestionsGetCurrentProjectResearchQuestionGetApiV1ProjectsProjectIdResearchQuestion(
        { path: { project_id: projectId } },
      ),
    )
  static get = (researchQuestionId: string) =>
    unwrap(
      researchQuestionsGetResearchQuestionGetApiV1ResearchQuestionsResearchQuestionId(
        { path: { research_question_id: researchQuestionId } },
      ),
    )
  static listVersions = (researchQuestionId: string) =>
    unwrap(
      researchQuestionsListResearchQuestionVersionsGetApiV1ResearchQuestionsResearchQuestionIdVersions(
        { path: { research_question_id: researchQuestionId } },
      ),
    )
  static getVersion = (versionId: string) =>
    unwrap(
      researchQuestionsGetResearchQuestionVersionGetApiV1ResearchQuestionVersionsVersionId(
        { path: { version_id: versionId } },
      ),
    )
  static create = (
    projectId: string,
    body: import("../generated/types.gen").ResearchQuestionCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      researchQuestionsCreateResearchQuestionPostApiV1ProjectsProjectIdResearchQuestions(
        {
          path: { project_id: projectId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static createVersion = (
    researchQuestionId: string,
    body: import("../generated/types.gen").ResearchQuestionVersionCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      researchQuestionsCreateResearchQuestionVersionPostApiV1ResearchQuestionsResearchQuestionIdVersions(
        {
          path: { research_question_id: researchQuestionId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static markReady = (
    versionId: string,
    body: import("../generated/types.gen").ResearchQuestionMarkReady,
    idempotencyKey: string,
  ) =>
    unwrap(
      researchQuestionsMarkResearchQuestionVersionReadyPostApiV1ResearchQuestionVersionsVersionIdReady(
        {
          path: { version_id: versionId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static requestConfirmation = (versionId: string, idempotencyKey: string) =>
    unwrap(
      researchQuestionsRequestResearchQuestionConfirmationPostApiV1ResearchQuestionVersionsVersionIdApprovalRequests(
        {
          path: { version_id: versionId },
          headers: { "Idempotency-Key": idempotencyKey },
        },
      ),
    )
}

export class QueryPlansApi {
  static create = (
    projectId: string,
    body: import("../generated/types.gen").QueryPlanCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      queryPlansCreateQueryPlanPostApiV1ProjectsProjectIdQueryPlans({
        path: { project_id: projectId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static get = (queryPlanId: string) =>
    unwrap(
      queryPlansGetQueryPlanGetApiV1QueryPlansQueryPlanId({
        path: { query_plan_id: queryPlanId },
      }),
    )
  static update = (
    queryPlanId: string,
    body: import("../generated/types.gen").QueryPlanUpdate,
    lockVersion: number,
  ) =>
    unwrap(
      queryPlansUpdateQueryPlanPatchApiV1QueryPlansQueryPlanId({
        path: { query_plan_id: queryPlanId },
        headers: { "If-Match": `"${lockVersion}"` },
        body,
      }),
    )
  static generate = (queryPlanId: string, idempotencyKey: string) =>
    unwrap(
      queryPlansGenerateQueryPlanPostApiV1QueryPlansQueryPlanIdGenerate({
        path: { query_plan_id: queryPlanId },
        headers: { "Idempotency-Key": idempotencyKey },
        body: {},
      }),
    )
}

export type LiteratureSearchQuery = PageQuery & {
  verification_status?: import("../generated/types.gen").LiteratureVerificationStatus
  open_access_status?: string
  from_year?: number
  to_year?: number
  q?: string
}

export type LiteratureListQuery = PageQuery & {
  decision?: import("../generated/types.gen").LiteratureDecisionStatus
  verification_status?: import("../generated/types.gen").LiteratureVerificationStatus
  has_document?: boolean
  year_from?: number
  year_to?: number
  q?: string
}

export class LiteratureApi {
  static search = (
    queryPlanId: string,
    body: import("../generated/types.gen").LiteratureSearchCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      literatureCreateSearchRunPostApiV1QueryPlansQueryPlanIdSearchRuns({
        path: { query_plan_id: queryPlanId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static results = (searchRunId: string, query: LiteratureSearchQuery = {}) =>
    unwrap(
      literatureGetSearchResultsGetApiV1LiteratureSearchRunsSearchRunIdResults({
        path: { search_run_id: searchRunId },
        query,
      }),
    )
  static importCandidates = (
    projectId: string,
    body: import("../generated/types.gen").LiteratureImportRequest,
    idempotencyKey: string,
  ) =>
    unwrap(
      literatureImportSearchCandidatesPostApiV1ProjectsProjectIdLiteratureImport(
        {
          path: { project_id: projectId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static importDoi = (
    projectId: string,
    body: import("../generated/types.gen").LiteratureDoiImportRequest,
    idempotencyKey: string,
  ) =>
    unwrap(
      literatureImportDoiPostApiV1ProjectsProjectIdLiteratureImportDoi({
        path: { project_id: projectId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static list = (projectId: string, query: LiteratureListQuery = {}) =>
    unwrap(
      literatureListLiteratureGetApiV1ProjectsProjectIdLiterature({
        path: { project_id: projectId },
        query,
      }),
    )
  static get = (literatureId: string) =>
    unwrap(
      literatureGetLiteratureGetApiV1LiteratureLiteratureId({
        path: { literature_id: literatureId },
      }),
    )
}

export type LiteratureMatrixQuery = {
  included_only?: boolean
  field_codes?: import("../generated/types.gen").LiteratureFieldCode[] | null
  page?: number
  page_size?: number
  sort?: import("../generated/types.gen").MatrixSort
  order?: import("../generated/types.gen").SortOrder
}

export class EvidenceApi {
  static matrix = (projectId: string, query: LiteratureMatrixQuery = {}) =>
    unwrap(
      evidenceGetLiteratureMatrixGetApiV1ProjectsProjectIdLiteratureMatrix({
        path: { project_id: projectId },
        query,
      }),
    )
  static extraction = (extractionId: string) =>
    unwrap(
      evidenceGetLiteratureExtractionGetApiV1LiteratureExtractionsExtractionId({
        path: { extraction_id: extractionId },
      }),
    )
  static createExtraction = (
    documentId: string,
    body: import("../generated/types.gen").LiteratureExtractionCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      evidenceCreateLiteratureExtractionPostApiV1DocumentsDocumentIdLiteratureExtractions(
        {
          path: { document_id: documentId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static correctField = (
    fieldId: string,
    lockVersion: number,
    body: import("../generated/types.gen").LiteratureExtractionFieldCorrection,
    idempotencyKey: string,
  ) =>
    unwrap(
      evidenceUpdateLiteratureExtractionFieldPatchApiV1LiteratureExtractionFieldsFieldId(
        {
          path: { field_id: fieldId },
          headers: {
            "If-Match": `"${lockVersion}"`,
            "Idempotency-Key": idempotencyKey,
          },
          body,
        },
      ),
    )
  static span = (evidenceSpanId: string) =>
    unwrap(
      evidenceGetEvidenceSpanGetApiV1EvidenceSpansEvidenceSpanId({
        path: { evidence_span_id: evidenceSpanId },
      }),
    )
  static createSpan = (
    documentId: string,
    body: import("../generated/types.gen").ManualEvidenceSpanCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      evidenceCreateEvidenceSpanPostApiV1DocumentsDocumentIdEvidenceSpans({
        path: { document_id: documentId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static verifySpan = (
    evidenceSpanId: string,
    body: import("../generated/types.gen").EvidenceSpanVerificationCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      evidenceCreateEvidenceSpanVerificationPostApiV1EvidenceSpansEvidenceSpanIdVerificationRecords(
        {
          path: { evidence_span_id: evidenceSpanId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static decisions = (literatureId: string) =>
    unwrap(
      evidenceListLiteratureDecisionsGetApiV1LiteratureLiteratureIdDecisions({
        path: { literature_id: literatureId },
      }),
    )
  static decide = (
    literatureId: string,
    body: import("../generated/types.gen").LiteratureDecisionCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      evidenceCreateLiteratureDecisionPostApiV1LiteratureLiteratureIdDecisions({
        path: { literature_id: literatureId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static search = (
    projectId: string,
    body: import("../generated/types.gen").EvidenceSearchRequest,
  ) =>
    unwrap(
      evidenceSearchProjectEvidencePostApiV1ProjectsProjectIdEvidenceSearch({
        path: { project_id: projectId },
        body,
      }),
    )
  static createSummary = (
    projectId: string,
    body: import("../generated/types.gen").EvidenceSetSummaryCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      evidenceCreateEvidenceSetSummaryPostApiV1ProjectsProjectIdEvidenceSetSummaries(
        {
          path: { project_id: projectId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static summary = (summaryId: string) =>
    unwrap(
      evidenceGetEvidenceSetSummaryGetApiV1EvidenceSetSummariesSummaryId({
        path: { summary_id: summaryId },
      }),
    )
  static generateTopics = (
    projectId: string,
    body: import("../generated/types.gen").TopicGenerationCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      evidenceCreateTopicGenerationRunPostApiV1ProjectsProjectIdTopicGenerationRuns(
        {
          path: { project_id: projectId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static topicRun = (runId: string) =>
    unwrap(
      evidenceGetTopicGenerationRunGetApiV1TopicGenerationRunsRunId({
        path: { run_id: runId },
      }),
    )
}

export class DocumentsApi {
  static upload = (
    projectId: string,
    file: File,
    documentType: import("../generated/types.gen").DocumentType,
    literatureRecordId: string | null,
    idempotencyKey: string,
  ) =>
    unwrap(
      documentsUploadDocumentPostApiV1ProjectsProjectIdDocuments({
        path: { project_id: projectId },
        headers: { "Idempotency-Key": idempotencyKey },
        body: {
          file,
          document_type: documentType,
          literature_record_id: literatureRecordId,
        },
      }),
    )
  static get = (documentId: string) =>
    unwrap(
      documentsGetDocumentGetApiV1DocumentsDocumentId({
        path: { document_id: documentId },
      }),
    )
  static parse = (
    documentId: string,
    body: import("../generated/types.gen").DocumentParseRequest,
    idempotencyKey: string,
  ) =>
    unwrap(
      documentsParseDocumentPostApiV1DocumentsDocumentIdParse({
        path: { document_id: documentId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static listPages = (documentId: string) =>
    unwrap(
      documentsListDocumentPagesGetApiV1DocumentsDocumentIdPages({
        path: { document_id: documentId },
      }),
    )
  static getPage = (documentId: string, pageNumber: number) =>
    unwrap(
      documentsGetDocumentPageGetApiV1DocumentsDocumentIdPagesPageNumber({
        path: { document_id: documentId, page_number: pageNumber },
      }),
    )
}

export class MembersApi {
  static list = (projectId: string, query: PageQuery = {}) =>
    unwrap(
      projectsListProjectMembersGetApiV1ProjectsProjectIdMembers({
        path: { project_id: projectId },
        query,
      }),
    )
  static add = (
    projectId: string,
    body: import("../generated/types.gen").MemberAdd,
    idempotencyKey: string,
  ) =>
    unwrap(
      projectsAddProjectMemberPostApiV1ProjectsProjectIdMembers({
        path: { project_id: projectId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static update = (
    projectId: string,
    memberId: string,
    body: import("../generated/types.gen").MemberUpdate,
    idempotencyKey: string,
  ) =>
    unwrap(
      projectsUpdateProjectMemberPatchApiV1ProjectsProjectIdMembersMemberId({
        path: { project_id: projectId, member_id: memberId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static remove = (
    projectId: string,
    memberId: string,
    idempotencyKey: string,
  ) =>
    unwrapVoid(
      projectsRemoveProjectMemberDeleteApiV1ProjectsProjectIdMembersMemberId({
        path: { project_id: projectId, member_id: memberId },
        headers: { "Idempotency-Key": idempotencyKey },
      }),
    )
}

export class ArtifactsApi {
  static list = (projectId: string, query: PageQuery = {}) =>
    unwrap(
      artifactsListProjectArtifactsGetApiV1ProjectsProjectIdArtifacts({
        path: { project_id: projectId },
        query,
      }),
    )
  static initiate = (
    projectId: string,
    body: import("../generated/types.gen").ArtifactUploadInitiate,
    idempotencyKey: string,
  ) =>
    unwrap(
      artifactsInitiateArtifactUploadPostApiV1ProjectsProjectIdArtifactsUploads(
        {
          path: { project_id: projectId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static transfer = (uploadId: string, file: File) =>
    unwrapVoid(
      client.put({
        url: "/api/v1/artifact-uploads/{upload_id}/content",
        path: { upload_id: uploadId },
        body: file,
        bodySerializer: null,
        headers: { "Content-Type": "application/octet-stream" },
        security: [{ scheme: "bearer", type: "http" }],
      }),
    )
  static complete = (
    projectId: string,
    uploadId: string,
    body: import("../generated/types.gen").ArtifactUploadComplete,
    idempotencyKey: string,
  ) =>
    unwrap(
      artifactsCompleteArtifactUploadPostApiV1ProjectsProjectIdArtifactsUploadsUploadIdComplete(
        {
          path: { project_id: projectId, upload_id: uploadId },
          headers: { "Idempotency-Key": idempotencyKey },
          body,
        },
      ),
    )
  static download = (artifactId: string) =>
    unwrap(
      artifactsAuthorizeArtifactDownloadGetApiV1ArtifactsArtifactIdDownload({
        path: { artifact_id: artifactId },
      }),
    )
}

export class DatasetsApi {
  static list = async (projectId: string) =>
    contractEnvelope<readonly DatasetDto[]>(
      await unwrap(
        datasetsListDatasetsGetApiV1ProjectsProjectIdDatasets({
          path: { project_id: projectId },
        }),
      ),
      "Dataset list response",
    )

  static upload = async (
    projectId: string,
    input: {
      file: File
      name: string
      sourceType?: import("../generated/types.gen").DatasetSourceType
      publisher?: string | null
      sourcePlatform?: string | null
      sourceIdentifier?: string | null
      licenseName?: string | null
      licenseStatus?: import("../generated/types.gen").DatasetLicenseStatus
    },
    idempotencyKey: string,
  ) =>
    contractEnvelope<{ dataset: DatasetDto; version: DatasetVersionDto }>(
      await unwrap(
        datasetsUploadDatasetPostApiV1ProjectsProjectIdDatasets({
          path: { project_id: projectId },
          headers: { "Idempotency-Key": idempotencyKey },
          body: {
            file: input.file,
            name: input.name,
            source_type: input.sourceType ?? "USER_UPLOAD",
            publisher: input.publisher,
            source_platform: input.sourcePlatform,
            source_identifier: input.sourceIdentifier,
            license_name: input.licenseName,
            license_status: input.licenseStatus ?? "UNKNOWN",
          },
        }),
      ),
      "Dataset upload response",
    )

  static get = async (datasetId: string) =>
    contractEnvelope<DatasetDto>(
      await unwrap(
        datasetsGetDatasetGetApiV1DatasetsDatasetId({
          path: { dataset_id: datasetId },
        }),
      ),
      "Dataset response",
    )

  static update = async (
    datasetId: string,
    body: import("../generated/types.gen").DatasetUpdate,
    lockVersion: number,
  ) =>
    contractEnvelope<DatasetDto>(
      await unwrap(
        datasetsUpdateDatasetPatchApiV1DatasetsDatasetId({
          path: { dataset_id: datasetId },
          headers: { "If-Match": String(lockVersion) },
          body,
        }),
      ),
      "Dataset update response",
    )

  static version = async (versionId: string) =>
    contractEnvelope<DatasetVersionDto>(
      await unwrap(
        datasetsGetDatasetVersionGetApiV1DatasetVersionsVersionId({
          path: { version_id: versionId },
        }),
      ),
      "Dataset version response",
    )

  static versions = async (datasetId: string) =>
    contractEnvelope<readonly DatasetVersionDto[]>(
      await unwrap(
        datasetsListDatasetVersionsGetApiV1DatasetsDatasetIdVersions({
          path: { dataset_id: datasetId },
        }),
      ),
      "Dataset version history response",
    )

  static worksheets = async (versionId: string) =>
    contractEnvelope<{
      version_id: string
      selected_worksheet_name: string | null
      worksheets: readonly WorksheetDto[]
    }>(
      await unwrap(
        datasetsGetWorksheetsGetApiV1DatasetVersionsVersionIdWorksheets({
          path: { version_id: versionId },
        }),
      ),
      "Worksheet response",
    )

  static selectWorksheet = async (
    versionId: string,
    body: import("../generated/types.gen").WorksheetSelection,
    idempotencyKey: string,
  ) =>
    contractEnvelope<DatasetVersionDto>(
      await unwrap(
        datasetsSelectWorksheetPostApiV1DatasetVersionsVersionIdWorksheetSelection(
          {
            path: { version_id: versionId },
            headers: { "Idempotency-Key": idempotencyKey },
            body,
          },
        ),
      ),
      "Worksheet selection response",
    )

  static preview = async (
    versionId: string,
    query: { offset?: number; limit?: number; columns?: string[] } = {},
  ) =>
    contractEnvelope<DatasetPreviewDto>(
      await unwrap(
        datasetsPreviewDatasetVersionGetApiV1DatasetVersionsVersionIdPreview({
          path: { version_id: versionId },
          query,
        }),
      ),
      "Dataset preview response",
    )

  static columns = async (versionId: string) =>
    contractEnvelope<readonly DatasetColumnDto[]>(
      await unwrap(
        datasetsListDatasetColumnsGetApiV1DatasetVersionsVersionIdColumns({
          path: { version_id: versionId },
        }),
      ),
      "Dataset columns response",
    )

  static updateColumn = async (
    columnId: string,
    body: import("../generated/types.gen").DatasetColumnUpdate,
    lockVersion: number,
  ) =>
    contractEnvelope<DatasetColumnDto>(
      await unwrap(
        datasetsUpdateDatasetColumnPatchApiV1DatasetColumnsColumnId({
          path: { column_id: columnId },
          headers: { "If-Match": String(lockVersion) },
          body,
        }),
      ),
      "Dataset column update response",
    )
}

export class DataQualityApi {
  static run = async (
    versionId: string,
    body: import("../generated/types.gen").QualityRunCreate,
    idempotencyKey: string,
  ) =>
    contractEnvelope<{
      run: DataQualityRunDto
      job: import("../generated/types.gen").JobPublic
    }>(
      await unwrap(
        dataQualityRequestQualityRunPostApiV1DatasetVersionsVersionIdQualityRuns(
          {
            path: { version_id: versionId },
            headers: { "Idempotency-Key": idempotencyKey },
            body,
          },
        ),
      ),
      "Quality run response",
    )

  static get = async (runId: string) =>
    contractEnvelope<DataQualityRunDto>(
      await unwrap(
        dataQualityGetQualityRunGetApiV1DataQualityRunsRunId({
          path: { run_id: runId },
        }),
      ),
      "Quality run response",
    )

  static issues = async (
    runId: string,
    query: {
      severity?: import("../generated/types.gen").DataQualitySeverity
      issue_type?: import("../generated/types.gen").DataQualityIssueType
      status?: import("../generated/types.gen").DataQualityIssueStatus
      column_id?: string
      page?: number
      page_size?: number
    } = {},
  ) =>
    contractQualityIssues(
      await unwrap(
        dataQualityListQualityIssuesGetApiV1DataQualityRunsRunIdIssues({
          path: { run_id: runId },
          query,
        }),
      ),
    )

  static acknowledge = async (issueId: string, idempotencyKey: string) =>
    contractEnvelope<DataQualityIssueDto>(
      await unwrap(
        dataQualityAcknowledgeQualityIssuePostApiV1DataQualityIssuesIssueIdAcknowledge(
          {
            path: { issue_id: issueId },
            headers: { "Idempotency-Key": idempotencyKey },
            body: {},
          },
        ),
      ),
      "Quality issue acknowledgement response",
    )

  static ignore = async (
    issueId: string,
    reason: string,
    idempotencyKey: string,
  ) =>
    contractEnvelope<DataQualityIssueDto>(
      await unwrap(
        dataQualityIgnoreQualityIssuePostApiV1DataQualityIssuesIssueIdIgnore({
          path: { issue_id: issueId },
          headers: { "Idempotency-Key": idempotencyKey },
          body: { reason },
        }),
      ),
      "Quality issue ignore response",
    )
}

export class AnalysisApi {
  static create = (
    projectId: string,
    body: import("../generated/types.gen").AnalysisPlanCreate,
  ) =>
    unwrap(
      analysisCreateAnalysisPlanPostApiV1ProjectsProjectIdAnalysisPlans({
        path: { project_id: projectId },
        body,
      }),
    )

  static getPlan = (planId: string) =>
    unwrap(
      analysisGetAnalysisPlanGetApiV1AnalysisPlansPlanId({
        path: { plan_id: planId },
      }),
    )

  static update = (
    planId: string,
    body: import("../generated/types.gen").AnalysisPlanUpdate,
    lockVersion: number,
  ) =>
    unwrap(
      analysisUpdateAnalysisPlanPatchApiV1AnalysisPlansPlanId({
        path: { plan_id: planId },
        headers: { "If-Match": String(lockVersion) },
        body,
      }),
    )

  static validate = (planId: string, idempotencyKey: string) =>
    unwrap(
      analysisValidateAnalysisPlanPostApiV1AnalysisPlansPlanIdValidate({
        path: { plan_id: planId },
        headers: { "Idempotency-Key": idempotencyKey },
      }),
    )

  static requestApproval = (planId: string) =>
    unwrap(
      analysisRequestAnalysisApprovalPostApiV1AnalysisPlansPlanIdApprovalRequests(
        { path: { plan_id: planId } },
      ),
    )

  static run = (
    planId: string,
    body: import("../generated/types.gen").AnalysisRunCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      analysisRunAnalysisPlanPostApiV1AnalysisPlansPlanIdRuns({
        path: { plan_id: planId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )

  static getRun = (runId: string) =>
    unwrap(
      analysisGetAnalysisRunGetApiV1AnalysisRunsRunId({
        path: { run_id: runId },
      }),
    )

  static getResults = (runId: string) =>
    unwrap(
      analysisGetAnalysisResultsGetApiV1AnalysisRunsRunIdResults({
        path: { run_id: runId },
      }),
    )

  static invalidate = (runId: string, reason: string) =>
    unwrap(
      analysisInvalidateAnalysisRunPostApiV1AnalysisRunsRunIdInvalidate({
        path: { run_id: runId },
        body: { reason },
      }),
    )
}

export class FiguresApi {
  static create = (
    projectId: string,
    body: import("../generated/types.gen").FigurePlanCreate,
  ) =>
    unwrap(
      figuresCreateFigurePlanPostApiV1ProjectsProjectIdFigurePlans({
        path: { project_id: projectId },
        body,
      }),
    )

  static getPlan = (planId: string) =>
    unwrap(
      figuresGetFigurePlanGetApiV1FigurePlansPlanId({
        path: { plan_id: planId },
      }),
    )

  static recommend = (
    projectId: string,
    body: import("../generated/types.gen").FigureRecommendationRequest,
  ) =>
    unwrap(
      figuresGetFigureRecommendationsPostApiV1ProjectsProjectIdFigureRecommendations(
        { path: { project_id: projectId }, body },
      ),
    )

  static render = (
    planId: string,
    body: import("../generated/types.gen").FigureRenderCreate,
    idempotencyKey: string,
  ) =>
    unwrap(
      figuresRenderFigurePlanPostApiV1FigurePlansPlanIdRenderRuns({
        path: { plan_id: planId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )

  static getRenderRun = (runId: string) =>
    unwrap(
      figuresGetFigureRenderRunGetApiV1FigureRenderRunsRunId({
        path: { run_id: runId },
      }),
    )

  static get = (figureId: string) =>
    unwrap(
      figuresGetFigureGetApiV1FiguresFigureId({
        path: { figure_id: figureId },
      }),
    )

  static issues = (figureId: string) =>
    unwrap(
      figuresGetFigureValidationIssuesGetApiV1FiguresFigureIdValidationIssues({
        path: { figure_id: figureId },
      }),
    )

  static requestConfirmation = (figureId: string) =>
    unwrap(
      figuresRequestFigureConfirmationPostApiV1FiguresFigureIdApprovalRequests({
        path: { figure_id: figureId },
      }),
    )

  static download = (figureId: string, formatName: string) =>
    unwrap(
      figuresDownloadFigureFormatGetApiV1FiguresFigureIdDownloadsFormatName({
        path: { figure_id: figureId, format_name: formatName.toLowerCase() },
      }),
    )
}

export class DataCleaningApi {
  static create = async (
    versionId: string,
    body: import("../generated/types.gen").CleaningPlanCreate,
    idempotencyKey: string,
  ) =>
    contractEnvelope<CleaningPlanDto>(
      await unwrap(
        dataCleaningCreateCleaningPlanPostApiV1DatasetVersionsVersionIdCleaningPlans(
          {
            path: { version_id: versionId },
            headers: { "Idempotency-Key": idempotencyKey },
            body,
          },
        ),
      ),
      "Cleaning plan response",
    )

  static get = async (planId: string) =>
    contractEnvelope<CleaningPlanDto>(
      await unwrap(
        dataCleaningGetCleaningPlanGetApiV1CleaningPlansPlanId({
          path: { plan_id: planId },
        }),
      ),
      "Cleaning plan response",
    )

  static transformation = async (transformationId: string) =>
    contractEnvelope<DataTransformationDto>(
      await unwrap(
        dataCleaningGetDataTransformationGetApiV1DataTransformationsTransformationId(
          {
            path: { transformation_id: transformationId },
          },
        ),
      ),
      "Data transformation response",
    )

  static update = async (
    planId: string,
    body: import("../generated/types.gen").CleaningPlanUpdate,
    lockVersion: number,
  ) =>
    contractEnvelope<CleaningPlanDto>(
      await unwrap(
        dataCleaningUpdateCleaningPlanPatchApiV1CleaningPlansPlanId({
          path: { plan_id: planId },
          headers: { "If-Match": String(lockVersion) },
          body,
        }),
      ),
      "Cleaning plan update response",
    )

  static preview = async (planId: string, idempotencyKey: string) =>
    contractEnvelope<CleaningPlanDto>(
      await unwrap(
        dataCleaningPreviewCleaningPlanPostApiV1CleaningPlansPlanIdPreview({
          path: { plan_id: planId },
          headers: { "Idempotency-Key": idempotencyKey },
        }),
      ),
      "Cleaning plan preview response",
    )

  static requestApproval = async (planId: string, idempotencyKey: string) =>
    contractEnvelope<{
      approval_id: string
      cleaning_plan_id: string
      status: string
      payload_hash: string
      expires_at: string
    }>(
      await unwrap(
        dataCleaningRequestCleaningPlanApprovalPostApiV1CleaningPlansPlanIdApprovalRequests(
          {
            path: { plan_id: planId },
            headers: { "Idempotency-Key": idempotencyKey },
          },
        ),
      ),
      "Cleaning plan approval response",
    )

  static execute = async (planId: string, idempotencyKey: string) =>
    contractEnvelope<{
      transformation: DataTransformationDto
      job: import("../generated/types.gen").JobPublic
    }>(
      await unwrap(
        dataCleaningExecuteCleaningPlanPostApiV1CleaningPlansPlanIdExecute({
          path: { plan_id: planId },
          headers: { "Idempotency-Key": idempotencyKey },
        }),
      ),
      "Cleaning plan execution response",
    )

  static compare = async (
    datasetId: string,
    baseVersionId: string,
    targetVersionId: string,
  ) =>
    contractEnvelope<VersionComparisonDto>(
      await unwrap(
        dataCleaningCompareDatasetVersionsGetApiV1DatasetsDatasetIdVersionComparison(
          {
            path: { dataset_id: datasetId },
            query: {
              base_version_id: baseVersionId,
              target_version_id: targetVersionId,
            },
          },
        ),
      ),
      "Dataset version comparison response",
    )
}

export class JobsApi {
  static list = (projectId: string, query: PageQuery = {}) =>
    unwrap(
      jobsListProjectJobsGetApiV1ProjectsProjectIdJobs({
        path: { project_id: projectId },
        query,
      }),
    )
  static get = (jobId: string) =>
    unwrap(jobsGetJobGetApiV1JobsJobId({ path: { job_id: jobId } }))
  static retry = (jobId: string, idempotencyKey: string) =>
    unwrap(
      jobsRetryJobPostApiV1JobsJobIdRetry({
        path: { job_id: jobId },
        headers: { "Idempotency-Key": idempotencyKey },
      }),
    )
  static cancel = (jobId: string, reason: string, idempotencyKey: string) =>
    unwrap(
      jobsCancelJobPostApiV1JobsJobIdCancel({
        path: { job_id: jobId },
        headers: { "Idempotency-Key": idempotencyKey },
        body: { reason },
      }),
    )
  static stream = async (
    jobId: string,
    lastEventId?: number,
    signal?: AbortSignal,
  ) => {
    const stream = await unwrap<unknown>(
      client.get({
        url: "/api/v1/jobs/{job_id}/events",
        path: { job_id: jobId },
        headers: { "Last-Event-ID": lastEventId },
        parseAs: "stream",
        signal,
        security: [{ scheme: "bearer", type: "http" }],
      }),
    )
    if (!(stream instanceof ReadableStream)) {
      throw new ApiError(0, "UNKNOWN", "The job event stream was unavailable.")
    }
    return stream as ReadableStream<Uint8Array>
  }
}

export class ApprovalsApi {
  static list = (projectId: string, query: PageQuery = {}) =>
    unwrap(
      approvalsListProjectApprovalsGetApiV1ProjectsProjectIdApprovals({
        path: { project_id: projectId },
        query,
      }),
    )
  static get = (approvalId: string) =>
    unwrap(
      approvalsGetApprovalGetApiV1ApprovalsApprovalId({
        path: { approval_id: approvalId },
      }),
    )
  static approve = (
    approvalId: string,
    body: import("../generated/types.gen").ApprovalDecisionRequest,
    idempotencyKey: string,
  ) =>
    unwrap(
      approvalsApprovePostApiV1ApprovalsApprovalIdApprove({
        path: { approval_id: approvalId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static reject = (
    approvalId: string,
    body: import("../generated/types.gen").ApprovalRejectRequest,
    idempotencyKey: string,
  ) =>
    unwrap(
      approvalsRejectPostApiV1ApprovalsApprovalIdReject({
        path: { approval_id: approvalId },
        headers: { "Idempotency-Key": idempotencyKey },
        body,
      }),
    )
  static cancel = (approvalId: string, idempotencyKey: string) =>
    unwrap(
      approvalsCancelPostApiV1ApprovalsApprovalIdCancel({
        path: { approval_id: approvalId },
        headers: { "Idempotency-Key": idempotencyKey },
      }),
    )
}

export class AuditApi {
  static list = (projectId: string, query: PageQuery = {}) =>
    unwrap(
      projectsListProjectAuditLogsGetApiV1ProjectsProjectIdAuditLogs({
        path: { project_id: projectId },
        query,
      }),
    )
}

export class HealthApi {
  static live = () => unwrap(healthLiveHealthGetApiV1HealthLive())
  static ready = () => unwrap(healthReadyHealthGetApiV1HealthReady())
  static dependencies = () =>
    unwrap(healthDependenciesHealthGetApiV1HealthDependencies())
}

export class AuthApi {
  static login = async (body: { username: string; password: string }) =>
    unwrap(
      loginLoginAccessTokenPostApiV1LoginAccessToken({
        body: { ...body, grant_type: "password" },
      }),
    )
  static recoverPassword = async (email: string) =>
    unwrap(
      loginRecoverPasswordPostApiV1PasswordRecoveryEmail({
        path: { email },
      }),
    )
  static resetPassword = async (body: {
    token: string
    new_password: string
  }) => unwrap(loginResetPasswordPostApiV1ResetPassword({ body }))
}

export class UsersApi {
  static current = async () => unwrap(usersReadUserMeGetApiV1UsersMe())
  static list = async (skip = 0, limit = 100) =>
    unwrap(usersReadUsersGetApiV1Users({ query: { skip, limit } }))
  static create = async (body: import("../generated/types.gen").UserCreate) =>
    unwrap(usersCreateUserPostApiV1Users({ body }))
  static signup = async (body: import("../generated/types.gen").UserRegister) =>
    unwrap(usersRegisterUserPostApiV1UsersSignup({ body }))
  static updateMe = async (
    body: import("../generated/types.gen").UserUpdateMe,
  ) => unwrap(usersUpdateUserMePatchApiV1UsersMe({ body }))
  static changePassword = async (
    body: import("../generated/types.gen").UpdatePassword,
  ) => unwrap(usersUpdatePasswordMePatchApiV1UsersMePassword({ body }))
  static deleteMe = async () => unwrap(usersDeleteUserMeDeleteApiV1UsersMe())
  static update = async (
    userId: string,
    body: import("../generated/types.gen").UserUpdate,
  ) =>
    unwrap(
      usersUpdateUserPatchApiV1UsersUserId({
        path: { user_id: userId },
        body,
      }),
    )
  static delete = async (userId: string) =>
    unwrap(usersDeleteUserDeleteApiV1UsersUserId({ path: { user_id: userId } }))
}

// Temporary names retain the upstream UI call shape while routing exclusively
// through the modern generated client. They are adapter API, not generated code.
export const HealthService = {
  liveHealthGetApiV1HealthLive: HealthApi.live,
  readyHealthGetApiV1HealthReady: HealthApi.ready,
  dependenciesHealthGetApiV1HealthDependencies: HealthApi.dependencies,
}
export const LoginService = {
  loginAccessTokenPostApiV1LoginAccessToken: ({
    formData,
  }: {
    formData: { username: string; password: string }
  }) => AuthApi.login(formData),
  recoverPasswordPostApiV1PasswordRecoveryEmail: ({
    path,
    email,
  }: {
    path?: { email: string }
    email?: string
  }) => AuthApi.recoverPassword(path?.email ?? email ?? ""),
  resetPasswordPostApiV1ResetPassword: ({
    body,
    requestBody,
  }: {
    body?: { token: string; new_password: string }
    requestBody?: { token: string; new_password: string }
  }) => AuthApi.resetPassword(body ?? requestBody!),
}
export const UsersService = {
  readUserMeGetApiV1UsersMe: UsersApi.current,
  readUsersGetApiV1Users: ({ skip = 0, limit = 100 } = {}) =>
    UsersApi.list(skip, limit),
  createUserPostApiV1Users: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UserCreate
    requestBody?: import("../generated/types.gen").UserCreate
  }) => UsersApi.create(body ?? requestBody!),
  registerUserPostApiV1UsersSignup: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UserRegister
    requestBody?: import("../generated/types.gen").UserRegister
  }) => UsersApi.signup(body ?? requestBody!),
  updateUserMePatchApiV1UsersMe: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UserUpdateMe
    requestBody?: import("../generated/types.gen").UserUpdateMe
  }) => UsersApi.updateMe(body ?? requestBody!),
  updatePasswordMePatchApiV1UsersMePassword: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UpdatePassword
    requestBody?: import("../generated/types.gen").UpdatePassword
  }) => UsersApi.changePassword(body ?? requestBody!),
  deleteUserMeDeleteApiV1UsersMe: UsersApi.deleteMe,
  updateUserPatchApiV1UsersUserId: ({
    path,
    userId,
    body,
    requestBody,
  }: {
    path?: { user_id: string }
    userId?: string
    body?: import("../generated/types.gen").UserUpdate
    requestBody?: import("../generated/types.gen").UserUpdate
  }) => UsersApi.update(path?.user_id ?? userId!, body ?? requestBody!),
  deleteUserDeleteApiV1UsersUserId: ({
    path,
    userId,
  }: {
    path?: { user_id: string }
    userId?: string
  }) => UsersApi.delete(path?.user_id ?? userId!),
}
