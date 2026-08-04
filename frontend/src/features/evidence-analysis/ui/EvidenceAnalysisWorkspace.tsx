import {
  AlertTriangle,
  BookOpenCheck,
  CircleDot,
  FlaskConical,
  Library,
  RefreshCw,
  Scale,
  SearchX,
  Users,
} from "lucide-react"

import { MutationError, StatusBadge } from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"

import type { EvidenceAnalysisWorkspaceProps } from "./contracts"
import "./evidence-analysis-workspace.css"

const labels = {
  CONSENSUS: "Consensus",
  CONTROVERSY: "Controversy",
  EVIDENCE_GAP: "Current-set evidence gap",
  COUNTEREXAMPLE: "Counterexample",
  METHOD_DIFFERENCE: "Method difference",
  SAMPLE_DIFFERENCE: "Sample difference",
  MISSING_LITERATURE: "Literature to seek",
} as const

const itemIcons = {
  CONSENSUS: CircleDot,
  CONTROVERSY: Scale,
  EVIDENCE_GAP: SearchX,
  COUNTEREXAMPLE: AlertTriangle,
  METHOD_DIFFERENCE: FlaskConical,
  SAMPLE_DIFFERENCE: Users,
  MISSING_LITERATURE: Library,
} as const

export function EvidenceAnalysisWorkspace(
  props: EvidenceAnalysisWorkspaceProps,
) {
  if (props.content.state === "loading") {
    return (
      <section className="m3-analysis-workspace" aria-busy="true">
        <h1>Current Evidence Analysis</h1>
        <div className="m3-analysis-skeleton" />
      </section>
    )
  }
  if (props.content.state === "error") {
    return (
      <section className="m3-analysis-workspace">
        <h1>Current Evidence Analysis</h1>
        <MutationError {...props.content.error} onRetry={props.onRetry} />
      </section>
    )
  }
  if (props.content.state === "empty") {
    return (
      <section className="m3-analysis-workspace m3-analysis-empty">
        <BookOpenCheck aria-hidden="true" />
        <h1>Current Evidence Analysis</h1>
        <p>{props.content.message}</p>
      </section>
    )
  }
  const data = props.content.data
  return (
    <section
      className="m3-analysis-workspace reca-visual-refresh"
      data-od-id="m3-evidence-analysis-workspace"
    >
      <header className="m3-analysis-header">
        <div>
          <h1>Current Evidence Analysis</h1>
          <p>{data.scopeStatement}</p>
        </div>
        <StatusBadge label={data.status} tone={data.tone} />
      </header>
      {!data.knownStatus || !data.permissionsKnown ? (
        <p className="m3-analysis-notice" role="status">
          <AlertTriangle aria-hidden="true" /> Unknown status or permissions;
          generation actions remain disabled.
        </p>
      ) : null}
      {props.mutationError ? <MutationError {...props.mutationError} /> : null}
      <dl className="m3-analysis-scope">
        <div>
          <dt>Included literature</dt>
          <dd>{data.includedLiteratureIds.length}</dd>
        </div>
        <div>
          <dt>Summary items</dt>
          <dd>{data.items.length}</dd>
        </div>
        <div>
          <dt>Counterexamples</dt>
          <dd>
            {data.items.filter((item) => item.kind === "COUNTEREXAMPLE").length}
          </dd>
        </div>
        <div>
          <dt>Current-set limitations</dt>
          <dd>{data.limitations.length + data.missingInformation.length}</dd>
        </div>
      </dl>
      <div className="m3-analysis-grid">
        {data.items.map((item, index) => {
          const ItemIcon = itemIcons[item.kind]
          return (
            <article
              key={`${item.kind}-${index}`}
              data-kind={item.kind}
              className="m3-analysis-item"
            >
              <header>
                <div className="m3-analysis-item__title">
                  <ItemIcon aria-hidden="true" />
                  <strong>{labels[item.kind]}</strong>
                </div>
                <StatusBadge label={item.strength} tone="evidence" />
              </header>
              <p className="m3-analysis-item__claim">{item.claim}</p>
              <dl>
                <div>
                  <dt>Literature sources</dt>
                  <dd>
                    {item.sources.literatureRecordIds.join(", ") || "None"}
                  </dd>
                </div>
                <div>
                  <dt>Contradicting sources</dt>
                  <dd>
                    {item.sources.contradictingLiteratureRecordIds.join(", ") ||
                      "None"}
                  </dd>
                </div>
                <div>
                  <dt>Evidence spans</dt>
                  <dd>{item.sources.evidenceSpanIds.join(", ") || "None"}</dd>
                </div>
              </dl>
              {item.limitations.length ? (
                <div className="m3-analysis-item__limitations">
                  <strong>Limits</strong>
                  <ul>
                    {item.limitations.map((limitation) => (
                      <li key={limitation}>{limitation}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </article>
          )
        })}
      </div>
      <section className="m3-analysis-limitations">
        <h2>Limitations of the current literature set</h2>
        <ul>
          {[...data.limitations, ...data.missingInformation].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
      <div className="m3-analysis-actions">
        <Button
          type="button"
          variant="outline"
          disabled={
            !data.canRetry ||
            data.jobId === null ||
            props.pendingAction !== null
          }
          title={
            data.canRetry ? undefined : "The server did not allow Job retry."
          }
          onClick={() => {
            if (data.jobId)
              props.onEvent({
                action: "retry-job",
                input: { jobId: data.jobId },
              })
          }}
        >
          <RefreshCw aria-hidden="true" /> Retry job
        </Button>
        <Button
          type="button"
          disabled
          title="A research-question version and formal topic read projection are required before production generation can be enabled."
        >
          Generate 3 topics
        </Button>
      </div>
    </section>
  )
}
