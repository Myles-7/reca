import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  Clock3,
  Database,
  FileSearch,
  ShieldAlert,
} from "lucide-react"

import { MutationError, StatusBadge } from "@/components/reca-visual-refresh"

import type { TopicCandidatesWorkspaceProps } from "./contracts"
import "./topic-candidates-workspace.css"

export function TopicCandidatesWorkspace(props: TopicCandidatesWorkspaceProps) {
  if (props.content.state === "loading") {
    return (
      <section className="m3-topics-workspace" aria-busy="true">
        <h1>Topic Candidates</h1>
        <div className="m3-topics-skeleton" />
      </section>
    )
  }
  if (props.content.state === "error") {
    return (
      <section className="m3-topics-workspace">
        <h1>Topic Candidates</h1>
        <MutationError {...props.content.error} onRetry={props.onRetry} />
      </section>
    )
  }
  if (props.content.state === "empty") {
    return (
      <section className="m3-topics-workspace m3-topics-empty">
        <FileSearch aria-hidden="true" />
        <h1>Topic Candidates</h1>
        <p>{props.content.message}</p>
      </section>
    )
  }
  const data = props.content.data
  if (
    !data.knownStatus ||
    !data.exactlyThree ||
    !data.sourcesValid ||
    data.candidates.some((candidate) => !candidate.knownStatus)
  ) {
    return (
      <section className="m3-topics-workspace m3-topics-failure" role="alert">
        <AlertTriangle aria-hidden="true" />
        <h1>Topic candidates unavailable</h1>
        <p>
          {data.failureReason ??
            "The server projection failed strict status, count, or source validation."}
        </p>
        <p>No candidates were padded, truncated, or adopted by the browser.</p>
      </section>
    )
  }
  return (
    <section
      className="m3-topics-workspace reca-visual-refresh"
      data-od-id="m3-topic-candidates-workspace"
    >
      <header className="m3-topics-header">
        <div>
          <h1>Topic Candidates</h1>
          <p>
            Exactly three server-projected candidates from the current evidence
            summary.
          </p>
        </div>
        <StatusBadge label={data.status} tone={data.tone} />
      </header>
      {props.mutationError ? <MutationError {...props.mutationError} /> : null}
      <div className="m3-topics-summary" role="status">
        <span>
          <strong>3</strong> sourced candidates
        </span>
        <span>
          <strong>
            {data.candidates.flatMap((candidate) => candidate.sources).length}
          </strong>{" "}
          source links
        </span>
        <span>Server order preserved</span>
      </div>
      <div className="m3-topic-list">
        {data.candidates.map((candidate) => (
          <article key={candidate.id} className="m3-topic-candidate">
            <header>
              <span>{candidate.order}</span>
              <div>
                <h2>{candidate.question}</h2>
                <p>
                  {candidate.researchObject ?? "Research object unavailable"}
                </p>
              </div>
            </header>
            <dl>
              <div>
                <dt>Literature basis</dt>
                <dd>{candidate.literatureBasis ?? "Unavailable"}</dd>
              </div>
              <div>
                <dt>Possible innovation</dt>
                <dd>{candidate.possibleInnovation ?? "Unavailable"}</dd>
              </div>
              <div>
                <dt>Recommended method</dt>
                <dd>{candidate.recommendedMethod ?? "Unavailable"}</dd>
              </div>
              <div>
                <dt>
                  <Database aria-hidden="true" /> Data availability
                </dt>
                <dd>{candidate.dataAvailability ?? "UNKNOWN"}</dd>
              </div>
              <div>
                <dt>
                  <BarChart3 aria-hidden="true" /> Method difficulty
                </dt>
                <dd>{candidate.methodDifficulty ?? "UNKNOWN"}</dd>
              </div>
              <div>
                <dt>
                  <Clock3 aria-hidden="true" /> Time feasibility
                </dt>
                <dd>{candidate.timeFeasibility ?? "UNKNOWN"}</dd>
              </div>
              <div>
                <dt>
                  <ShieldAlert aria-hidden="true" /> Ethical risk
                </dt>
                <dd>{candidate.ethicalRisk ?? "UNKNOWN"}</dd>
              </div>
            </dl>
            <section className="m3-topic-sources">
              <h3>Sources</h3>
              <ul>
                {candidate.sources.map((source, index) => (
                  <li
                    key={`${source.literatureRecordId}-${source.evidenceSpanId}-${index}`}
                  >
                    <BookOpen aria-hidden="true" />
                    <button
                      type="button"
                      onClick={() =>
                        props.onEvent({
                          action: "open-source",
                          input: {
                            candidateId: candidate.id,
                            literatureRecordId: source.literatureRecordId,
                            evidenceSpanId: source.evidenceSpanId,
                          },
                        })
                      }
                    >
                      {source.evidenceSpanId ?? source.literatureRecordId}
                    </button>
                    <span>{source.relationType}</span>
                  </li>
                ))}
              </ul>
            </section>
            <section className="m3-topic-risks">
              <h3>Major risks</h3>
              <ul>
                {candidate.majorRisks.map((risk) => (
                  <li key={risk}>{risk}</li>
                ))}
              </ul>
              {candidate.limitations.length ? (
                <ul className="m3-topic-limitations">
                  {candidate.limitations.map((limitation) => (
                    <li key={limitation}>{limitation}</li>
                  ))}
                </ul>
              ) : null}
            </section>
          </article>
        ))}
      </div>
    </section>
  )
}
