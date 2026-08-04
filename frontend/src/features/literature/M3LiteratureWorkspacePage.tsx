import { BarChart3, Grid3X3, Lightbulb } from "lucide-react"
import { useState } from "react"

import type { LiteratureMatrixQuery } from "@/api/adapter"
import { Button } from "@/components/ui/button"
import { EvidenceAnalysisContainer } from "@/features/evidence-analysis/containers/EvidenceAnalysisContainer"
import { EvidenceAnalysisWorkspace } from "@/features/evidence-analysis/ui/EvidenceAnalysisWorkspace"
import { EvidenceMatrixContainer } from "@/features/evidence-matrix/containers/EvidenceMatrixContainer"
import { EvidenceMatrixWorkspace } from "@/features/evidence-matrix/ui/EvidenceMatrixWorkspace"
import { TopicCandidatesContainer } from "@/features/topic-candidates/containers/TopicCandidatesContainer"
import { TopicCandidatesWorkspace } from "@/features/topic-candidates/ui/TopicCandidatesWorkspace"

import type { M3LiteratureSearch, M3LiteratureView } from "./m3-route-contract"
import "./m3-literature-workspace.css"

export function M3LiteratureWorkspacePage({
  projectId,
  search,
  onSearchChange,
}: {
  projectId: string
  search: M3LiteratureSearch
  onSearchChange: (next: Partial<M3LiteratureSearch>) => void
}) {
  const [matrixQuery, setMatrixQuery] = useState<LiteratureMatrixQuery>({
    page: 1,
    page_size: 20,
  })
  const activeView = search.view ?? "matrix"
  const setView = (view: M3LiteratureView) => onSearchChange({ view })
  return (
    <main className="m3-literature-page">
      <nav
        className="m3-literature-tabs"
        role="tablist"
        aria-label="Literature evidence views"
      >
        <Button
          type="button"
          role="tab"
          variant={activeView === "matrix" ? "default" : "ghost"}
          aria-selected={activeView === "matrix"}
          onClick={() => setView("matrix")}
        >
          <Grid3X3 aria-hidden="true" /> Matrix
        </Button>
        <Button
          type="button"
          role="tab"
          variant={activeView === "analysis" ? "default" : "ghost"}
          aria-selected={activeView === "analysis"}
          onClick={() => setView("analysis")}
        >
          <BarChart3 aria-hidden="true" /> Analysis
        </Button>
        <Button
          type="button"
          role="tab"
          variant={activeView === "topics" ? "default" : "ghost"}
          aria-selected={activeView === "topics"}
          onClick={() => setView("topics")}
        >
          <Lightbulb aria-hidden="true" /> Topics
        </Button>
      </nav>
      {activeView === "matrix" ? (
        <EvidenceMatrixContainer
          projectId={projectId}
          documentId={search.documentId}
          extractionId={search.extractionId}
          fieldId={search.fieldId}
          evidenceSpanId={search.evidenceSpanId}
          matrixQuery={matrixQuery}
          View={EvidenceMatrixWorkspace}
          onNavigate={(input) =>
            onSearchChange({
              view: "matrix",
              documentId: input.documentId,
              extractionId: input.extractionId ?? undefined,
              fieldId: input.fieldId ?? undefined,
              evidenceSpanId: input.evidenceSpanId ?? undefined,
            })
          }
          onQueryChange={(event) => {
            if (event.action === "filter") {
              setMatrixQuery((value) => ({
                ...value,
                page: 1,
                included_only: event.input.includedOnly,
                field_codes: event.input.fieldCodes.length
                  ? event.input.fieldCodes
                  : null,
              }))
            } else {
              setMatrixQuery((value) => ({
                ...value,
                page: 1,
                sort: event.input.sort,
                order: event.input.order,
              }))
            }
          }}
        />
      ) : activeView === "analysis" ? (
        <EvidenceAnalysisContainer
          projectId={projectId}
          summaryId={search.summaryId}
          View={EvidenceAnalysisWorkspace}
        />
      ) : (
        <TopicCandidatesContainer
          projectId={projectId}
          runId={search.topicRunId}
          View={TopicCandidatesWorkspace}
          onOpenSource={(source) =>
            onSearchChange({
              view: "matrix",
              evidenceSpanId: source.evidenceSpanId ?? undefined,
            })
          }
        />
      )}
    </main>
  )
}
