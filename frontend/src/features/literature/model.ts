import type { SemanticTone } from "../projects/model"

export const literatureRoute = "/projects/$projectId/literature" as const

export type LiteratureCandidateViewModel = {
  id: string
  title: string
  authors: string | null
  year: number | null
  doi: string | null
  verificationStatus: string
  degraded: boolean
  importedRecordId: string | null
  canImport: boolean
}

export type LiteratureRecordViewModel = {
  id: string
  title: string
  authors: string | null
  year: number | null
  doi: string | null
  sourceType: string
  verificationStatus: string
  decision: string
  documentId: string | null
  canUploadDocument: boolean
}

export type LiteratureSearchRunViewModel = {
  id: string
  queryPlanId: string
  status: string
  knownStatus: boolean
  tone: SemanticTone
  progressJobId: string | null
  resultCount: number
  cacheHit: boolean
  cacheStale: boolean
  degraded: boolean
  limitations: readonly string[]
  errorCode: string | null
  fetchedAt: string
  retryabilityKnown: boolean
  retryPermissionKnown: boolean
  retryable: boolean
  canRetry: boolean
  retryDisabledReason: string | null
}

export type LiteratureWorkspaceViewModel = {
  records: readonly LiteratureRecordViewModel[]
  activeSearch: LiteratureSearchRunViewModel | null
  candidates: readonly LiteratureCandidateViewModel[]
  permissionsKnown: boolean
  permissions: {
    canSearch: boolean
    canImport: boolean
    canImportDoi: boolean
  }
}

export function literatureHref(
  projectId: string,
  searchRunId?: string,
): string {
  const path = literatureRoute.replace("$projectId", projectId)
  return searchRunId
    ? `${path}?searchRunId=${encodeURIComponent(searchRunId)}`
    : path
}
