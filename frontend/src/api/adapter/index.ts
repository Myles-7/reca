import { client } from "../generated/client.gen"
import {
  approvalsApprovePostApiV1ApprovalsApprovalIdApprove,
  approvalsCancelPostApiV1ApprovalsApprovalIdCancel,
  approvalsGetApprovalGetApiV1ApprovalsApprovalId,
  approvalsListProjectApprovalsGetApiV1ProjectsProjectIdApprovals,
  approvalsRejectPostApiV1ApprovalsApprovalIdReject,
  artifactsAuthorizeArtifactDownloadGetApiV1ArtifactsArtifactIdDownload,
  artifactsCompleteArtifactUploadPostApiV1ProjectsProjectIdArtifactsUploadsUploadIdComplete,
  artifactsInitiateArtifactUploadPostApiV1ProjectsProjectIdArtifactsUploads,
  artifactsListProjectArtifactsGetApiV1ProjectsProjectIdArtifacts,
  documentsGetDocumentGetApiV1DocumentsDocumentId,
  documentsGetDocumentPageGetApiV1DocumentsDocumentIdPagesPageNumber,
  documentsListDocumentPagesGetApiV1DocumentsDocumentIdPages,
  documentsParseDocumentPostApiV1DocumentsDocumentIdParse,
  documentsUploadDocumentPostApiV1ProjectsProjectIdDocuments,
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
  JobListEnvelope,
  JobPublic,
  LiteratureCandidatePublic,
  LiteratureDoiImportRequest,
  LiteratureImportEnvelope,
  LiteratureImportRequest,
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
