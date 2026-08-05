export const manuscriptWorkspaceViews = [
  "manuscript",
  "checks",
  "issues",
  "fixes",
  "audits",
  "claims",
] as const

export type ManuscriptWorkspaceRouteView =
  (typeof manuscriptWorkspaceViews)[number]

export type ManuscriptWorkspaceRouteSearch = {
  manuscript?: string
  version?: string
  checkRun?: string
  issue?: string
  transformation?: string
  audit?: string
  claim?: string
  view?: ManuscriptWorkspaceRouteView
}

const uuid =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const optionalUuid = (value: unknown) =>
  typeof value === "string" && uuid.test(value) ? value : undefined

export function parseManuscriptWorkspaceSearch(
  search: Record<string, unknown>,
): ManuscriptWorkspaceRouteSearch {
  const view =
    typeof search.view === "string" &&
    manuscriptWorkspaceViews.includes(
      search.view as ManuscriptWorkspaceRouteView,
    )
      ? (search.view as ManuscriptWorkspaceRouteView)
      : undefined
  return {
    manuscript: optionalUuid(search.manuscript),
    version: optionalUuid(search.version),
    checkRun: optionalUuid(search.checkRun),
    issue: optionalUuid(search.issue),
    transformation: optionalUuid(search.transformation),
    audit: optionalUuid(search.audit),
    claim: optionalUuid(search.claim),
    view,
  }
}

export const manuscriptWorkspaceRouteContract = {
  path: "/projects/$projectId/manuscript",
  productionIntegrationComplete: true,
  fallback: "authorized workspace default without resource disclosure",
  refresh: "restore only from authorized server facts",
  searchKeys: [
    "manuscript",
    "version",
    "checkRun",
    "issue",
    "transformation",
    "audit",
    "claim",
    "view",
  ],
  ownership: {
    route: "Codex-owned; registered at /projects/$projectId/manuscript",
    container: "Codex-owned",
    ui: "Codex-owned production implementation; pure display contract remains stable",
  },
} as const
