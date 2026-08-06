import type { EvidenceWorkspaceView } from "./model"

export const EVIDENCE_WORKSPACE_PATH = "/projects/$projectId/evidence"

export type EvidenceWorkspaceRouteSearch = {
  claim?: string
  node?: string
  link?: string
  audit?: string
  export?: string
  package?: string
  view?: EvidenceWorkspaceView
}

const views = new Set<EvidenceWorkspaceView>([
  "graph",
  "claims",
  "audits",
  "exports",
])

const safeId = (value: unknown) =>
  typeof value === "string" && value.length > 0 && value.length <= 255
    ? value
    : undefined

export function parseEvidenceWorkspaceSearch(
  value: Readonly<Record<string, unknown>>,
): EvidenceWorkspaceRouteSearch {
  const rawView = value.view
  return {
    claim: safeId(value.claim),
    node: safeId(value.node),
    link: safeId(value.link),
    audit: safeId(value.audit),
    export: safeId(value.export),
    package: safeId(value.package),
    view:
      typeof rawView === "string" && views.has(rawView as EvidenceWorkspaceView)
        ? (rawView as EvidenceWorkspaceView)
        : "graph",
  }
}

export function evidenceWorkspaceHref(
  projectId: string,
  search: EvidenceWorkspaceRouteSearch = {},
) {
  const query = new URLSearchParams()
  for (const key of [
    "claim",
    "node",
    "link",
    "audit",
    "export",
    "package",
  ] as const) {
    const value = search[key]
    if (value) query.set(key, value)
  }
  if (search.view && search.view !== "graph") query.set("view", search.view)
  const suffix = query.toString()
  return `/projects/${encodeURIComponent(projectId)}/evidence${suffix ? `?${suffix}` : ""}`
}
