import {
  AlertTriangle,
  ArrowLeft,
  Ban,
  Bot,
  ChevronDown,
  ChevronRight,
  Circle,
  CircleDashed,
  Clock3,
  Cpu,
  Database,
  ExternalLink,
  FileCheck2,
  ListChecks,
  LoaderCircle,
  MessageSquareText,
  PanelRight,
  Play,
  RefreshCw,
  RotateCcw,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Square,
  UserRoundCheck,
  Wrench,
  XCircle,
} from "lucide-react"
import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from "react"

import {
  JobProgress,
  MetadataList,
  MutationError,
  SourceBadge,
  StatusBadge,
  useVisualTheme,
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

import type {
  ActionCapability,
  AgentEventViewModel,
  AgentRunState,
  AgentWorkspaceViewModel,
  FactKind,
  ToolCallViewModel,
} from "../model"
import type { AgentWorkspaceEvent, AgentWorkspaceProps } from "./contracts"
import "./agent-workspace.css"

export type AgentWorkspaceSurface = "run" | "plan" | "timeline" | "tools"

export type AgentWorkspaceVisualProps = AgentWorkspaceProps & {
  initialSurface?: AgentWorkspaceSurface
  onSurfaceChange?: (surface: AgentWorkspaceSurface) => void
}

const surfaces: ReadonlyArray<{
  id: AgentWorkspaceSurface
  label: string
  icon: typeof Bot
}> = [
  { id: "run", label: "运行", icon: Bot },
  { id: "plan", label: "计划", icon: ListChecks },
  { id: "timeline", label: "时间线", icon: MessageSquareText },
  { id: "tools", label: "工具", icon: Wrench },
]

const factDefinitions: Record<
  FactKind,
  { label: string; kind: Parameters<typeof SourceBadge>[0]["kind"] }
> = {
  AGENT_SUGGESTION: { label: "Agent 建议", kind: "ai-suggestion" },
  SYSTEM_FACT: { label: "系统事实", kind: "verified" },
  DETERMINISTIC_RESULT: { label: "确定性结果", kind: "evidence" },
  USER_CONFIRMATION: { label: "用户确认", kind: "human-decision" },
  FORMAL_APPROVAL: { label: "正式审批", kind: "approval" },
}

function runLabel(state: AgentRunState) {
  const labels: Record<AgentRunState, string> = {
    accepted: "已受理",
    planning: "规划中",
    running: "运行中",
    "waiting-user-input": "等待用户输入",
    "waiting-approval": "等待正式审批",
    completed: "已完成",
    failed: "失败",
    cancelled: "已取消",
    unknown: "未知状态",
  }
  return labels[state]
}

function runTone(state: AgentRunState) {
  if (state === "completed") return "success"
  if (state === "failed" || state === "cancelled") return "danger"
  if (state === "waiting-approval" || state === "waiting-user-input")
    return "warning"
  if (state === "unknown") return "unknown"
  return "info"
}

function planTone(status: string, known: boolean) {
  if (!known) return "unknown"
  if (status === "COMPLETED") return "success"
  if (status === "FAILED" || status === "CANCELLED") return "danger"
  if (status === "RUNNING") return "info"
  if (status.includes("WAITING")) return "warning"
  return "neutral"
}

function planLabel(status: string, known: boolean) {
  if (!known) return `未知 · ${status}`
  const labels: Record<string, string> = {
    PENDING: "待执行",
    PLANNING: "规划中",
    RUNNING: "执行中",
    COMPLETED: "已完成",
    FAILED: "失败",
    CANCELLED: "已取消",
    WAITING_USER_INPUT: "等待输入",
    WAITING_APPROVAL: "等待审批",
  }
  return labels[status] ?? status
}

function statusTone(status: string, known: boolean) {
  if (!known) return "unknown"
  if (["COMPLETED", "SUCCEEDED", "APPROVED"].includes(status)) return "success"
  if (["FAILED", "DENIED", "REJECTED", "CANCELLED"].includes(status))
    return "danger"
  if (["PENDING", "REQUESTED", "RUNNING", "QUEUED"].includes(status))
    return "info"
  if (["EXPIRED", "STALE", "TIMEOUT"].includes(status)) return "warning"
  return "neutral"
}

function toolCategoryLabel(category: ToolCallViewModel["category"]) {
  const labels: Record<ToolCallViewModel["category"], string> = {
    READ_ONLY: "只读工具",
    SUGGESTION: "建议工具",
    SIDE_EFFECT: "副作用工具",
    UNKNOWN: "未知类别",
  }
  return labels[category]
}

function confirmationLabel(confirmation: ToolCallViewModel["confirmation"]) {
  const labels: Record<ToolCallViewModel["confirmation"], string> = {
    NONE: "无需确认",
    LIGHT_CONFIRMATION: "轻量确认",
    FORMAL_APPROVAL: "需要正式审批",
    PROHIBITED: "策略禁止",
    UNKNOWN: "确认要求未知",
  }
  return labels[confirmation]
}

function sourceStateCopy(state: AgentWorkspaceViewModel["sourceState"]) {
  const copies: Record<AgentWorkspaceViewModel["sourceState"], string> = {
    available: "来源可用，可按服务端投影打开正式对象。",
    denied: "来源访问被拒绝；不会披露对象身份、名称或数量。",
    missing: "来源资源缺失，无法打开。",
    stale: "来源或项目快照已过期，需要刷新后再定位。",
    invalidated: "来源已失效但保留历史风险，不等于已删除。",
    unknown: "来源状态未知，跳转保持禁用。",
  }
  return copies[state]
}

function formatTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }).format(date)
}

function shortId(value: string) {
  return value.length > 18 ? `${value.slice(0, 8)}…${value.slice(-6)}` : value
}

