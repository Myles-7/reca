import { Clock3 } from "lucide-react"

import { DegradedNotice, StatusBadge } from "@/components/reca-visual-refresh"

import type { OverviewPanelProps } from "./contracts"
import { ProjectPanel } from "./ProjectPanel"

export function OverviewPanel(props: OverviewPanelProps) {
  return (
    <ProjectPanel
      title="项目概览"
      description="项目基础计数、当前阶段与服务端投影的能力可用性。"
      content={props.content}
      loadError={props.loadError}
      onRetry={props.onRetry}
    >
      {(overview) => (
        <>
          <div className="project-inline-meta">
            <StatusBadge label={`阶段 ${overview.stage}`} tone="info" />
            <span>基础计数由正式服务端结果提供，不可用值不会显示为 0。</span>
          </div>

          <dl className="project-counts">
            {overview.foundationCounts.map((item) => (
              <div key={item.label} className="project-counts__item">
                <dt>{item.label}</dt>
                <dd>
                  {item.value ?? "—"}
                  {item.value === null ? <small> 未投影</small> : null}
                </dd>
              </div>
            ))}
          </dl>

          <section aria-labelledby="project-capabilities-title">
            <h3
              id="project-capabilities-title"
              className="project-section-label"
            >
              能力可用性
            </h3>
            <p className="project-section-copy">
              Availability 是能力投影，不代表数据质量或任务成功。
            </p>
            <div className="project-capability-list">
              {overview.capabilities.map((capability) => {
                const unavailable = capability.availability === "NOT_AVAILABLE"
                return (
                  <div key={capability.key} className="project-capability-row">
                    <span className="project-capability-row__label">
                      {capability.label}
                    </span>
                    <StatusBadge
                      label={
                        capability.availability === "AVAILABLE"
                          ? "可用"
                          : capability.availability === "DEGRADED"
                            ? "降级可用"
                            : "不可用 · Not available"
                      }
                      tone={unavailable ? "neutral" : capability.tone}
                    />
                    <span className="project-table__secondary">
                      {capability.value === null
                        ? unavailable
                          ? "无入口"
                          : "数值未知"
                        : `${capability.value} 项`}
                    </span>
                  </div>
                )
              })}
            </div>
          </section>

          {overview.pendingActionCount > 0 ? (
            <div className="project-risk-strip" role="status">
              <Clock3 aria-hidden="true" />
              <p>
                当前有 {overview.pendingActionCount}{" "}
                项待处理操作；待处理不表示已批准或已完成。
              </p>
            </div>
          ) : null}

          {overview.capabilities.some(
            (capability) => capability.availability === "DEGRADED",
          ) ? (
            <DegradedNotice
              title="部分能力处于降级状态"
              message="请按各能力的来源和限制复核结果，不要把降级可用视为正式成功。"
            />
          ) : null}
        </>
      )}
    </ProjectPanel>
  )
}
