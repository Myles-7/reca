import type { ReactNode } from "react"

import { normalizeVisualTone, StatusBadge } from "./semantic"

export function JobProgress({
  label,
  statusLabel,
  tone = "unknown",
  progress,
  step,
}: {
  label: string
  statusLabel: string
  tone?: string
  progress: number | null
  step?: string | null
}) {
  const safeProgress =
    progress === null ? null : Math.max(0, Math.min(100, progress))
  const safeTone = normalizeVisualTone(tone)
  return (
    <div className={`reca-job-progress reca-tone-${safeTone}`}>
      <div className="reca-job-progress__header">
        <span className="reca-job-progress__label">{label}</span>
        <StatusBadge label={statusLabel} tone={safeTone} />
      </div>
      <div
        className="reca-job-progress__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={safeProgress ?? undefined}
        aria-valuetext={safeProgress === null ? "进度未知" : `${safeProgress}%`}
      >
        {safeProgress === null ? null : (
          <div
            className="reca-job-progress__fill"
            style={{ width: `${safeProgress}%` }}
          />
        )}
      </div>
      <div className="reca-job-progress__meta">
        <span>{step ?? "等待服务端步骤信息"}</span>
        <span>{safeProgress === null ? "未知" : `${safeProgress}%`}</span>
      </div>
    </div>
  )
}

export type MetadataItem = {
  label: string
  value: ReactNode
  mono?: boolean
}

export function MetadataList({ items }: { items: readonly MetadataItem[] }) {
  return (
    <dl className="reca-metadata-list">
      {items.map((item) => (
        <div key={item.label} className="reca-metadata-list__row">
          <dt>{item.label}</dt>
          <dd className={item.mono ? "reca-metadata-list__mono" : undefined}>
            {item.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function InspectorSection({
  title,
  accessory,
  children,
}: {
  title: string
  accessory?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="reca-inspector-section">
      <div className="reca-inspector-section__header">
        <h3 className="reca-inspector-section__title">{title}</h3>
        {accessory}
      </div>
      <div className="reca-inspector-section__content">{children}</div>
    </section>
  )
}
