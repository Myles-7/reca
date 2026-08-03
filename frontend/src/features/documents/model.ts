import type { SemanticTone } from "../projects/model"

export const documentRoute =
  "/projects/$projectId/documents/$documentId" as const

export type DocumentViewModel = {
  id: string
  projectId: string
  artifactId: string
  literatureRecordId: string | null
  documentType: string
  parserType: string
  parseStatus: string
  knownStatus: boolean
  tone: SemanticTone
  parseConfidence: string
  pageCount: number | null
  language: string | null
  isScanned: boolean | null
  permissions: { canParse: boolean }
  updatedAt: string
}

export type DocumentPageViewModel = {
  pageNumber: number
  printedPageLabel: string | null
  textContent: string | null
}

export type DocumentJobViewModel = {
  id: string
  status: string
  knownStatus: boolean
  tone: SemanticTone
  progressPercent: number
  currentStep: string | null
  retryable: boolean
  retryPermissionKnown: boolean
  canRetry: boolean
  retryDisabledReason: string | null
  errorCode: string | null
  errorMessage: string | null
}

export type DocumentWorkspaceViewModel = {
  document: DocumentViewModel
  pages: readonly DocumentPageViewModel[]
  job: DocumentJobViewModel | null
  permissionsKnown: boolean
  canUpload: boolean
}

export function documentHref(
  projectId: string,
  documentId: string,
  jobId?: string,
): string {
  const path = documentRoute
    .replace("$projectId", projectId)
    .replace("$documentId", documentId)
  return jobId ? `${path}?jobId=${encodeURIComponent(jobId)}` : path
}
