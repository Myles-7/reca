export const m3LiteratureViews = ["matrix", "analysis", "topics"] as const
export type M3LiteratureView = (typeof m3LiteratureViews)[number]

export type M3LiteratureSearch = {
  view?: M3LiteratureView
  documentId?: string
  extractionId?: string
  fieldId?: string
  evidenceSpanId?: string
  summaryId?: string
  topicRunId?: string
}

function optionalId(value: unknown) {
  return typeof value === "string" && value.trim() ? value : undefined
}

export function parseM3LiteratureSearch(
  search: Record<string, unknown>,
): M3LiteratureSearch {
  const view = m3LiteratureViews.includes(search.view as M3LiteratureView)
    ? (search.view as M3LiteratureView)
    : undefined
  return {
    view,
    documentId: optionalId(search.documentId),
    extractionId: optionalId(search.extractionId),
    fieldId: optionalId(search.fieldId),
    evidenceSpanId: optionalId(search.evidenceSpanId),
    summaryId: optionalId(search.summaryId),
    topicRunId: optionalId(search.topicRunId),
  }
}
