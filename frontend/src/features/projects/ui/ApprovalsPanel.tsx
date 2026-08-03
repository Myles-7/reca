import { Check, Clock3, Trash2, X } from "lucide-react"

import {
  MutationError,
  SourceBadge,
  StatusBadge,
} from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"

import type { ApprovalsPanelProps } from "./contracts"
import { DisabledReason, ProjectPanel } from "./ProjectPanel"

export function ApprovalsPanel(props: ApprovalsPanelProps) {
  return (
    <ProjectPanel
      title="Approvals"
      description="审批目标、payload hash、请求者、有效期与 allowedActions 保持同屏可复核。"
      content={props.content}
      loadError={props.loadError}
      onRetry={props.onRetry}
      actions={<SourceBadge label="正式审批记录" kind="approval" />}
    >
      {(approvals) => (
        <>
          <p className="project-section-copy">
            审批只能由所属领域服务创建；下列操作仅发出意图，不自动改变审批状态。
          </p>
          {props.mutationError ? (
            <MutationError
              message={props.mutationError.message}
              code={props.mutationError.code}
              requestId={props.mutationError.requestId}
            />
          ) : null}
          {approvals.length === 0 ? (
            <p className="project-section-copy">
              当前没有需要处理的审批请求。No approval requests require
              attention.
            </p>
          ) : (
            <div className="project-approval-list">
              {approvals.map((approval) => {
                const submitting = props.submittingApprovalId === approval.id
                const canApprove =
                  approval.allowedActions.has("approval.approve") && !submitting
                const canReject =
                  approval.allowedActions.has("approval.reject") && !submitting
                const canCancel =
                  approval.allowedActions.has("approval.cancel") && !submitting
                return (
                  <article key={approval.id} className="project-approval-row">
                    <div>
                      <div className="project-approval-row__title">
                        {approval.type}
                      </div>
                      <div className="project-table__secondary">
                        {approval.target}
                      </div>
                      <div className="project-table__secondary project-code">
                        {approval.id}
                      </div>
                    </div>
                    <div>
                      <StatusBadge
                        label={approval.status}
                        tone={approval.tone}
                      />
                      <div className="project-table__secondary">
                        请求者：{approval.requester}
                      </div>
                    </div>
                    <div>
                      <span className="project-metadata-label">
                        请求 / 到期
                      </span>
                      <div>{approval.requestedAt}</div>
                      <div className="project-table__secondary">
                        {approval.expiresAt ?? "未提供到期时间"}
                      </div>
                    </div>
                    <div className="project-approval-row__actions">
                      <div className="project-action-row">
                        <Button
                          type="button"
                          size="sm"
                          aria-label="Approve"
                          disabled={!canApprove}
                          onClick={() =>
                            props.onAction({
                              approvalId: approval.id,
                              action: "approve",
                              reason: null,
                            })
                          }
                        >
                          <Check aria-hidden="true" />
                          批准
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          aria-label="Reject"
                          disabled={!canReject}
                          onClick={() =>
                            props.onAction({
                              approvalId: approval.id,
                              action: "reject",
                              reason: "Rejected from project workspace",
                            })
                          }
                        >
                          <X aria-hidden="true" />
                          拒绝
                        </Button>
                        <Button
                          type="button"
                          size="icon-sm"
                          variant="ghost"
                          aria-label="Cancel approval"
                          disabled={!canCancel}
                          onClick={() =>
                            props.onAction({
                              approvalId: approval.id,
                              action: "cancel",
                              reason: null,
                            })
                          }
                        >
                          <Trash2 aria-hidden="true" />
                        </Button>
                      </div>
                      {submitting ? (
                        <DisabledReason>
                          审批意图提交中，状态尚未改变。
                        </DisabledReason>
                      ) : !canApprove && !canReject && !canCancel ? (
                        <DisabledReason>
                          服务端未提供可用 allowedActions。
                        </DisabledReason>
                      ) : null}
                    </div>
                    <div className="project-approval-hash">
                      <span className="project-metadata-label">
                        Payload hash
                      </span>
                      <div className="project-code">{approval.payloadHash}</div>
                    </div>
                    {approval.stale ? (
                      <div className="project-risk-strip" role="status">
                        <Clock3 aria-hidden="true" />
                        <p>
                          该审批已 stale；请复核目标版本与 payload hash
                          后再操作。
                        </p>
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
