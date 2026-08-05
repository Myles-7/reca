import { RefreshCw, Upload } from "lucide-react"
import { type ChangeEvent, useState } from "react"

import {
  EmptyState,
  LoadableState,
  MutationError,
  PaneHeader,
  StatusBadge,
  WorkspaceHeader,
} from "@/components/reca-visual-refresh"

import type { ManuscriptWorkspaceViewModel } from "../model"
import type {
  ManuscriptWorkspaceEvent,
  ManuscriptWorkspaceProps,
} from "./contracts"

function stateLabel(data: ManuscriptWorkspaceViewModel): string {
  if (!data.discoveryKnown || !data.permissionsKnown) return "Unknown"
  if (!data.manuscript) return "No manuscript"
  return data.discoveryState
}

export function ManuscriptWorkspace({
  content,
  pendingAction,
  mutationError,
  onRetry,
  onEvent,
}: ManuscriptWorkspaceProps) {
  const [file, setFile] = useState<File | null>(null)
  const data = content.state === "ready" ? content.data : null
  const uploadAllowed = Boolean(data?.capabilities.uploadManuscript.allowed)

  const upload = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.files?.[0] ?? null
    setFile(next)
    if (next && uploadAllowed && pendingAction !== "upload-manuscript") {
      onEvent({
        action: "upload-manuscript",
        input: { file: next, title: next.name },
      })
    }
  }

  const emit = (event: ManuscriptWorkspaceEvent) => {
    if (pendingAction === event.action) return
    onEvent(event)
  }

  const loadableState = content.state
  return (
    <main className="reca-workspace" aria-label="Manuscript workspace">
      <WorkspaceHeader
        title={data?.manuscript?.title ?? "Manuscript review"}
        context={data ? `Project ${data.projectId}` : "Project manuscript"}
        actions={
          <button
            type="button"
            className="reca-button reca-button--secondary"
            onClick={() => emit({ action: "refresh" })}
          >
            <RefreshCw aria-hidden="true" /> Refresh
          </button>
        }
      />
      <LoadableState
        state={loadableState}
        title="Manuscript workspace"
        message={content.state === "empty" ? content.message : undefined}
        action={
          content.state === "error" ? (
            <button
              type="button"
              className="reca-button reca-button--secondary"
              onClick={onRetry}
            >
              Retry
            </button>
          ) : undefined
        }
      >
        {data ? (
          <>
            <section className="reca-pane" aria-labelledby="manuscript-status">
              <PaneHeader
                title="Manuscript status"
                subtitle="Review state and server facts"
              />
              <div className="reca-pane__body">
                <StatusBadge
                  label={stateLabel(data)}
                  tone={
                    data.discoveryKnown && data.permissionsKnown
                      ? "info"
                      : "unknown"
                  }
                />
                {data.selectedVersion ? (
                  <p>
                    Version {data.selectedVersion.versionNumber} ·{" "}
                    {data.selectedVersion.sourceHash}
                  </p>
                ) : null}
                {data.job ? (
                  <p>
                    Job {data.job.status} · {data.job.progress}%
                  </p>
                ) : null}
                {data.degraded ? (
                  <p role="status">
                    Some checks are degraded or low confidence.
                  </p>
                ) : null}
              </div>
            </section>
            {!data.manuscript ? (
              <section className="reca-pane">
                <EmptyState
                  title="No manuscript"
                  message="Upload a DOCX to begin review."
                />
                <label className="reca-button reca-button--primary">
                  <Upload aria-hidden="true" /> Upload DOCX
                  <input
                    type="file"
                    accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={upload}
                    disabled={
                      !uploadAllowed || pendingAction === "upload-manuscript"
                    }
                    hidden
                  />
                </label>
                {file ? <p>{file.name}</p> : null}
              </section>
            ) : (
              <section
                className="reca-pane"
                aria-labelledby="manuscript-actions"
              >
                <PaneHeader title="Review actions" />
                <div className="reca-pane__body">
                  <button
                    type="button"
                    className="reca-button reca-button--primary"
                    disabled={
                      !data.capabilities.startCheck.allowed ||
                      pendingAction === "start-check" ||
                      !data.selectedVersion
                    }
                    onClick={() =>
                      data.selectedVersion &&
                      emit({
                        action: "start-check",
                        input: {
                          versionId: data.selectedVersion.id,
                          checks: data.checkDefinitions
                            .filter((item) => item.allowed)
                            .map((item) => item.value),
                        },
                      })
                    }
                  >
                    Run checks
                  </button>
                  <p>
                    {data.issues.length} issue(s) ·{" "}
                    {data.claim
                      ? `Claim ${data.claim.status}`
                      : "No claim selected"}
                  </p>
                </div>
              </section>
            )}
            {mutationError ? (
              <MutationError
                message={mutationError.message}
                code={mutationError.code}
                retryable={mutationError.retryable}
                onRetry={onRetry}
              />
            ) : null}
          </>
        ) : null}
      </LoadableState>
    </main>
  )
}
