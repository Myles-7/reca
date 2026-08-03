import {
  Ban,
  CircleAlert,
  FileQuestion,
  LoaderCircle,
  ShieldAlert,
  TriangleAlert,
} from "lucide-react"
import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"

export function DegradedNotice({
  title = "结果已降级",
  message,
}: {
  title?: string
  message: string
}) {
  return (
    <div className="reca-notice reca-notice--degraded" role="status">
      <TriangleAlert aria-hidden="true" />
      <div>
        <div className="reca-notice__title">{title}</div>
        <p className="reca-notice__message">{message}</p>
      </div>
    </div>
  )
}

export function PermissionNotice({
  title = "当前操作不可用",
  reason,
}: {
  title?: string
  reason: string
}) {
  return (
    <div className="reca-notice reca-notice--permission" role="status">
      <ShieldAlert aria-hidden="true" />
      <div>
        <div className="reca-notice__title">{title}</div>
        <p className="reca-notice__message">{reason}</p>
      </div>
    </div>
  )
}

export function MutationError({
  title = "操作未完成",
  message,
  code,
  requestId,
  retryable = false,
  onRetry,
}: {
  title?: string
  message: string
  code?: string | null
  requestId?: string | null
  retryable?: boolean
  onRetry?: () => void
}) {
  return (
    <div className="reca-mutation-error" role="alert" aria-live="polite">
      <CircleAlert aria-hidden="true" />
      <div>
        <div className="reca-mutation-error__title">{title}</div>
        <p className="reca-mutation-error__message">{message}</p>
        {code || requestId ? (
          <p className="reca-mutation-error__message">
            {[code, requestId].filter(Boolean).join(" · ")}
          </p>
        ) : null}
        {retryable && onRetry ? (
          <div className="reca-mutation-error__action">
            <Button type="button" size="sm" variant="outline" onClick={onRetry}>
              重试
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  )
}

export function EmptyState({
  title,
  message,
  action,
}: {
  title: string
  message: string
  action?: ReactNode
}) {
  return (
    <div className="reca-empty-state" role="status">
      <FileQuestion aria-hidden="true" />
      <div>
        <div className="reca-state__title">{title}</div>
        <p className="reca-state__message">{message}</p>
        {action ? <div className="reca-state__action">{action}</div> : null}
      </div>
    </div>
  )
}

export type DisplayLoadableState =
  | "loading"
  | "empty"
  | "error"
  | "forbidden"
  | "ready"
  | string

export type WorkspaceSkeletonLayout = "project" | "dual-pane" | "three-pane"

export function WorkspaceLoadingFrame({
  layout,
  children,
}: {
  layout: WorkspaceSkeletonLayout
  children: ReactNode
}) {
  const paneCount = layout === "three-pane" ? 3 : layout === "dual-pane" ? 2 : 1
  const primaryIndex = layout === "three-pane" ? 1 : 0

  return (
    <div className="reca-workspace-skeleton" data-layout={layout}>
      {Array.from({ length: paneCount }, (_, index) => (
        <section
          key={index}
          className="reca-workspace-skeleton__pane"
          data-primary={index === primaryIndex}
          aria-hidden={index !== primaryIndex}
        >
          <div className="reca-workspace-skeleton__toolbar" aria-hidden="true">
            <span />
            <span />
          </div>
          {index === primaryIndex ? (
            children
          ) : (
            <div className="reca-workspace-skeleton__rows" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
          )}
        </section>
      ))}
    </div>
  )
}

export function WorkspaceLoadingSkeleton({
  layout,
  state,
  title,
  message,
  action,
}: {
  layout: WorkspaceSkeletonLayout
  state: DisplayLoadableState
  title?: string
  message?: string
  action?: ReactNode
}) {
  return (
    <WorkspaceLoadingFrame layout={layout}>
      <LoadableState
        state={state}
        title={title}
        message={message}
        action={action}
      />
    </WorkspaceLoadingFrame>
  )
}

export function LoadableState({
  state,
  title,
  message,
  children,
  action,
}: {
  state: DisplayLoadableState
  title?: string
  message?: string
  children?: ReactNode
  action?: ReactNode
}) {
  if (state === "ready") {
    return <div className="reca-loadable-state--ready">{children}</div>
  }

  if (state === "empty") {
    return (
      <EmptyState
        title={title ?? "暂无内容"}
        message={message ?? "当前范围内没有可显示的数据。"}
        action={action}
      />
    )
  }

  const isLoading = state === "loading"
  const isForbidden = state === "forbidden"
  const isError = state === "error"
  const Icon = isLoading ? LoaderCircle : isForbidden ? Ban : TriangleAlert
  const fallbackTitle = isLoading
    ? "正在加载"
    : isForbidden
      ? "无权查看"
      : state === "error"
        ? "加载失败"
        : "状态未知"
  const fallbackMessage = isLoading
    ? "正在读取服务端结果，布局将保持稳定。"
    : isForbidden
      ? "服务端未授权访问此内容。"
      : state === "error"
        ? "请求未能完成，请查看错误详情。"
        : "该状态未被当前展示契约识别，写操作保持禁用。"

  return (
    <div
      className="reca-loadable-state"
      role={isForbidden || isError ? "alert" : "status"}
      aria-live="polite"
    >
      <Icon aria-hidden="true" />
      <div>
        <div className="reca-state__title">{title ?? fallbackTitle}</div>
        <p className="reca-state__message">{message ?? fallbackMessage}</p>
        {isLoading ? (
          <div className="reca-loading-lines" aria-hidden="true">
            <span />
            <span />
          </div>
        ) : null}
        {action ? <div className="reca-state__action">{action}</div> : null}
      </div>
    </div>
  )
}
