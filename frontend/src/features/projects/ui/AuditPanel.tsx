import { LockKeyhole } from "lucide-react"

import { SourceBadge, StatusBadge } from "@/components/reca-visual-refresh"

import type { AuditPanelProps } from "./contracts"
import { ProjectPanel } from "./ProjectPanel"

export function AuditPanel(props: AuditPanelProps) {
  return (
    <ProjectPanel
      title="Audit"
      description="只读审计时间线保留 actor、action、target、request ID 与 outcome。"
      content={props.content}
      loadError={props.loadError}
      onRetry={props.onRetry}
      actions={
        <span className="project-readonly-mark">
          <LockKeyhole aria-hidden="true" />
          只读
        </span>
      }
    >
      {(events) =>
        events.length === 0 ? (
          <p className="project-section-copy">当前没有可见审计事件。</p>
        ) : (
          <div className="project-table-wrap">
            <table className="project-table">
              <thead>
                <tr>
                  <th>操作</th>
                  <th>Actor</th>
                  <th>Target</th>
                  <th>Outcome</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>
                      <span className="project-mobile-label">操作</span>
                      <span className="project-table__primary">
                        {event.action}
                      </span>
                      {event.requestId ? (
                        <span className="project-table__secondary project-code">
                          {event.requestId}
                        </span>
                      ) : null}
                    </td>
                    <td>
                      <span className="project-mobile-label">Actor</span>
                      <span>{event.actor}</span>
                    </td>
                    <td>
                      <span className="project-mobile-label">Target</span>
                      <span>{event.target}</span>
                      {event.summary ? (
                        <span className="project-table__secondary">
                          {event.summary}
                        </span>
                      ) : null}
                    </td>
                    <td>
                      <span className="project-mobile-label">Outcome</span>
                      <StatusBadge label={event.outcome} tone={event.tone} />
                    </td>
                    <td>
                      <span className="project-mobile-label">时间</span>
                      <span>{event.occurredAt}</span>
                      <SourceBadge label="服务端审计记录" kind="verified" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </ProjectPanel>
  )
}
