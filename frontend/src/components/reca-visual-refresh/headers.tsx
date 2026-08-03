import type { ReactNode } from "react"

export function WorkspaceHeader({
  title,
  context,
  metadata,
  actions,
}: {
  title: string
  context?: string
  metadata?: ReactNode
  actions?: ReactNode
}) {
  return (
    <header className="reca-workspace-header">
      <div className="reca-workspace-header__identity">
        {context ? (
          <div className="reca-workspace-header__context">{context}</div>
        ) : null}
        <h1 className="reca-workspace-header__title">{title}</h1>
      </div>
      {metadata ? (
        <div className="reca-workspace-header__meta">{metadata}</div>
      ) : null}
      {actions ? (
        <div className="reca-workspace-header__actions">{actions}</div>
      ) : null}
    </header>
  )
}

export function SectionHeader({
  title,
  description,
  actions,
}: {
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <header className="reca-section-header">
      <div className="reca-section-header__identity">
        <h2 className="reca-section-header__title">{title}</h2>
        {description ? (
          <p className="reca-section-header__description">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="reca-section-header__actions">{actions}</div>
      ) : null}
    </header>
  )
}

export function PaneHeader({
  title,
  subtitle,
  actions,
}: {
  title: string
  subtitle?: string
  actions?: ReactNode
}) {
  return (
    <header className="reca-pane-header">
      <div className="reca-pane-header__identity">
        <h3 className="reca-pane-header__title">{title}</h3>
        {subtitle ? (
          <div className="reca-pane-header__subtitle">{subtitle}</div>
        ) : null}
      </div>
      {actions ? (
        <div className="reca-pane-header__actions">{actions}</div>
      ) : null}
    </header>
  )
}
