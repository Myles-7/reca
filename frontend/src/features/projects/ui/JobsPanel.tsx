import { ExternalLink, RotateCcw, X } from "lucide-react"

import {
  DegradedNotice,
  JobProgress,
  MutationError,
  PermissionNotice,
  StatusBadge,
} from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"

import type { JobsPanelProps } from "./contracts"
import { DisabledReason, ProjectPanel } from "./ProjectPanel"

export function JobsPanel(props: JobsPanelProps) {
  const streamTone =
    props.streamState === "connected"
      ? "info"
      : props.streamState === "idle"
        ? "neutral"
        : "degraded"

  return (
    <ProjectPanel
      title="Jobs"
      description="任务进度、attempt、错误、结果与 retryability 均来自正式投影。"
      content={props.content}
      loadError={props.loadError}
      onRetry={props.onRetryLoad}
      actions={
        <StatusBadge
          label={`更新流 ${props.streamState}`}
          tone={streamTone}
          title="实时流状态不等同 Job 业务状态"
        />
      }
    >
      {(jobs) => (
        <>
          {props.permissions === null ? (
            <PermissionNotice reason="Job 权限投影未知；重试和取消操作全部保持禁用。" />
          ) : null}
          {props.streamState === "degraded" || props.streamState === "stale" ? (
            <DegradedNotice
              title="Job 更新流已降级"
              message="当前状态可能通过轮询更新；这不是 Job 已失败或已完成的证明。"
            />
          ) : null}
          {props.mutationError ? (
            <MutationError
              message={props.mutationError.message}
              code={props.mutationError.code}
              requestId={props.mutationError.requestId}
            />
          ) : null}
          {jobs.length === 0 ? (
            <p className="project-section-copy">
              当前没有由领域服务创建的 Job。No jobs have been created by M1
              domain services.
            </p>
          ) : (
            <div className="project-job-list">
              {jobs.map((job) => {
                const submitting = props.submittingJobId === job.id
                const canRetry =
                  Boolean(props.permissions?.canRetryJob) &&
                  job.retryable &&
                  !submitting
                const canCancel =
                  Boolean(props.permissions?.canCancelJob) &&
                  job.active &&
                  !submitting
                return (
                  <article key={job.id} className="project-job-row">
                    <div>
                      <div className="project-job-row__title">
                        {job.taskLabel}
                      </div>
                      <div className="project-table__secondary project-code">
                        {job.id}
                      </div>
                    </div>
                    <JobProgress
                      label={job.taskLabel}
                      statusLabel={job.status}
                      tone={job.tone}
                      progress={job.progress}
                      step={job.step}
                    />
                    <div>
                      <span className="project-metadata-label">Attempts</span>
                      <div>
                        {job.retryCount} / {job.maxRetries}
                      </div>
                    </div>
                    <div className="project-job-row__actions">
                      <div className="project-action-row">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          aria-label="Retry job"
                          disabled={!canRetry}
                          onClick={() =>
                            props.onAction({ jobId: job.id, action: "retry" })
                          }
                        >
                          <RotateCcw aria-hidden="true" />
                          重试
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          aria-label="Cancel job"
                          disabled={!canCancel}
                          onClick={() =>
                            props.onAction({ jobId: job.id, action: "cancel" })
                          }
                        >
                          <X aria-hidden="true" />
                          取消
                        </Button>
                        {job.resultUrl ? (
                          <Button asChild size="sm" variant="ghost">
                            <a
                              href={job.resultUrl}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <ExternalLink aria-hidden="true" />
                              结果
                            </a>
                          </Button>
                        ) : null}
                      </div>
                      {submitting ? (
                        <DisabledReason>
                          事件提交中，重复操作已禁用。
                        </DisabledReason>
                      ) : !job.retryable ? (
                        <DisabledReason>
                          服务端未将此 Job 投影为可重试。
                        </DisabledReason>
                      ) : props.permissions === null ? (
                        <DisabledReason>权限未知。</DisabledReason>
                      ) : null}
                    </div>
                    {job.error ? (
                      <div className="project-risk-strip" role="alert">
                        <X aria-hidden="true" />
                        <p>{job.error}</p>
                      </div>
                    ) : null}
                  </article>
                )
              })}
            </div>
          )}
        </>
      )}
    </ProjectPanel>
  )
}
