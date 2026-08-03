import {
  BookOpenCheck,
  ClipboardList,
  FileText,
  FlaskConical,
  FolderKanban,
  ListTree,
  Monitor,
  Moon,
  PanelRightClose,
  PanelRightOpen,
  RotateCcw,
  Smartphone,
  Sun,
  Tablet,
  Trash2,
} from "lucide-react"
import { type ReactNode, useEffect, useMemo, useRef, useState } from "react"

import { VisualThemeProvider } from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"
import { documentFixtures } from "@/features/documents/fixtures"
import { DocumentWorkspace } from "@/features/documents/ui/DocumentWorkspace"
import { literatureFixtures } from "@/features/literature/fixtures"
import { LiteratureWorkspace } from "@/features/literature/ui/LiteratureWorkspace"
import { projectWorkspaceFixtures } from "@/features/projects/fixtures"
import { queryPlanFixtures } from "@/features/query-plan/fixtures"
import { QueryPlanWorkspace } from "@/features/query-plan/ui/QueryPlanWorkspace"
import { researchQuestionFixtures } from "@/features/research-question/fixtures"
import type { ResearchQuestionWorkspaceProps } from "@/features/research-question/ui/contracts"
import { ResearchQuestionWorkspace } from "@/features/research-question/ui/ResearchQuestionWorkspace"
import { ProjectWorkspacePreview } from "./ProjectWorkspacePreview"
import { VisualFoundationsPreview } from "./VisualFoundationsPreview"

type ModuleId =
  | "foundations"
  | "query-plan"
  | "literature"
  | "document"
  | "research-question"
  | "project-workspace"
type ThemeChoice = "light" | "dark" | "system"
type ViewportChoice = "desktop" | "tablet" | "mobile"

type EventEntry = {
  id: number
  module: ModuleId
  action: string
  time: string
  summary: unknown
}

const modules: ReadonlyArray<{
  id: ModuleId
  label: string
  icon: typeof FlaskConical
}> = [
  { id: "foundations", label: "Foundations", icon: FlaskConical },
  { id: "query-plan", label: "Query Plan", icon: ListTree },
  { id: "literature", label: "Literature", icon: BookOpenCheck },
  { id: "document", label: "Document", icon: FileText },
  { id: "research-question", label: "Research Question", icon: ClipboardList },
  { id: "project-workspace", label: "Project Workspace", icon: FolderKanban },
]

const viewportOptions: ReadonlyArray<{
  id: ViewportChoice
  label: string
  size: string
  width: number
  height: number
  icon: typeof Monitor
}> = [
  {
    id: "desktop",
    label: "桌面",
    size: "1440 × 900",
    width: 1440,
    height: 900,
    icon: Monitor,
  },
  {
    id: "tablet",
    label: "平板",
    size: "1024 × 768",
    width: 1024,
    height: 768,
    icon: Tablet,
  },
  {
    id: "mobile",
    label: "移动",
    size: "390 × 844",
    width: 390,
    height: 844,
    icon: Smartphone,
  },
]

const queryPlanFixtureOptions = queryPlanFixtures
const literatureFixtureOptions = literatureFixtures
const documentFixtureOptions = documentFixtures

const defaultFixtureIds: Record<ModuleId, string> = {
  foundations: "visual-foundations",
  "query-plan": queryPlanFixtureOptions[0].id,
  literature: literatureFixtureOptions[0].id,
  document: documentFixtureOptions[0].id,
  "research-question": researchQuestionFixtures[0].id,
  "project-workspace": projectWorkspaceFixtures[0].id,
}

const moduleStatus: Record<
  ModuleId,
  ReadonlyArray<{ label: string; state: "ready" | "pending" }>