function CapabilityButton({
  capability,
  pending,
  label,
  pendingLabel,
  icon,
  variant = "outline",
  onClick,
}: {
  capability: ActionCapability
  pending: boolean
  label: string
  pendingLabel: string
  icon: ReactNode
  variant?: "default" | "outline" | "ghost"
  onClick: () => void
}) {
  const reason = capability.reason ?? "服务端未提供该操作能力。"
  return (
    <Button
      type="button"
      size="sm"
      variant={variant}
      disabled={!capability.allowed || pending}
      title={!capability.allowed ? reason : label}
      aria-label={!capability.allowed ? `${label}：${reason}` : label}
      onClick={onClick}
    >
      {pending ? <LoaderCircle className="m8-spin" aria-hidden="true" /> : icon}
      {pending ? pendingLabel : label}
    </Button>
  )
}

function SafetyNotices({ data }: { data: AgentWorkspaceViewModel }) {
  const notices: Array<{
    key: string
    icon: typeof AlertTriangle
    title: string
    text: string
    tone: string
  }> = []
  if (!data.permissionsKnown) {
    notices.push({
      key: "permissions",
      icon: ShieldAlert,
      title: "权限状态未知",
      text: "所有写操作保持禁用，等待服务端重新确认项目权限。",
      tone: "danger",
    })
  }
  if (data.run && !data.run.snapshotCurrent) {
    notices.push({
      key: "snapshot",
      icon: Clock3,
      title: "项目快照已过期",
      text: "当前事实仍可阅读，但继续、取消或重试需要先刷新。",
      tone: "warning",
    })
  }
  if (data.providerDegraded) {
    notices.push({
      key: "provider",
      icon: CircleDashed,
      title: "模型提供方已降级",
      text: "Agent 建议可能不可用；已有系统事实与确定性结果仍可复核。",
      tone: "degraded",
    })
  }
  if (data.schemaInvalid) {
    notices.push({
      key: "schema",
      icon: XCircle,
      title: "结构化输出无效",
      text: "该输出未被接受为成功结果，请刷新或返回结构化工作台。",
      tone: "danger",
    })
  }
  if (data.promptInjectionBlocked) {
    notices.push({
      key: "injection",
      icon: Ban,
      title: "提示注入已阻断",
      text: "安全策略已阻止不可信指令，受阻内容不会在此披露。",
      tone: "danger",
    })
  }
  if (data.toolDenied) {
    notices.push({
      key: "tool-policy",
      icon: Ban,
      title: "Tool 已被策略拒绝",
      text: "该阻断不能在 Agent 面板中绕过；请返回结构化工作台复核允许操作。",
      tone: "danger",
    })
  }
  if (data.approvalStale) {
    notices.push({
      key: "approval-stale",
      icon: ShieldAlert,
      title: "Approval 已过期或不再匹配",
      text: "Agent 不会自动恢复或继续副作用操作，需要正式 Approval surface 重新核验。",
      tone: "warning",
    })
  }
  if (data.sourceState !== "available") {
    notices.push({
      key: "source-state",
      icon: Database,
      title:
        data.sourceState === "denied"
          ? "来源访问被拒绝"
          : data.sourceState === "missing"
            ? "来源缺失"
            : data.sourceState === "stale"
              ? "来源已过期"
              : data.sourceState === "invalidated"
                ? "来源已失效"
                : "来源状态未知",
      text: sourceStateCopy(data.sourceState),
      tone:
        data.sourceState === "denied" || data.sourceState === "invalidated"
          ? "danger"
          : data.sourceState === "unknown"
            ? "unknown"
            : "warning",
    })
  }
  if (data.routeFallback) {
    notices.push({
      key: "route",
      icon: ArrowLeft,
      title: "已回退到项目 Agent 面板",
      text: "深链目标不可用或未授权；界面不会披露目标对象是否存在。",
      tone: "unknown",
    })
  }
  if (!notices.length) return null
  return (
    <div className="m8-notice-stack" aria-label="安全与降级状态">
      {notices.map((notice) => {
        const Icon = notice.icon
        return (
          <div
            key={notice.key}
            className="m8-notice"
            data-tone={notice.tone}
            role="status"
          >
            <Icon aria-hidden="true" />
            <div>
              <strong>{notice.title}</strong>
              <span>{notice.text}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function PlanPane({ data }: { data: AgentWorkspaceViewModel }) {
  return (
    <aside className="m8-plan-pane" aria-labelledby="m8-plan-heading">
      <header className="m8-pane-heading">
        <div>
          <span>项目编排</span>
          <h2 id="m8-plan-heading">阶段与计划</h2>
        </div>
        <StatusBadge label={data.projectStage} tone="neutral" />
      </header>
      <div className="m8-plan-scroll">
        <section
          className="m8-plan-section"
          aria-labelledby="m8-blockers-heading"
        >
          <h3 id="m8-blockers-heading">阻塞项</h3>
          {data.blockers.length ? (
            <ul className="m8-compact-list m8-compact-list--warning">
              {data.blockers.map((blocker, index) => (
                <li key={`${blocker}-${index}`}>
                  <AlertTriangle aria-hidden="true" />
                  <span>{blocker}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="m8-empty-copy">当前投影没有阻塞项。</p>
          )}
        </section>
        <section
          className="m8-plan-section"
          aria-labelledby="m8-actions-heading"
        >
          <h3 id="m8-actions-heading">允许的下一步</h3>
          {data.allowedNextActions.length ? (
            <ul className="m8-compact-list">
              {data.allowedNextActions.map((item, index) => (
                <li key={`${item}-${index}`}>
                  <ChevronRight aria-hidden="true" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="m8-empty-copy">服务端未投影可执行下一步。</p>
          )}
        </section>
        <section className="m8-plan-section" aria-labelledby="m8-steps-heading">
          <div className="m8-section-row">
            <h3 id="m8-steps-heading">Agent 计划</h3>
            <span>{data.planSteps.length} 步</span>
          </div>
          {data.planSteps.length ? (
            <ol className="m8-step-list">
              {data.planSteps.map((step, index) => (
                <li key={step.id}>
                  <span className="m8-step-index">{index + 1}</span>
                  <div>
                    <strong>{step.label}</strong>
                    <StatusBadge
                      label={planLabel(step.status, step.knownStatus)}
                      tone={planTone(step.status, step.knownStatus)}
                      title={step.knownStatus ? undefined : step.status}
                    />
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <p className="m8-empty-copy">
              尚无计划步骤。计划仅由服务端运行投影，不可在此勾选完成。
            </p>
          )}
        </section>
      </div>
    </aside>
  )
}

function TimelineRow({ event }: { event: AgentEventViewModel }) {
  const [expanded, setExpanded] = useState(false)
  const definition = factDefinitions[event.factKind]
  const text = event.text?.trim() || "服务端未提供可安全展示的事件摘要。"
  const long = text.length > 220
  return (
    <li className="m8-timeline-row" data-fact-kind={event.factKind}>
      <span className="m8-timeline-marker" aria-hidden="true">
        {event.factKind === "AGENT_SUGGESTION" ? (
          <Sparkles />
        ) : event.factKind === "FORMAL_APPROVAL" ? (
          <ShieldCheck />
        ) : event.factKind === "USER_CONFIRMATION" ? (
          <UserRoundCheck />
        ) : event.factKind === "DETERMINISTIC_RESULT" ? (
          <FileCheck2 />
        ) : (
          <Circle />
        )}
      </span>
      <article>
        <header>
          <div>
            <SourceBadge label={definition.label} kind={definition.kind} />
            <span className="m8-event-kind">{event.kind}</span>
          </div>
          <time dateTime={event.createdAt}>{formatTime(event.createdAt)}</time>
        </header>
        <p className={long && !expanded ? "m8-event-text--clamped" : undefined}>
          {text}
        </p>
        {long ? (
          <button
            type="button"
            className="m8-disclosure"
            aria-expanded={expanded}
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? <ChevronDown /> : <ChevronRight />}
            {expanded ? "收起摘要" : "展开完整安全摘要"}
          </button>
        ) : null}
      </article>
    </li>
  )
}

function MessageComposer({
  data,
  pendingAction,
  onEvent,
}: {
  data: AgentWorkspaceViewModel
  pendingAction: AgentWorkspaceProps["pendingAction"]
  onEvent: AgentWorkspaceProps["onEvent"]
}) {
  const [message, setMessage] = useState("")
  if (!data.run || data.run.state !== "waiting-user-input") return null
  const capability = data.capabilities.sendMessage
  const pending = pendingAction === "send-message"
  const submit = (event: FormEvent) => {
    event.preventDefault()
    const value = message.trim()
    if (!value || !capability.allowed || pending) return
    onEvent({
      action: "send-message",
      input: { runId: data.run!.id, message: value },
    })
  }
  return (
    <form
      className="m8-composer"
      onSubmit={submit}
      aria-label="回复 Agent 请求"
    >
      <label htmlFor="m8-agent-message">补充信息</label>
      <p id="m8-agent-message-description">
        仅发送用户意图。消息被接受不代表运行已恢复。
      </p>
      <div>
        <textarea
          id="m8-agent-message"
          value={message}
          rows={3}
          maxLength={500}
          aria-describedby="m8-agent-message-description m8-agent-message-reason"
          disabled={!capability.allowed || pending}
          onChange={(event) => setMessage(event.target.value)}
        />
        <Button
          type="submit"
          size="sm"
          disabled={!capability.allowed || pending || !message.trim()}
        >
          {pending ? <LoaderCircle className="m8-spin" /> : <Send />}
          {pending ? "发送中" : "发送"}
        </Button>
      </div>
      <span id="m8-agent-message-reason" className="m8-field-reason">
        {!capability.allowed
          ? (capability.reason ?? "当前运行不接受用户输入。")
          : `${message.length}/500`}
      </span>
    </form>
  )
}

function TimelinePane({
  data,
  pendingAction,
  onEvent,
}: {
  data: AgentWorkspaceViewModel
  pendingAction: AgentWorkspaceProps["pendingAction"]
  onEvent: AgentWorkspaceProps["onEvent"]
}) {
  return (
    <section className="m8-timeline-pane" aria-labelledby="m8-timeline-heading">
      <header className="m8-pane-heading">
        <div>
          <span>审计与操作流</span>
          <h2 id="m8-timeline-heading">事件时间线</h2>
        </div>
        <span className="m8-pane-count">{data.timeline.length} 条</span>
      </header>
      <div className="m8-timeline-scroll">
        {data.timeline.length ? (
          <ol className="m8-timeline-list">
            {data.timeline.map((event) => (
              <TimelineRow key={event.id} event={event} />
            ))}
          </ol>
        ) : (
          <div className="m8-workspace-empty" role="status">
            <MessageSquareText aria-hidden="true" />
            <strong>尚无运行事件</strong>
            <p>创建 AgentRun 后，服务端安全摘要会按序显示在这里。</p>
          </div>
        )}
      </div>
      <MessageComposer
        data={data}
        pendingAction={pendingAction}
        onEvent={onEvent}
      />
    </section>
  )
}

function RunInspector({ data }: { data: AgentWorkspaceViewModel }) {
  const run = data.run
  return (
    <div className="m8-inspector-content">
      <section>
        <h3>运行事实</h3>
        {run ? (
          <dl className="m8-metadata">
            <div>
              <dt>Run ID</dt>
              <dd title={run.id}>{shortId(run.id)}</dd>
            </div>
            <div>
              <dt>原始状态</dt>
              <dd>{run.status}</dd>
            </div>
            <div>
              <dt>快照</dt>
              <dd>{run.snapshotCurrent ? "当前" : "已过期"}</dd>
            </div>
            <div>
              <dt>锁版本</dt>
              <dd>{run.lockVersion}</dd>
            </div>
            <div>
              <dt>失败代码</dt>
              <dd>{run.failureCode ?? "无"}</dd>
            </div>
            <div>
              <dt>降级代码</dt>
              <dd>{run.degradationCode ?? "无"}</dd>
            </div>
          </dl>
        ) : (
          <p className="m8-empty-copy">当前项目没有 AgentRun。</p>
        )}
      </section>
      <section>
        <h3>对象边界</h3>
        <ul className="m8-boundary-list">
          <li>
            AgentRun、ToolCall、ModelInvocation、Job 与 Approval 独立显示。
          </li>
          <li>建议不等于系统事实，系统事实不等于确定性结果。</li>
          <li>本地选择、展开与滚动不会改变正式状态。</li>
        </ul>
      </section>
    </div>
  )
}

function ToolInspector({
  data,
  tool,
  pendingAction,
  onEvent,
}: {
  data: AgentWorkspaceViewModel
  tool: ToolCallViewModel
  pendingAction: AgentWorkspaceProps["pendingAction"]
  onEvent: AgentWorkspaceProps["onEvent"]
}) {
  const invocations = data.modelInvocations.filter(
    (invocation) =>
      invocation.toolCallId === tool.id || invocation.toolCallId === null,
  )
  const sourceAvailable =
    data.sourceState === "available" && tool.sourceLink !== null
  const approvalSafe =
    tool.approval?.knownStatus === true &&
    !tool.approval.stale &&
    tool.errorCode !== "APPROVAL_HASH_MISMATCH"
  const retryAllowed =
    tool.knownStatus &&
    tool.retryable &&
    data.run?.knownStatus === true &&
    data.run.snapshotCurrent &&
    data.capabilities.retryOrRestart.allowed
  const retryReason = !tool.knownStatus
    ? "ToolCall 状态未知。"
    : !tool.retryable
      ? "该 ToolCall 未投影为可重试。"
      : !data.run?.snapshotCurrent
        ? "项目快照已过期，请先刷新。"
        : (data.capabilities.retryOrRestart.reason ??
          "Workspace 未提供重试或重新开始能力。")

  return (
    <div className="m8-inspector-content m8-tool-inspector">
      <section>
        <div className="m8-inspector-title-row">
          <div>
            <span>ToolCall</span>
            <h3>{tool.name}</h3>
          </div>
          <StatusBadge
            label={tool.knownStatus ? tool.status : `未知 · ${tool.status}`}
            tone={statusTone(tool.status, tool.knownStatus)}
          />
        </div>
        <div className="m8-badge-row">
          <StatusBadge
            label={toolCategoryLabel(tool.category)}
            tone="neutral"
          />
          <StatusBadge
            label={confirmationLabel(tool.confirmation)}
            tone={
              tool.confirmation === "PROHIBITED"
                ? "danger"
                : tool.confirmation === "FORMAL_APPROVAL"
                  ? "approval"
                  : tool.confirmation === "UNKNOWN"
                    ? "unknown"
                    : "neutral"
            }
          />
          <SourceBadge
            label={factDefinitions[tool.factKind].label}
            kind={factDefinitions[tool.factKind].kind}
          />
        </div>
        <MetadataList
          items={[
            { label: "版本", value: tool.version, mono: true },
            { label: "Tool ID", value: shortId(tool.id), mono: true },
            { label: "错误代码", value: tool.errorCode ?? "无", mono: true },
          ]}
        />
      </section>

      <section>
        <h3>服务端安全摘要</h3>
        <div className="m8-summary-pair">
          <div>
            <span>输入摘要</span>
            <p>{tool.inputSummary ?? "未提供可安全展示的输入摘要。"}</p>
          </div>
          <div>
            <span>输出摘要</span>
            <p>{tool.outputSummary ?? "未提供可安全展示的输出摘要。"}</p>
          </div>
        </div>
        <p className="m8-inspector-note">
          摘要不是完整参数或结果；Preview Event Log 不记录这些文本。
        </p>
      </section>

      {tool.category === "SUGGESTION" ? (
        <section className="m8-integrity-note" data-tone="ai">
          <Sparkles aria-hidden="true" />
          <div>
            <strong>建议尚未采用</strong>
            <p>该输出仍是 Agent 建议，不是系统事实或正式科研决定。</p>
          </div>
        </section>
      ) : null}
      {tool.confirmation === "PROHIBITED" || tool.status === "DENIED" ? (
        <section className="m8-integrity-note" data-tone="danger">
          <Ban aria-hidden="true" />
          <div>
            <strong>策略阻断</strong>
            <p>该 ToolCall 不可执行，界面不提供本地绕过方式。</p>
          </div>
        </section>
      ) : null}

      <section>
        <h3>关联 Job</h3>
        {tool.job ? (
          <>
            <JobProgress
              label="Tool 关联 Job"
              statusLabel={
                tool.job.knownStatus
                  ? tool.job.status
                  : `未知 · ${tool.job.status}`
              }
              tone={statusTone(tool.job.status, tool.job.knownStatus)}
              progress={tool.job.progress}
              step={tool.job.errorCode ?? "Tool 与 Job 状态相互独立"}
            />
            <p className="m8-inspector-note">
              Tool completed 不等于 Job completed；Job completed 也不由 UI
              生成正式领域结果。
            </p>
          </>
        ) : (
          <p className="m8-empty-copy">当前 ToolCall 没有关联 Job 投影。</p>
        )}
      </section>

      <section>
        <h3>正式 Approval</h3>
        {tool.approval ? (
          <>
            <MetadataList
              items={[
                {
                  label: "Approval ID",
                  value: shortId(tool.approval.id),
                  mono: true,
                },
                {
                  label: "状态",
                  value: tool.approval.knownStatus
                    ? tool.approval.status
                    : `未知 · ${tool.approval.status}`,
                },
                {
                  label: "新鲜度",
                  value: tool.approval.stale ? "已过期或失配" : "当前",
                },
                {
                  label: "到期时间",
                  value: tool.approval.expiresAt ?? "未提供",
                  mono: true,
                },
              ]}
            />
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={!approvalSafe || pendingAction === "open-approval"}
              aria-label={
                approvalSafe
                  ? "打开正式 Approval"
                  : "打开正式 Approval：状态未知、已过期或 payload 不匹配"
              }
              title={
                approvalSafe
                  ? "打开正式 Approval"
                  : "状态未知、已过期或 payload 不匹配"
              }
              onClick={() =>
                onEvent({
                  action: "open-approval",
                  input: { approvalId: tool.approval!.id },
                })
              }
            >
              <ShieldCheck aria-hidden="true" /> 打开正式 Approval
            </Button>
            {!approvalSafe ? (
              <p className="m8-action-reason" role="status">
                Approval 状态未知、stale/expired 或 hash mismatch
                时保持安全阻断。
              </p>
            ) : null}
          </>
        ) : (
          <p className="m8-empty-copy">当前 ToolCall 没有关联 Approval。</p>
        )}
      </section>

      <section>
        <h3>来源</h3>
        <div className="m8-source-state" data-state={data.sourceState}>
          <Database aria-hidden="true" />
          <p>{sourceStateCopy(data.sourceState)}</p>
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={!sourceAvailable || pendingAction === "open-source"}
          aria-label={
            sourceAvailable
              ? "打开正式来源"
              : `打开正式来源：${sourceStateCopy(data.sourceState)}`
          }
          title={
            sourceAvailable ? "打开正式来源" : sourceStateCopy(data.sourceState)
          }
          onClick={() =>
            tool.sourceLink &&
            onEvent({ action: "open-source", input: tool.sourceLink })
          }
        >
          <ExternalLink aria-hidden="true" /> 打开正式来源
        </Button>
      </section>

      <section>
        <h3>ModelInvocation</h3>
        {invocations.length ? (
          <div className="m8-invocation-list">
            {invocations.map((invocation) => (
              <article key={invocation.id}>
                <div>
                  <Cpu aria-hidden="true" />
                  <strong>{shortId(invocation.id)}</strong>
                  <StatusBadge
                    label={
                      invocation.knownStatus
                        ? invocation.status
                        : `未知 · ${invocation.status}`
                    }
                    tone={statusTone(invocation.status, invocation.knownStatus)}
                  />
                </div>
                <MetadataList
                  items={[
                    {
                      label: "关联",
                      value:
                        invocation.toolCallId === tool.id
                          ? "当前 ToolCall"
                          : "AgentRun",
                    },
                    {
                      label: "Token",
                      value:
                        invocation.totalTokens === null
                          ? "未知"
                          : `${invocation.inputTokens ?? "?"} + ${invocation.outputTokens ?? "?"} = ${invocation.totalTokens}`,
                      mono: true,
                    },
                    {
                      label: "请求次数",
                      value: invocation.requestCount ?? "未知",
                      mono: true,
                    },
                    {
                      label: "延迟",
                      value:
                        invocation.latencyMs === null
                          ? "未知"
                          : `${invocation.latencyMs} ms`,
                      mono: true,
                    },
                    {
                      label: "错误代码",
                      value: invocation.errorCode ?? "无",
                      mono: true,
                    },
                  ]}
                />
                {invocation.degraded ? (
                  <p className="m8-action-reason">
                    Provider 已降级；Token 与延迟不代表科研质量。
                  </p>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <p className="m8-empty-copy">
            当前 ToolCall 没有关联 ModelInvocation；Run 级 invocation 保持独立。
          </p>
        )}
      </section>

      <section>
        <h3>安全下一步</h3>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={!retryAllowed || pendingAction === "retry-or-restart"}
          aria-label={
            retryAllowed ? "重试或重新开始" : `重试或重新开始：${retryReason}`
          }
          title={retryAllowed ? "重试或重新开始" : retryReason}
          onClick={() =>
            data.run &&
            onEvent({
              action: "retry-or-restart",
              input: { runId: data.run.id, goal: data.run.safeGoal ?? "" },
            })
          }
        >
          <RotateCcw aria-hidden="true" /> 重试或重新开始
        </Button>
        {!retryAllowed ? (
          <p className="m8-action-reason" role="status">
            {retryReason}
          </p>
        ) : null}
      </section>
    </div>
  )
}

function WorkspaceInspector({
  data,
  selectedToolCallId,
  pendingAction,
  onEvent,
}: {
  data: AgentWorkspaceViewModel
  selectedToolCallId: string | null
  pendingAction: AgentWorkspaceProps["pendingAction"]
  onEvent: AgentWorkspaceProps["onEvent"]
}) {
  const tool =
    data.toolCalls.find((item) => item.id === selectedToolCallId) ??
    data.toolCalls[0] ??
    null
  return tool ? (
    <ToolInspector
      data={data}
      tool={tool}
      pendingAction={pendingAction}
      onEvent={onEvent}
    />
  ) : (
    <RunInspector data={data} />
  )
}

function ToolsSurface({
  data,
  selectedToolCallId,
  onToolSelectionChange,
  onOpenInspector,
}: {
  data: AgentWorkspaceViewModel
  selectedToolCallId: string | null
  onToolSelectionChange: (id: string | null) => void
  onOpenInspector: () => void
}) {
  return (
    <section className="m8-tools-surface" aria-labelledby="m8-tools-heading">
      <header className="m8-pane-heading">
        <div>
          <span>只读运行投影</span>
          <h2 id="m8-tools-heading">ToolCall</h2>
        </div>
        <span className="m8-pane-count">{data.toolCalls.length} 项</span>
      </header>
      {data.toolCalls.length ? (
        <div className="m8-tool-list" role="listbox" aria-label="ToolCall 列表">
          {data.toolCalls.map((tool) => (
            <button
              key={tool.id}
              type="button"
              role="option"
              aria-selected={selectedToolCallId === tool.id}
              onClick={() => {
                onToolSelectionChange(tool.id)
                onOpenInspector()
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault()
                  onToolSelectionChange(tool.id)
                  onOpenInspector()
                  return
                }
                if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return
                event.preventDefault()
                const options = Array.from(
                  event.currentTarget.parentElement?.querySelectorAll<HTMLElement>(
                    '[role="option"]',
                  ) ?? [],
                )
                const index = options.indexOf(event.currentTarget)
                const direction = event.key === "ArrowDown" ? 1 : -1
                options[
                  (index + direction + options.length) % options.length
                ]?.focus()
              }}
            >
              <Wrench aria-hidden="true" />
              <span>
                <strong>{tool.name}</strong>
                <small>
                  {toolCategoryLabel(tool.category)} · {tool.status}
                </small>
              </span>
              <StatusBadge
                label={tool.knownStatus ? tool.status : "未知"}
                tone={statusTone(tool.status, tool.knownStatus)}
              />
              <ChevronRight aria-hidden="true" />
            </button>
          ))}
        </div>
      ) : (
        <div className="m8-workspace-empty" role="status">
          <Wrench aria-hidden="true" />
          <strong>没有 ToolCall</strong>
          <p>本阶段不推断工具执行；仅显示服务端已投影的记录。</p>
        </div>
      )}
    </section>
  )
}

function CreateRunDialog({
  open,
  capability,
  pending,
  onOpenChange,
  onSubmit,
}: {
  open: boolean
  capability: ActionCapability
  pending: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (goal: string, allowToolCalls: boolean) => void
}) {
  const [goal, setGoal] = useState("")
  const [allowToolCalls, setAllowToolCalls] = useState(true)
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!goal.trim() || !capability.allowed || pending) return
    onSubmit(goal.trim(), allowToolCalls)
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="m8-dialog" data-od-id="create-agent-run-dialog">
        <DialogHeader>
          <DialogTitle>创建 AgentRun</DialogTitle>
          <DialogDescription>
            Agent
            只生成建议、解释和计划。正式科研状态仍由结构化工作台与服务端决定。
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit}>
          <label htmlFor="m8-run-goal">目标</label>
          <textarea
            id="m8-run-goal"
            autoFocus
            rows={5}
            maxLength={500}
            value={goal}
            aria-describedby="m8-run-goal-help"
            disabled={!capability.allowed || pending}
            onChange={(event) => setGoal(event.target.value)}
          />
          <p id="m8-run-goal-help">
            最多 500 字。Preview Event Log 只记录长度，不记录正文。
          </p>
          <label className="m8-check-row">
            <input
              type="checkbox"
              checked={allowToolCalls}
              disabled={!capability.allowed || pending}
              onChange={(event) => setAllowToolCalls(event.target.checked)}
            />
            <span>
              <strong>允许白名单工具调用</strong>
              <small>工具仍受服务端权限、阶段、审批与快照规则约束。</small>
            </span>
          </label>
          <div className="m8-fixed-mode">
            <span>运行模式</span>
            <strong>PLAN_AND_EXPLAIN</strong>
            <small>提供方模式由服务端管理，用户不可选择。</small>
          </div>
          {!capability.allowed ? (
            <p className="m8-dialog-reason" role="status">
              <ShieldAlert aria-hidden="true" />
              {capability.reason ?? "当前项目不可创建 AgentRun。"}
            </p>
          ) : null}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={!goal.trim() || !capability.allowed || pending}
            >
              {pending ? <LoaderCircle className="m8-spin" /> : <Play />}
              {pending ? "提交中" : "提交创建意图"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function CancelRunDialog({
  open,
  pending,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  pending: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="m8-dialog" data-od-id="cancel-agent-run-dialog">
        <DialogHeader>
          <DialogTitle>取消当前 AgentRun？</DialogTitle>
          <DialogDescription>
            取消只表达停止后续编排的意图，不会回滚已完成的 Tool、Job
            或领域事实。
          </DialogDescription>
        </DialogHeader>
        <div className="m8-dialog-warning" role="note">
          <AlertTriangle aria-hidden="true" />
          <span>最终取消状态以服务端刷新后的 AgentRun 为准。</span>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            返回
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={pending}
            onClick={onConfirm}
          >
            {pending ? <LoaderCircle className="m8-spin" /> : <Square />}
            {pending ? "提交中" : "提交取消意图"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function RetryRunDialog({
  open,
  pending,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  pending: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="m8-dialog" data-od-id="retry-agent-run-dialog">
        <DialogHeader>
          <DialogTitle>重试或重新开始当前 AgentRun？</DialogTitle>
          <DialogDescription>
            此操作只提交重试或重新开始意图。服务端仍会重新检查权限、快照、阶段和幂等边界。
          </DialogDescription>
        </DialogHeader>
        <div className="m8-dialog-warning" role="note">
          <AlertTriangle aria-hidden="true" />
          <span>
            已完成的 Tool、Job、Approval
            和领域事实不会由前端回滚或复制；后续状态以刷新后的服务端投影为准。
          </span>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            返回
          </Button>
          <Button type="button" disabled={pending} onClick={onConfirm}>
            {pending ? <LoaderCircle className="m8-spin" /> : <RotateCcw />}
            {pending ? "提交中" : "提交重试意图"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function WorkspaceLoading() {
  const theme = useVisualTheme() ?? "light"
  return (
    <main className="m8-agent-workspace reca-visual-refresh" data-theme={theme}>
      <header
        className="m8-header m8-header--loading"
        aria-label="正在加载 Agent 工作台"
      >
        <div>
          <span />
          <span />
        </div>
        <a className="m8-direct-link" href="/projects">
          <ArrowLeft aria-hidden="true" /> 返回结构化工作台
        </a>
      </header>
      <div className="m8-loading-grid" role="status" aria-live="polite">
        <span className="sr-only">正在加载 Agent 工作台</span>
        {[0, 1, 2].map((pane) => (
          <section key={pane} aria-hidden="true">
            <div />
            <div />
            <div />
            <div />
          </section>
        ))}
      </div>
    </main>
  )
}

export function AgentWorkspace({
  content,
  pendingAction,
  mutationError,
  onRetry,
  onEvent,
  selectedToolCallId: controlledToolId,
  onToolSelectionChange,
  initialSurface = "timeline",
  onSurfaceChange,
}: AgentWorkspaceVisualProps) {
  const theme = useVisualTheme() ?? "light"
  const [surface, setSurface] = useState<AgentWorkspaceSurface>(initialSurface)
  const [localToolId, setLocalToolId] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [cancelOpen, setCancelOpen] = useState(false)
  const [retryOpen, setRetryOpen] = useState(false)
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const createTriggerRef = useRef<HTMLElement | null>(null)
  const cancelTriggerRef = useRef<HTMLElement | null>(null)
  const retryTriggerRef = useRef<HTMLElement | null>(null)
  const inspectorTriggerRef = useRef<HTMLElement | null>(null)
  const serverRunId = content.state === "ready" ? content.data.run?.id : null
  const serverRunStatus =
    content.state === "ready" ? content.data.run?.status : null

  useEffect(() => setSurface(initialSurface), [initialSurface])
  useEffect(() => {
    setCreateOpen(false)
    setCancelOpen(false)
    setRetryOpen(false)
  }, [serverRunId, serverRunStatus])
  const changeSurface = (next: AgentWorkspaceSurface) => {
    setSurface(next)
    onSurfaceChange?.(next)
  }
  const openInspector = () => {
    inspectorTriggerRef.current = document.activeElement as HTMLElement | null
    setInspectorOpen(true)
  }
  const openActionDialog = (
    triggerRef: { current: HTMLElement | null },
    setOpen: (open: boolean) => void,
  ) => {
    triggerRef.current = document.activeElement as HTMLElement | null
    setOpen(true)
  }
  const changeActionDialog = (
    open: boolean,
    triggerRef: { current: HTMLElement | null },
    setOpen: (open: boolean) => void,
  ) => {
    setOpen(open)
    if (!open) window.setTimeout(() => triggerRef.current?.focus(), 0)
  }
  const changeInspectorOpen = (open: boolean) => {
    setInspectorOpen(open)
    if (!open) {
      window.setTimeout(() => inspectorTriggerRef.current?.focus(), 0)
    }
  }

  if (content.state === "loading") return <WorkspaceLoading />

  if (content.state !== "ready") {
    const forbidden = content.state === "error" && content.error.forbidden
    const title =
      content.state === "empty"
        ? "尚无 AgentRun"
        : forbidden
          ? "无法访问 Agent 工作台"
          : "Agent 工作台加载失败"
    const message =
      content.state === "empty"
        ? content.message
        : content.state === "error"
          ? content.error.message
          : "当前状态无法安全展示。"
    return (
      <main
        className="m8-agent-workspace reca-visual-refresh"
        data-theme={theme}
      >
        <header className="m8-header">
          <div className="m8-header-identity">
            <span>RECA · Research Orchestrator</span>
            <h1>{title}</h1>
          </div>
          <a className="m8-direct-link" href="/projects">
            <ArrowLeft aria-hidden="true" /> 返回结构化工作台
          </a>
        </header>
        <section
          className="m8-load-state"
          role={forbidden ? "alert" : "status"}
        >
          {forbidden ? (
            <ShieldAlert />
          ) : content.state === "empty" ? (
            <Bot />
          ) : (
            <XCircle />
          )}
          <div>
            <h2>{title}</h2>
            <p>{message}</p>
          </div>
          {content.state === "error" && content.error.retryable ? (
            <Button type="button" variant="outline" onClick={onRetry}>
              <RefreshCw /> 重试
            </Button>
          ) : null}
        </section>
      </main>
    )
  }

  const data = content.data
  const selectedToolCallId =
    controlledToolId ?? localToolId ?? data.selectedToolCallId
  const setSelectedTool = (id: string | null) => {
    if (controlledToolId === undefined) setLocalToolId(id)
    onToolSelectionChange?.(id)
  }
  const run = data.run
  const disabledReasons = [
    ["创建", data.capabilities.createRun],
    ["取消", data.capabilities.cancelRun],
    ["重试", data.capabilities.retryOrRestart],
  ] as const

  const emit = (event: AgentWorkspaceEvent) => {
    if (pendingAction === event.action) return
    onEvent(event)
  }

  return (
    <main
      className="m8-agent-workspace reca-visual-refresh"
      data-theme={theme}
      data-run-state={run?.state ?? "none"}
      data-od-id="agent-workspace"
    >
      <header className="m8-header" data-od-id="agent-workspace-header">
        <div className="m8-header-identity">
          <span>{data.projectStage} · Research Orchestrator</span>
          <div>
            <h1>{data.projectName}</h1>
            {run ? (
              <StatusBadge
                label={runLabel(run.state)}
                tone={runTone(run.state)}
                title={run.knownStatus ? undefined : run.status}
              />
            ) : (
              <StatusBadge label="尚无 AgentRun" tone="neutral" />
            )}
            {run ? (
              <StatusBadge
                label={run.snapshotCurrent ? "快照当前" : "快照过期"}
                tone={run.snapshotCurrent ? "success" : "warning"}
              />
            ) : null}
          </div>
        </div>
        <div className="m8-header-actions">
          <a
            className="m8-direct-link"
            href={`/projects/${encodeURIComponent(data.projectId)}`}
          >
            <ArrowLeft aria-hidden="true" /> 结构化工作台
          </a>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={pendingAction === "refresh"}
            onClick={() => emit({ action: "refresh" })}
          >
            {pendingAction === "refresh" ? (
              <LoaderCircle className="m8-spin" />
            ) : (
              <RefreshCw />
            )}
            刷新
          </Button>
          <CapabilityButton
            capability={data.capabilities.retryOrRestart}
            pending={pendingAction === "retry-or-restart"}
            label="重试"
            pendingLabel="提交中"
            icon={<RotateCcw aria-hidden="true" />}
            onClick={() => openActionDialog(retryTriggerRef, setRetryOpen)}
          />
          <CapabilityButton
            capability={data.capabilities.cancelRun}
            pending={pendingAction === "cancel-run"}
            label="取消运行"
            pendingLabel="取消中"
            icon={<Square aria-hidden="true" />}
            onClick={() => openActionDialog(cancelTriggerRef, setCancelOpen)}
          />
          <CapabilityButton
            capability={data.capabilities.createRun}
            pending={pendingAction === "create-run"}
            label="创建运行"
            pendingLabel="创建中"
            icon={<Play aria-hidden="true" />}
            variant="default"
            onClick={() => openActionDialog(createTriggerRef, setCreateOpen)}
          />
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            aria-label="打开运行检查器"
            title="打开运行检查器"
            onClick={openInspector}
          >
            <PanelRight aria-hidden="true" />
          </Button>
        </div>
      </header>

      <SafetyNotices data={data} />

      <nav className="m8-surface-tabs" aria-label="Agent 工作台表面">
        {surfaces.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              type="button"
              aria-current={surface === item.id ? "page" : undefined}
              onClick={() => changeSurface(item.id)}
            >
              <Icon aria-hidden="true" /> {item.label}
            </button>
          )
        })}
      </nav>

      <div className="m8-disabled-reasons" aria-label="不可用操作原因">
        {disabledReasons.map(([label, capability]) =>
          !capability.allowed && capability.reason ? (
            <span key={label}>
              <ShieldAlert aria-hidden="true" /> {label}：{capability.reason}
            </span>
          ) : null,
        )}
      </div>

      <div className="m8-workspace-grid">
        <div
          className={
            surface === "plan"
              ? "m8-mobile-active"
              : surface === "tools"
                ? "m8-plan-replaced"
                : ""
          }
          data-surface="plan"
        >
          <PlanPane data={data} />
        </div>
        <div
          className={
            surface === "timeline" || surface === "run"
              ? "m8-mobile-active"
              : ""
          }
          data-surface="timeline"
        >
          {surface === "run" ? (
            <section
              className="m8-run-overview"
              aria-labelledby="m8-run-overview-heading"
            >
              <header className="m8-pane-heading">
                <div>
                  <span>当前运行</span>
                  <h2 id="m8-run-overview-heading">Run 概览</h2>
                </div>
              </header>
              <RunInspector data={data} />
            </section>
          ) : (
            <TimelinePane
              data={data}
              pendingAction={pendingAction}
              onEvent={emit}
            />
          )}
        </div>
        <aside
          className="m8-inspector-pane"
          aria-labelledby="m8-inspector-heading"
        >
          <header className="m8-pane-heading">
            <div>
              <span>安全投影</span>
              <h2 id="m8-inspector-heading">运行检查器</h2>
            </div>
          </header>
          <WorkspaceInspector
            data={data}
            selectedToolCallId={selectedToolCallId}
            pendingAction={pendingAction}
            onEvent={emit}
          />
        </aside>
        <div
          className={surface === "tools" ? "m8-mobile-active" : ""}
          data-surface="tools"
        >
          <ToolsSurface
            data={data}
            selectedToolCallId={selectedToolCallId}
            onToolSelectionChange={setSelectedTool}
            onOpenInspector={openInspector}
          />
        </div>
      </div>

      {mutationError ? (
        <div className="m8-mutation-wrap">
          <MutationError
            title={mutationError.title}
            message={mutationError.message}
            code={mutationError.code}
            requestId={mutationError.requestId}
            retryable={mutationError.retryable}
            onRetry={onRetry}
          />
        </div>
      ) : null}

      <CreateRunDialog
        open={createOpen}
        capability={data.capabilities.createRun}
        pending={pendingAction === "create-run"}
        onOpenChange={(open) =>
          changeActionDialog(open, createTriggerRef, setCreateOpen)
        }
        onSubmit={(goal, allowToolCalls) =>
          emit({
            action: "create-run",
            input: { goal, mode: "PLAN_AND_EXPLAIN", allowToolCalls },
          })
        }
      />
      <CancelRunDialog
        open={cancelOpen}
        pending={pendingAction === "cancel-run"}
        onOpenChange={(open) =>
          changeActionDialog(open, cancelTriggerRef, setCancelOpen)
        }
        onConfirm={() =>
          run && emit({ action: "cancel-run", input: { runId: run.id } })
        }
      />
      <RetryRunDialog
        open={retryOpen}
        pending={pendingAction === "retry-or-restart"}
        onOpenChange={(open) =>
          changeActionDialog(open, retryTriggerRef, setRetryOpen)
        }
        onConfirm={() =>
          run &&
          emit({
            action: "retry-or-restart",
            input: { runId: run.id, goal: run.safeGoal ?? "" },
          })
        }
      />
      <Sheet open={inspectorOpen} onOpenChange={changeInspectorOpen}>
        <SheetContent
          className="m8-inspector-sheet"
          data-od-id="agent-run-inspector-sheet"
        >
          <SheetHeader>
            <SheetTitle>Tool / Run 检查器</SheetTitle>
            <SheetDescription>
              只读展示服务端投影；本地选择不会改变正式状态。
            </SheetDescription>
          </SheetHeader>
          <WorkspaceInspector
            data={data}
            selectedToolCallId={selectedToolCallId}
            pendingAction={pendingAction}
            onEvent={emit}
          />
        </SheetContent>
      </Sheet>
    </main>
  )
}
