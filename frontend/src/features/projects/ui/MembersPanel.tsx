import { ShieldCheck, Trash2 } from "lucide-react"
import { type FormEvent, useRef, useState } from "react"

import {
  MutationError,
  PermissionNotice,
  StatusBadge,
} from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import type { MemberRoleOption, MemberViewModel } from "../model"
import type { MembersPanelProps } from "./contracts"
import { DisabledReason, ProjectPanel } from "./ProjectPanel"

const roleOptions: MemberRoleOption[] = ["EDITOR", "REVIEWER", "VIEWER"]

export function MembersPanel(props: MembersPanelProps) {
  const [role, setRole] = useState<MemberRoleOption>("VIEWER")
  const [transferTarget, setTransferTarget] = useState<MemberViewModel | null>(
    null,
  )
  const [previousOwnerRole, setPreviousOwnerRole] =
    useState<MemberRoleOption>("EDITOR")
  const transferTriggerRef = useRef<HTMLButtonElement | null>(null)

  function closeTransfer() {
    setTransferTarget(null)
    window.setTimeout(() => transferTriggerRef.current?.focus(), 0)
  }

  function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    props.onAddMember({
      userId: String(form.get("user_id") ?? "").trim(),
      role,
    })
  }

  function transferOwnership(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!transferTarget) return
    const form = new FormData(event.currentTarget)
    props.onTransferOwnership({
      memberId: transferTarget.id,
      previousOwnerRole,
      reason: String(form.get("reason") ?? "").trim(),
    })
    closeTransfer()
  }

  return (
    <ProjectPanel
      title="项目成员"
      description="密集成员表保留所有权、当前用户与高风险成员变更的明确层级。"
      content={props.content}
      loadError={props.loadError}
      onRetry={props.onRetry}
    >
      {({ members, permissions }) => (
        <>
          {permissions.canManageMembers ? (
            <form className="project-inline-form" onSubmit={add}>
              <div className="project-field">
                <label htmlFor="member-user-id">用户 ID</label>
                <Input
                  id="member-user-id"
                  name="user_id"
                  aria-label="User ID"
                  required
                  disabled={!permissions.canManageMembers || props.submitting}
                  placeholder="输入正式用户 ID"
                />
              </div>
              <div className="project-field project-field--compact">
                <label htmlFor="member-role">角色</label>
                <Select
                  value={role}
                  disabled={!permissions.canManageMembers || props.submitting}
                  onValueChange={(value) => setRole(value as MemberRoleOption)}
                >
                  <SelectTrigger id="member-role" aria-label="Member role">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {roleOptions.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                type="submit"
                aria-label="Add member"
                disabled={!permissions.canManageMembers || props.submitting}
              >
                {props.submitting ? "正在提交" : "添加成员"}
              </Button>
            </form>
          ) : null}

          {!permissions.canManageMembers ? (
            <PermissionNotice reason="当前权限不允许管理项目成员；角色、移除和所有权转移均保持禁用。" />
          ) : null}
          {props.mutationError ? (
            <MutationError
              message={props.mutationError.message}
              code={props.mutationError.code}
              requestId={props.mutationError.requestId}
            />
          ) : null}

          {members.length === 0 ? (
            <p className="project-section-copy">当前项目没有可见成员。</p>
          ) : (
            <div className="project-table-wrap">
              <table className="project-table">
                <thead>
                  <tr>
                    <th className="project-col-member">成员</th>
                    <th className="project-col-role">角色</th>
                    <th className="project-col-date">加入时间</th>
                    <th className="project-col-actions">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((member) => {
                    const writable =
                      permissions.canManageMembers &&
                      !member.isOwner &&
                      !member.removed &&
                      !props.submitting
                    return (
                      <tr key={member.id}>
                        <td>
                          <span className="project-mobile-label">成员</span>
                          <span className="project-table__primary">
                            {member.displayName}
                          </span>
                          <span className="project-table__secondary">
                            {member.email}
                          </span>
                          <span className="project-inline-meta">
                            {member.isCurrentUser ? (
                              <StatusBadge label="当前用户" tone="info" />
                            ) : null}
                            {member.isOwner ? (
                              <StatusBadge label="所有者" tone="approval" />
                            ) : null}
                            {member.removed ? (
                              <StatusBadge label="已移除" tone="danger" />
                            ) : null}
                          </span>
                        </td>
                        <td>
                          <span className="project-mobile-label">角色</span>
                          {writable ? (
                            <Select
                              value={member.role}
                              onValueChange={(value) =>
                                props.onChangeRole({
                                  memberId: member.id,
                                  role: value as MemberRoleOption,
                                })
                              }
                            >
                              <SelectTrigger
                                size="sm"
                                aria-label={`Role for ${member.displayName}`}
                              >
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {roleOptions.map((option) => (
                                  <SelectItem key={option} value={option}>
                                    {option}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          ) : (
                            <StatusBadge label={member.role} tone="neutral" />
                          )}
                        </td>
                        <td>
                          <span className="project-mobile-label">加入时间</span>
                          <span>{member.joinedAt}</span>
                        </td>
                        <td>
                          <span className="project-mobile-label">操作</span>
                          {permissions.canManageMembers && !member.isOwner ? (
                            <div className="project-table__actions">
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                aria-label="Transfer ownership"
                                disabled={!writable}
                                title={
                                  writable
                                    ? "转移项目所有权"
                                    : member.isOwner
                                      ? "当前所有者不能转移给自己"
                                      : "成员管理权限不可用"
                                }
                                onClick={(event) => {
                                  transferTriggerRef.current =
                                    event.currentTarget
                                  setTransferTarget(member)
                                }}
                              >
                                <ShieldCheck aria-hidden="true" />
                                转移所有权
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                disabled={!writable}
                                aria-label={`Remove ${member.displayName}`}
                                title={writable ? "移除成员" : "移除操作不可用"}
                                onClick={() => props.onRemoveMember(member.id)}
                              >
                                <Trash2 aria-hidden="true" />
                                移除
                              </Button>
                            </div>
                          ) : null}
                          {!writable ? (
                            <DisabledReason>
                              {member.isOwner
                                ? "所有者必须先完成正式所有权转移。"
                                : "当前成员操作不可用。"}
                            </DisabledReason>
                          ) : null}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
          <Dialog
            open={transferTarget !== null}
            onOpenChange={(open) => {
              if (!open) closeTransfer()
            }}
          >
            <DialogContent>
              <form className="space-y-5" onSubmit={transferOwnership}>
                <DialogHeader>
                  <DialogTitle>转移项目所有权</DialogTitle>
                  <DialogDescription>
                    目标成员：{transferTarget?.displayName ?? "未选择"}
                    。该操作只发出意图，服务端返回前不会改变成员角色。
                  </DialogDescription>
                </DialogHeader>
                <div className="project-field">
                  <label htmlFor="previous-owner-role">原所有者的新角色</label>
                  <Select
                    value={previousOwnerRole}
                    onValueChange={(value) =>
                      setPreviousOwnerRole(value as MemberRoleOption)
                    }
                  >
                    <SelectTrigger id="previous-owner-role">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {roleOptions.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="project-field">
                  <label htmlFor="ownership-transfer-reason">转移原因</label>
                  <Input
                    id="ownership-transfer-reason"
                    name="reason"
                    required
                    placeholder="说明正式所有权转移原因"
                  />
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={closeTransfer}
                  >
                    取消
                  </Button>
                  <Button type="submit" variant="destructive">
                    确认转移意图
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </>
      )}
    </ProjectPanel>
  )
}