> = {
  foundations: [
    { label: "Token ready", state: "ready" },
    { label: "Shared UI ready", state: "ready" },
  ],
  "query-plan": [
    { label: "Workspace ready", state: "ready" },
    { label: "Fixture ready", state: "ready" },
    { label: "integration pending", state: "pending" },
  ],
  literature: [
    { label: "Workspace ready", state: "ready" },
    { label: "Fixture ready", state: "ready" },
    { label: "integration pending", state: "pending" },
  ],
  document: [
    { label: "Workspace ready", state: "ready" },
    { label: "Fixture ready", state: "ready" },
    { label: "integration pending", state: "pending" },
  ],
  "research-question": [
    { label: "Workspace ready", state: "ready" },
    { label: "Fixture ready", state: "ready" },
    { label: "integration pending", state: "pending" },
  ],
  "project-workspace": [
    { label: "Workspace panels ready", state: "ready" },
    { label: "Fixture ready", state: "ready" },
    { label: "integration pending", state: "pending" },
  ],
}

function fixtureOptionsFor(
  module: ModuleId,
): ReadonlyArray<{ id: string; label: string }> {
  if (module === "query-plan") return queryPlanFixtureOptions
  if (module === "literature") return literatureFixtureOptions
  if (module === "document") return documentFixtureOptions
  if (module === "research-question") return researchQuestionFixtures
  if (module === "project-workspace") return projectWorkspaceFixtures
  return [{ id: "visual-foundations", label: "共享视觉基础" }]
}

function maskIdentifier(value: string) {
  if (value.length <= 10) return `${value.slice(0, 3)}…`
  return `${value.slice(0, 6)}…${value.slice(-4)}`
}

function summarizeInput(value: unknown, key = "input"): unknown {
  if (typeof File !== "undefined" && value instanceof File) {
    return { name: value.name, size: value.size, mime: value.type || "未知" }
  }
  if (Array.isArray(value)) return { count: value.length }
  if (typeof value === "string") {
    if (/id$/i.test(key)) return maskIdentifier(value)
    if (key === "documentType") return value
    return { kind: "text", length: value.length }
  }
  if (typeof value === "number" || typeof value === "boolean" || value == null)
    return value
  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .slice(0, 8)
        .map(([childKey, childValue]) => [
          childKey,
          summarizeInput(childValue, childKey),
        ]),
    )
  }
  return { kind: typeof value }
}

