import type { ReactNode } from "react"

import {
  LoadableState,
  MutationError,
  SectionHeader,
  WorkspaceLoadingSkeleton,
} from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"

import type { Loadable, UiErrorViewModel } from "../model"

import "./project-workspace.css"

function RetryAction({ onRetry }: { onRetry: () => void }) {
  return (
    <Button type="button" size="sm" variant="outline" onClick={onRetry}>
      重新加载
    </Button>
  )
}

export function ProjectPanel<T>({
  title,
  description,
  content,
  loadError,
  onRetry,
  actions,
  children,
}: {
  title: string
  description: string
  content: Loadable<T>
  loadError: UiErrorViewModel | null
  onRetry: () => void
  actions?: ReactNode
  children: (data: T) => ReactNode
}) {
  const retry = <RetryAction onRetry={onRetry} />
  let body: ReactNode

  if (content.state === "loading") {
    body = (
      <WorkspaceLoadingSkeleton
        layout="project"
        state="loading"
        title={content.label}
      />
    )
  } else if (content.state === "empty") {
    body = (
      <LoadableState
        state="empty"
        title={`暂无${title}`}
        message={content.message}
      />
    )
  } else if (content.state === "error") {
    body = (
      <LoadableState
        state={content.error.forbidden ? "forbidden" : "error"}
        title={content.error.title}
        message={content.error.message}
        action={content.error.retryable ? retry : undefined}
      />
    )
  } else {
    body = children(content.data)
  }

  return (
    <section className="project-panel" aria-label={title}>
      <SectionHeader
        title={title}
        description={description}
        actions={actions}
      />
      {loadError ? (
        <MutationError
          message={loadError.message}
          code={loadError.code}
          requestId={loadError.requestId}
          retryable={loadError.retryable}
          onRetry={loadError.retryable ? onRetry : undefined}
        />
      ) : null}
      <div className="project-panel__body">{body}</div>
    </section>
  )
}

export function DisabledReason({ children }: { children: ReactNode }) {
  return <p className="project-disabled-reason">{children}</p>
}