export function DesignPreviewWorkbench() {
  const [module, setModule] = useState<ModuleId>("foundations")
  const [fixtureIds, setFixtureIds] = useState(defaultFixtureIds)
  const [themeChoice, setThemeChoice] = useState<ThemeChoice>("system")
  const [systemDark, setSystemDark] = useState(false)
  const [viewport, setViewport] = useState<ViewportChoice>("desktop")
  const [showEventLog, setShowEventLog] = useState(true)
  const [eventLog, setEventLog] = useState<EventEntry[]>([])
  const [renderKey, setRenderKey] = useState(0)
  const [stageWidth, setStageWidth] = useState(0)
  const stageRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const update = () => setSystemDark(media.matches)
    update()
    media.addEventListener("change", update)
    return () => media.removeEventListener("change", update)
  }, [])

  useEffect(() => {
    const stage = stageRef.current
    if (!stage) return

    const updateStageWidth = () => setStageWidth(stage.clientWidth)
    updateStageWidth()

    const observer = new ResizeObserver(updateStageWidth)
    observer.observe(stage)
    return () => observer.disconnect()
  }, [])

  const resolvedTheme =
    themeChoice === "system" ? (systemDark ? "dark" : "light") : themeChoice
  const currentModule = modules.find((item) => item.id === module) ?? modules[0]
  const fixtureOptions = fixtureOptionsFor(module)
  const currentFixtureId = fixtureIds[module]
  const currentViewport =
    viewportOptions.find((item) => item.id === viewport) ?? viewportOptions[0]
  const viewportScale =
    stageWidth > 0
      ? Math.min(1, Math.max(0.35, (stageWidth - 36) / currentViewport.width))
      : 1

  const logIntent = (action: string, input?: unknown) => {
    setEventLog((entries) =>
      [
        {
          id: Date.now() + entries.length,
          module,
          action,
          time: new Intl.DateTimeFormat("zh-CN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
          }).format(new Date()),
          summary: summarizeInput(input),
        },
        ...entries,
      ].slice(0, 50),
    )
  }

  const resetLocalState = () => {
    setFixtureIds({ ...defaultFixtureIds })
    setThemeChoice("system")
    setViewport("desktop")
    setShowEventLog(true)
    setEventLog([])
    setRenderKey((value) => value + 1)
  }

  const previewContent = useMemo<ReactNode>(() => {
    if (module === "foundations") return <VisualFoundationsPreview />
    if (module === "query-plan") {
      const fixture =
        queryPlanFixtureOptions.find((item) => item.id === currentFixtureId) ??
        queryPlanFixtureOptions[0]
      return (
        <QueryPlanWorkspace
          {...fixture.props}
          onRetry={() => logIntent("retry")}
          onEvent={(event) => logIntent(event.action, event.input)}
        />
      )
    }
    if (module === "literature") {
      const fixture =
        literatureFixtureOptions.find((item) => item.id === currentFixtureId) ??
        literatureFixtureOptions[0]
      return (
        <LiteratureWorkspace
          {...fixture.props}
          onRetry={() => logIntent("retry")}
          onEvent={(event) => logIntent(event.action, event.input)}
        />
      )
    }
    if (module === "document") {
      const fixture =
        documentFixtureOptions.find((item) => item.id === currentFixtureId) ??
        documentFixtureOptions[0]
      return (
        <DocumentWorkspace
          {...fixture.props}
          onRetry={() => logIntent("retry")}
          onEvent={(event) => logIntent(event.action, event.input)}
        />
      )
    }
    if (module === "research-question") {
      const fixture =
        researchQuestionFixtures.find((item) => item.id === currentFixtureId) ??
        researchQuestionFixtures[0]
      const props: ResearchQuestionWorkspaceProps = {
        ...fixture.props,
        onRetry: () => logIntent("retry"),
        onEvent: (event) => logIntent(event.action, event.input),
      }
      return <ResearchQuestionWorkspace {...props} />
    }
    const fixture =
      projectWorkspaceFixtures.find((item) => item.id === currentFixtureId) ??
      projectWorkspaceFixtures[0]
    return <ProjectWorkspacePreview fixture={fixture} onIntent={logIntent} />
  }, [currentFixtureId, module])

  return (
    <div className="preview-workbench" data-od-id="design-preview-workbench">
      <aside className="preview-sidebar" data-od-id="preview-module-navigation">
        <div className="preview-brand">
          <span>RECA</span>
          <small>Design Preview</small>
        </div>
        <nav aria-label="设计预览模块">
          {modules.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                type="button"
                aria-current={module === item.id ? "page" : undefined}
                onClick={() => setModule(item.id)}
              >
                <Icon aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
        <div className="preview-dev-note">
          <span>DEV ONLY</span>
          <p>fixture 与设计说明不会进入生产 Workspace。</p>
        </div>
      </aside>

      <div className="preview-main">
        <header className="preview-toolbar" data-od-id="preview-toolbar">
          <div className="preview-toolbar__module">
            <span>当前模块</span>
            <strong>{currentModule.label}</strong>
          </div>
          <label className="preview-field">
            <span>Fixture</span>
            <select
              value={currentFixtureId}
              onChange={(event) =>
                setFixtureIds((value) => ({
                  ...value,
                  [module]: event.target.value,
                }))
              }
            >
              {fixtureOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <div className="preview-segment" aria-label="预览主题">
            {(["light", "dark", "system"] as const).map((choice) => {
              const Icon =
                choice === "light" ? Sun : choice === "dark" ? Moon : Monitor
              return (
                <button
                  key={choice}
                  type="button"
                  aria-pressed={themeChoice === choice}
                  onClick={() => setThemeChoice(choice)}
                  title={
                    choice === "light"
                      ? "浅色"
                      : choice === "dark"
                        ? "深色"
                        : "跟随系统"
                  }
                >
                  <Icon aria-hidden="true" />
                  <span>
                    {choice === "light"
                      ? "浅色"
                      : choice === "dark"
                        ? "深色"
                        : "系统"}
                  </span>
                </button>
              )
            })}
          </div>
          <div className="preview-segment" aria-label="模拟宽度">
            {viewportOptions.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={viewport === item.id}
                  onClick={() => setViewport(item.id)}
                  title={`${item.label} ${item.size}`}
                >
                  <Icon aria-hidden="true" />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </div>
          <div className="preview-toolbar__actions">
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              aria-label="重置本地界面状态"
              title="重置本地界面状态"
              onClick={resetLocalState}
            >
              <RotateCcw aria-hidden="true" />
            </Button>
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              aria-label={showEventLog ? "隐藏 Event Log" : "显示 Event Log"}
              title={showEventLog ? "隐藏 Event Log" : "显示 Event Log"}
              aria-pressed={showEventLog}
              onClick={() => setShowEventLog((value) => !value)}
            >
              {showEventLog ? (
                <PanelRightClose aria-hidden="true" />
              ) : (
                <PanelRightOpen aria-hidden="true" />
              )}
            </Button>
          </div>
        </header>

        <div className="preview-content">
          <main
            ref={stageRef}
            className="preview-stage"
            data-od-id="preview-stage"
          >
            <div
              className="preview-stage__ruler"
              style={{ width: currentViewport.width * viewportScale }}
            >
              <span>
                {currentViewport.size} · {Math.round(viewportScale * 100)}%
              </span>
              <span>等比适配预览区；最终验收使用真实 Playwright viewport</span>
            </div>
            <div
              className="preview-stage__canvas"
              style={{
                width: currentViewport.width * viewportScale,
                height: currentViewport.height * viewportScale,
              }}
            >
              <div
                className={`preview-stage__viewport preview-stage__viewport--${viewport}`}
                style={{ transform: `scale(${viewportScale})` }}
                role="region"
                aria-label={`${currentViewport.label}预览，${currentViewport.size}`}
              >
                <VisualThemeProvider theme={resolvedTheme}>
                  <div
                    key={`${module}-${currentFixtureId}-${renderKey}`}
                    className="preview-product-surface"
                    data-module={module}
                  >
                    {previewContent}
                  </div>
                </VisualThemeProvider>
              </div>
            </div>
          </main>

          <aside className="preview-inspector" data-od-id="preview-inspector">
            <section>
              <div className="preview-inspector__heading">
                <h2>设计状态</h2>
              </div>
              <div className="preview-status-list">
                {moduleStatus[module].map((item) => (
                  <span key={item.label} data-state={item.state}>
                    {item.state === "ready" ? "已就绪" : "待处理"} ·{" "}
                    {item.label}
                  </span>
                ))}
              </div>
            </section>
            <section>
              <div className="preview-inspector__heading">
                <h2>边界说明</h2>
              </div>
              <p>
                Preview 仅渲染现有正式 Workspace/Panel 与 typed
                fixture。事件只记录意图，不改变 fixture、权限、Job、Approval
                或正式状态。
              </p>
            </section>
            {showEventLog ? (
              <section className="preview-event-log">
                <div className="preview-inspector__heading">
                  <h2>Event Log</h2>
                  <button
                    type="button"
                    onClick={() => setEventLog([])}
                    disabled={eventLog.length === 0}
                  >
                    <Trash2 aria-hidden="true" />
                    清空
                  </button>
                </div>
                {eventLog.length === 0 ? (
                  <p className="preview-event-log__empty">尚未触发事件。</p>
                ) : (
                  <ol aria-live="polite">
                    {eventLog.map((entry) => (
                      <li key={entry.id}>
                        <div>
                          <strong>{entry.action}</strong>
                          <time>{entry.time}</time>
                        </div>
                        <span>
                          {
                            modules.find((item) => item.id === entry.module)
                              ?.label
                          }
                        </span>
                        <pre>{JSON.stringify(entry.summary, null, 2)}</pre>
                      </li>
                    ))}
                  </ol>
                )}
              </section>
            ) : null}
          </aside>
        </div>
      </div>
    </div>
  )
}
