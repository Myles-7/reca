import {
  Background,
  Controls,
  type Edge,
  MarkerType,
  type Node,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import {
  AlertTriangle,
  ArrowDownUp,
  Ban,
  BrainCircuit,
  Check,
  ChevronRight,
  CircleHelp,
  Clipboard,
  Clock3,
  Download,
  FileCheck2,
  FileClock,
  FileJson2,
  FolderArchive,
  GitBranch,
  HardDriveDownload,
  Link2,
  List,
  LockKeyhole,
  Maximize2,
  Network,
  PackageCheck,
  PanelRightOpen,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldAlert,
  Table2,
  TriangleAlert,
  XCircle,
} from "lucide-react"
import { useEffect, useState } from "react"

import {
  DegradedNotice,
  EmptyState,
  InspectorSection,
  MetadataList,
  MutationError,
  PermissionNotice,
  StatusBadge,
  useVisualTheme,
  WorkspaceHeader,
  WorkspaceLoadingSkeleton,
} from "@/components/reca-visual-refresh"
import "@/components/reca-visual-refresh/visual-refresh.css"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type {
  ClaimCompletenessViewModel,
  EvidenceGraphEdgeViewModel,
  EvidenceGraphNodeViewModel,
  EvidenceLinkViewModel,
  EvidenceRisk,
  EvidenceScope,
  EvidenceWorkspaceView,
  EvidenceWorkspaceViewModel,
  ExportCandidateViewModel,
} from "../model"
import type {
  EvidenceLinkInput,
  EvidenceWorkspaceEvent,
  EvidenceWorkspaceProps,
  ReproPackageInput,
} from "./contracts"
import "./evidence-workspace.css"

export type EvidenceGraphMode = "graph" | "table"

export type EvidenceWorkspaceVisualProps = EvidenceWorkspaceProps & {
  graphMode?: EvidenceGraphMode
  onGraphModeChange?: (mode: EvidenceGraphMode) => void
}

type Selection =
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string }
  | { kind: "link"; id: string }
  | null

const viewLabels: Record<EvidenceWorkspaceView, string> = {
  graph: "证据图谱",
  claims: "主张复核",
  audits: "审计",
  exports: "导出",
}

const scopeLabels: Record<EvidenceScope, string> = {
  AVAILABLE: "可访问",
  DENIED: "受限",
  MISSING: "缺失",
  STALE: "陈旧",
  UNKNOWN: "未知",
}

const semanticLabels = {
  SUPPORT: "支持",
  CONTRADICT: "反驳",
  QUALIFY: "限定",
  PROVENANCE: "来源链",
  UNKNOWN: "未知关系",
} as const

function statusTone(status: string, known = true) {
  if (!known) return "unknown"
  if (["ACTIVE", "AVAILABLE", "SATISFIED", "SUPPORTED"].includes(status))
    return "success"
  if (["MISSING", "STALE", "SUGGESTED", "RESTRICTED"].includes(status))
    return "warning"
  if (["INVALIDATED", "CONFLICTED", "REJECTED"].includes(status))
    return "danger"
  return "neutral"
}

function graphNodeTone(node: EvidenceGraphNodeViewModel) {
  if (!node.knownStatus || node.scope === "UNKNOWN") return "unknown"
  if (node.invalidated || node.risk === "HIGH") return "danger"
  if (node.stale || node.scope === "STALE" || node.risk === "MEDIUM")
    return "warning"
  return "evidence"
}

function edgeTone(edge: EvidenceGraphEdgeViewModel) {
  if (!edge.knownStatus || edge.semantic === "UNKNOWN") return "unknown"
  if (edge.invalidated || edge.semantic === "CONTRADICT") return "danger"
  if (edge.semantic === "QUALIFY") return "warning"
  return edge.sourceKind === "STORED" ? "evidence" : "neutral"
}

function shortId(value: string) {
  if (value.length <= 18) return value
  return `${value.slice(0, 10)}…${value.slice(-6)}`
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

function safeValue(value: unknown) {
  if (value === null) return "null"
  if (value === undefined) return "未提供"
  if (typeof value === "string") return value
  if (typeof value === "number" || typeof value === "boolean")
    return String(value)
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return "无法安全显示的结构化值"
  }
}

function CopyButton({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <IconButton
      label={copied ? "已复制" : label}
      onClick={() => {
        void navigator.clipboard?.writeText(value).then(() => {
          setCopied(true)
          window.setTimeout(() => setCopied(false), 1200)
        })
      }}
    >
      {copied ? <Check aria-hidden="true" /> : <Clipboard aria-hidden="true" />}
    </IconButton>
  )
}

function DisabledReason({
  show,
  children,
}: {
  show: boolean
  children: string
}) {
  if (!show) return null
  return (
    <small className="m7-disabled-reason" role="note">
      <CircleHelp aria-hidden="true" />
      {children}
    </small>
  )
}

function IconButton({
  label,
  children,
  ...props
}: React.ComponentProps<typeof Button> & { label: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          aria-label={label}
          {...props}
        >
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}

function toFlowNodes(data: EvidenceWorkspaceViewModel): Node[] {
  return data.graph.canvasNodes.map((node) => ({
    id: node.id,
    position: node.position,
    data: { label: node.data.label },
    draggable: node.draggable,
    selectable: node.selectable,
    connectable: node.connectable,
    className: `m7-flow-node m7-flow-node--${node.data.nodeType.toLowerCase()}`,
  }))
}

function toFlowEdges(data: EvidenceWorkspaceViewModel): Edge[] {
  return data.graph.canvasEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    selectable: edge.selectable,
    reconnectable: edge.reconnectable,
    label: `${semanticLabels[edge.data.semantic]} · ${edge.data.sourceKind === "STORED" ? "已存 Link" : "派生来源"}`,
    markerEnd: { type: MarkerType.ArrowClosed },
    className: `m7-flow-edge m7-flow-edge--${edge.data.semantic.toLowerCase()} m7-flow-edge--${edge.data.sourceKind.toLowerCase()}`,
  }))
}

function GraphCanvas({
  data,
  selection,
  onSelection,
}: {
  data: EvidenceWorkspaceViewModel
  selection: Selection
  onSelection: (selection: Selection) => void
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState(toFlowNodes(data))
  const [edges, setEdges, onEdgesChange] = useEdgesState(toFlowEdges(data))

  useEffect(() => setNodes(toFlowNodes(data)), [data, setNodes])
  useEffect(() => setEdges(toFlowEdges(data)), [data, setEdges])

  if (data.graph.nodes.length === 0) {
    return (
      <div className="m7-graph-empty">
        <EmptyState
          title="当前范围没有图谱节点"
          message="这是已授权范围的空结果，不代表存在被隐藏的对象。"
        />
      </div>
    )
  }

  return (
    <div className="m7-graph-canvas" data-od-id="evidence-graph-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onSelection({ kind: "node", id: node.id })}
        onEdgeClick={(_, edge) => onSelection({ kind: "edge", id: edge.id })}
        onPaneClick={() => onSelection(null)}
        nodesConnectable={false}
        edgesReconnectable={false}
        elementsSelectable
        fitView
        fitViewOptions={{ padding: 0.18, maxZoom: 1.1 }}
        minZoom={0.08}
        maxZoom={1.7}
        onlyRenderVisibleElements
        aria-label="证据图谱画布"
      >
        <Background gap={24} size={1} />
        <Controls showInteractive={false} position="bottom-right" />
      </ReactFlow>
      <div className="m7-canvas-legend" aria-label="图谱关系图例">
        <span>
          <Link2 aria-hidden="true" />
          已存 Link
        </span>
        <span>
          <GitBranch aria-hidden="true" />
          派生来源
        </span>
        <span>
          <AlertTriangle aria-hidden="true" />
          反驳/风险
        </span>
      </div>
      {selection ? <span className="sr-only">已选择图谱元素</span> : null}
    </div>
  )
}

function GraphTable({
  data,
  selection,
  onSelection,
}: {
  data: EvidenceWorkspaceViewModel
  selection: Selection
  onSelection: (selection: Selection) => void
}) {
  return (
    <div className="m7-fallback" data-od-id="evidence-graph-table-fallback">
      <section aria-labelledby="m7-node-table-title">
        <div className="m7-table-heading">
          <h3 id="m7-node-table-title">节点</h3>
          <span>{data.graph.nodes.length} 条授权记录</span>
        </div>
        <div className="m7-table-scroll">
          <table>
            <thead>
              <tr>
                <th>对象</th>
                <th>类型</th>
                <th>状态</th>
                <th>风险</th>
                <th>范围</th>
              </tr>
            </thead>
            <tbody>
              {data.graph.nodes.map((node) => (
                <tr
                  key={node.id}
                  tabIndex={0}
                  aria-selected={
                    selection?.kind === "node" && selection.id === node.id
                  }
                  onClick={() => onSelection({ kind: "node", id: node.id })}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault()
                      onSelection({ kind: "node", id: node.id })
                    }
                  }}
                >
                  <td>
                    <strong>{node.label}</strong>
                    <small>{shortId(node.id)}</small>
                  </td>
                  <td>{node.nodeType}</td>
                  <td>
                    <StatusBadge
                      label={
                        node.knownStatus ? node.status : `未知 · ${node.status}`
                      }
                      tone={graphNodeTone(node)}
                    />
                  </td>
                  <td>{node.risk}</td>
                  <td>
                    {scopeLabels[node.scope]}
                    {node.stale ? " · 陈旧" : ""}
                    {node.invalidated ? " · 已失效" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section aria-labelledby="m7-edge-table-title">
        <div className="m7-table-heading">
          <h3 id="m7-edge-table-title">关系</h3>
          <span>{data.graph.edges.length} 条投影关系</span>
        </div>
        <div className="m7-table-scroll">
          <table>
            <thead>
              <tr>
                <th>语义</th>
                <th>来源类型</th>
                <th>关系</th>
                <th>状态</th>
                <th>风险</th>
              </tr>
            </thead>
            <tbody>
              {data.graph.edges.map((edge) => (
                <tr
                  key={edge.id}
                  tabIndex={0}
                  aria-selected={
                    selection?.kind === "edge" && selection.id === edge.id
                  }
                  onClick={() => onSelection({ kind: "edge", id: edge.id })}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault()
                      onSelection({ kind: "edge", id: edge.id })
                    }
                  }}
                >
                  <td>
                    <StatusBadge
                      label={semanticLabels[edge.semantic]}
                      tone={edgeTone(edge)}
                    />
                  </td>
                  <td>
                    {edge.sourceKind === "STORED"
                      ? "已存 Link"
                      : edge.sourceKind === "DERIVED"
                        ? "派生来源"
                        : "未知"}
                  </td>
                  <td>{edge.relationType}</td>
                  <td>
                    {edge.knownStatus ? edge.status : `未知 · ${edge.status}`}
                    {edge.invalidated ? " · 已失效" : ""}
                  </td>
                  <td>{edge.risk}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function GraphNotices({ data }: { data: EvidenceWorkspaceViewModel }) {
  return (
    <div className="m7-notice-stack">
      {data.graph.partial ? (
        <div
          className="m7-inline-notice m7-inline-notice--warning"
          role="status"
        >
          <ArrowDownUp aria-hidden="true" />
          <span>
            当前图谱为部分结果{data.graph.nextCursor ? "，存在后续游标" : ""}。
          </span>
        </div>
      ) : null}
      {data.graph.degraded ? (
        <DegradedNotice message="图谱投影已降级；已显示的确定性关系仍保留。" />
      ) : null}
      {data.graph.limitations.map((item) => (
        <div className="m7-inline-notice" role="status" key={item}>
          <CircleHelp aria-hidden="true" />
          <span>{item}</span>
        </div>
      ))}
      {data.scopeNotices.map((notice, index) => (
        <div
          className="m7-inline-notice m7-inline-notice--scope"
          role="status"
          key={`${notice.scope}-${index}`}
        >
          <ShieldAlert aria-hidden="true" />
          <span>
            {scopeLabels[notice.scope]}：{notice.message}
          </span>
        </div>
      ))}
    </div>
  )
}

function Inspector({
  data,
  selection,
  onEvent,
}: {
  data: EvidenceWorkspaceViewModel
  selection: Selection
  onEvent: (event: EvidenceWorkspaceEvent) => void
}) {
  const node =
    selection?.kind === "node"
      ? data.graph.nodes.find((item) => item.id === selection.id)
      : null
  const edge =
    selection?.kind === "edge"
      ? data.graph.edges.find((item) => item.id === selection.id)
      : null
  const link =
    selection?.kind === "link"
      ? data.links.find((item) => item.id === selection.id)
      : data.selectedLink
  const expandAllowed = Boolean(data.permissionsKnown && node?.knownStatus)

  if (node) {
    return (
      <div className="m7-inspector-body">
        <InspectorSection title="选中节点">
          <div className="m7-inspector-title">
            <Network aria-hidden="true" />
            <strong>{node.label}</strong>
          </div>
          <div className="m7-badge-row">
            <StatusBadge
              label={node.knownStatus ? node.status : `未知 · ${node.status}`}
              tone={graphNodeTone(node)}
            />
            <StatusBadge
              label={node.risk}
              tone={
                node.risk === "HIGH"
                  ? "danger"
                  : node.risk === "MEDIUM"
                    ? "warning"
                    : "neutral"
              }
            />
          </div>
        </InspectorSection>
        <InspectorSection title="对象事实">
          <MetadataList
            items={[
              { label: "类型", value: node.nodeType },
              { label: "对象 ID", value: node.objectId, mono: true },
              { label: "来源", value: node.sourceKind },
              { label: "范围", value: scopeLabels[node.scope] },
              {
                label: "位置提示",
                value: `${node.lane ?? "未指定"} / ${node.rank ?? "未指定"}`,
              },
            ]}
          />
        </InspectorSection>
        {node.limitations.length ? (
          <InspectorSection title="限制">
            <ul className="m7-plain-list">
              {node.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </InspectorSection>
        ) : null}
        <div className="m7-inspector-actions">
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={!expandAllowed}
            title={
              expandAllowed ? "请求服务端扩展此节点" : "权限或节点状态未知"
            }
            onClick={() =>
              onEvent({ action: "expand-graph-node", nodeId: node.id })
            }
          >
            <Maximize2 aria-hidden="true" />
            扩展节点
          </Button>
        </div>
      </div>
    )
  }

  if (edge) {
    return (
      <div className="m7-inspector-body">
        <InspectorSection title="选中关系">
          <div className="m7-badge-row">
            <StatusBadge
              label={semanticLabels[edge.semantic]}
              tone={edgeTone(edge)}
            />
            <StatusBadge
              label={edge.sourceKind === "STORED" ? "已存 Link" : "派生来源"}
              tone={edge.sourceKind === "STORED" ? "evidence" : "neutral"}
            />
          </div>
        </InspectorSection>
        <InspectorSection title="关系事实">
          <MetadataList
            items={[
              { label: "关系", value: edge.relationType },
              { label: "强度", value: edge.strength ?? "不适用" },
              {
                label: "状态",
                value: edge.knownStatus ? edge.status : `未知 · ${edge.status}`,
              },
              { label: "来源节点", value: edge.source, mono: true },
              { label: "目标节点", value: edge.target, mono: true },
            ]}
          />
        </InspectorSection>
      </div>
    )
  }

  if (link) return <LinkInspector link={link} />

  return (
    <div className="m7-inspector-empty">
      <PanelRightOpen aria-hidden="true" />
      <p>选择节点、关系或 Link 查看正式投影事实。</p>
    </div>
  )
}

function LinkInspector({ link }: { link: EvidenceLinkViewModel }) {
  return (
    <div className="m7-inspector-body">
      <InspectorSection title="存储 Link">
        <div className="m7-badge-row">
          <StatusBadge
            label={link.knownStatus ? link.status : `未知 · ${link.status}`}
            tone={statusTone(link.status, link.knownStatus)}
          />
          <StatusBadge
            label={semanticLabels[link.semantic]}
            tone={edgeTone({
              ...link,
              source: "",
              target: "",
              risk: "LOW",
              sourceKind: "STORED",
            })}
          />
        </div>
      </InspectorSection>
      <InspectorSection title="证据引用">
        <MetadataList
          items={[
            { label: "对象", value: link.evidence.label },
            { label: "类型", value: link.evidence.objectType },
            { label: "范围", value: scopeLabels[link.evidence.scope] },
            { label: "关系", value: link.relationType },
            { label: "强度", value: link.strength },
            { label: "锁版本", value: link.lockVersion },
          ]}
        />
      </InspectorSection>
      {link.explanation ? (
        <InspectorSection title="说明">
          <p className="m7-wrap">{link.explanation}</p>
        </InspectorSection>
      ) : null}
    </div>
  )
}

function ClaimQueue({ data }: { data: EvidenceWorkspaceViewModel }) {
  const [query, setQuery] = useState("")
  const [risk, setRisk] = useState<EvidenceRisk | "ALL">("ALL")
  const claims = data.claims.filter((claim) => {
    const matchesQuery = claim.label
      .toLocaleLowerCase()
      .includes(query.toLocaleLowerCase())
    return matchesQuery && (risk === "ALL" || claim.risk === risk)
  })
  return (
    <div className="m7-claim-queue">
      <div className="m7-pane-title">
        <div>
          <strong>主张队列</strong>
          <span>{data.claims.length} 条</span>
        </div>
      </div>
      <label className="m7-search">
        <Search aria-hidden="true" />
        <span className="sr-only">搜索主张</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="搜索主张"
        />
      </label>
      <label className="m7-filter">
        <span>风险</span>
        <select
          value={risk}
          onChange={(event) =>
            setRisk(event.target.value as EvidenceRisk | "ALL")
          }
        >
          <option value="ALL">全部</option>
          <option value="HIGH">高</option>
          <option value="MEDIUM">中</option>
          <option value="LOW">低</option>
          <option value="UNKNOWN">未知</option>
        </select>
      </label>
      <div className="m7-queue-list">
        {claims.map((claim) => (
          <button
            key={claim.id}
            type="button"
            className="m7-queue-item"
            aria-current={
              data.selectedClaim?.id === claim.id ? "true" : undefined
            }
          >
            <span className="m7-queue-item__top">
              <StatusBadge
                label={claim.risk}
                tone={
                  claim.risk === "HIGH"
                    ? "danger"
                    : claim.risk === "MEDIUM"
                      ? "warning"
                      : "neutral"
                }
              />
              <ChevronRight aria-hidden="true" />
            </span>
            <strong>{claim.label}</strong>
            <small>
              {claim.knownStatus ? claim.status : `未知 · ${claim.status}`}
              {claim.stale ? " · 陈旧" : ""}
              {claim.invalidated ? " · 已失效" : ""}
            </small>
          </button>
        ))}
        {claims.length === 0 ? (
          <p className="m7-queue-empty">没有匹配的主张。</p>
        ) : null}
      </div>
    </div>
  )
}

function Completeness({ value }: { value: ClaimCompletenessViewModel | null }) {
  if (!value)
    return (
      <EmptyState
        title="没有完整度投影"
        message="当前主张没有服务端完整度检查结果。"
      />
    )
  return (
    <section className="m7-completeness" data-od-id="claim-completeness">
      <div className="m7-section-heading">
        <div>
          <h3>证据完整度</h3>
          <p>规则版本 {value.ruleSetVersion}</p>
        </div>
        <StatusBadge label="分类检查，不是质量分" tone="neutral" />
      </div>
      <div className="m7-check-list">
        {value.items.map((item) => (
          <article key={item.code} className="m7-check-item">
            <div className="m7-check-item__icon">
              {item.status === "SATISFIED" ? (
                <Check aria-hidden="true" />
              ) : item.status === "CONFLICTED" ? (
                <XCircle aria-hidden="true" />
              ) : (
                <AlertTriangle aria-hidden="true" />
              )}
            </div>
            <div>
              <strong>{item.code}</strong>
              <div className="m7-badge-row">
                <StatusBadge
                  label={
                    item.knownStatus ? item.status : `未知 · ${item.status}`
                  }
                  tone={statusTone(item.status, item.knownStatus)}
                />
              </div>
              {item.limitations.map((text) => (
                <p key={text}>{text}</p>
              ))}
              {item.missingActions.map((text) => (
                <p key={text}>待办：{text}</p>
              ))}
            </div>
          </article>
        ))}
      </div>
      {value.limitations.length ? (
        <div className="m7-limitations">
          <strong>限制</strong>
          <ul>
            {value.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}

function CreateLinkDialog({
  data,
  onEvent,
}: {
  data: EvidenceWorkspaceViewModel
  onEvent: (event: EvidenceWorkspaceEvent) => void
}) {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState<EvidenceLinkInput>({
    claimId: data.selectedClaim?.id ?? "",
    evidenceObjectType: "EVIDENCE_SPAN",
    evidenceObjectId: "",
    relationType: "SUPPORTED_BY",
    strength: "MODERATE",
    suggestion: false,
  })
  const capability = data.capabilities.createEvidenceLink
  const allowed =
    data.permissionsKnown &&
    capability.allowed &&
    Boolean(data.selectedClaim?.knownStatus)
  return (
    <div className="m7-command-with-reason">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button
            type="button"
            size="sm"
            disabled={!allowed}
            title={
              allowed
                ? "创建证据 Link"
                : (capability.disabledReason ?? "权限或主张状态未知")
            }
          >
            <Plus aria-hidden="true" />
            创建 Link
          </Button>
        </DialogTrigger>
        <DialogContent
          className="m7-dialog"
          aria-describedby="m7-create-link-description"
        >
          <DialogHeader>
            <DialogTitle>创建证据 Link</DialogTitle>
            <DialogDescription id="m7-create-link-description">
              提交后等待服务端验证；关闭此窗口不会改变正式关系。
            </DialogDescription>
          </DialogHeader>
          <div className="m7-form-grid">
            <label>
              <span>证据类型</span>
              <select
                value={input.evidenceObjectType}
                onChange={(e) =>
                  setInput({ ...input, evidenceObjectType: e.target.value })
                }
              >
                <option>EVIDENCE_SPAN</option>
                <option>LITERATURE_RECORD</option>
                <option>DATASET_VERSION</option>
                <option>ANALYSIS_RESULT</option>
                <option>FIGURE</option>
              </select>
            </label>
            <label>
              <span>证据对象 ID</span>
              <input
                autoFocus
                value={input.evidenceObjectId}
                onChange={(e) =>
                  setInput({ ...input, evidenceObjectId: e.target.value })
                }
              />
            </label>
            <label>
              <span>关系</span>
              <select
                value={input.relationType}
                onChange={(e) =>
                  setInput({ ...input, relationType: e.target.value })
                }
              >
                <option>SUPPORTED_BY</option>
                <option>CONTRADICTED_BY</option>
                <option>DERIVED_FROM</option>
              </select>
            </label>
            <label>
              <span>强度</span>
              <select
                value={input.strength}
                onChange={(e) =>
                  setInput({ ...input, strength: e.target.value })
                }
              >
                <option>STRONG</option>
                <option>MODERATE</option>
                <option>WEAK</option>
                <option>UNKNOWN</option>
              </select>
            </label>
            <label className="m7-form-span">
              <span>说明（可选）</span>
              <textarea
                value={input.explanation ?? ""}
                onChange={(e) =>
                  setInput({ ...input, explanation: e.target.value })
                }
              />
            </label>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                取消
              </Button>
            </DialogClose>
            <Button
              type="button"
              disabled={!input.evidenceObjectId.trim()}
              onClick={() => {
                onEvent({ action: "create-evidence-link", input })
                setOpen(false)
              }}
            >
              提交意图
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <DisabledReason show={!allowed}>
        {capability.disabledReason ?? "权限或主张状态未知，创建 Link 已关闭。"}
      </DisabledReason>
    </div>
  )
}

function LinkActions({
  data,
  onEvent,
  onSelect,
}: {
  data: EvidenceWorkspaceViewModel
  onEvent: (event: EvidenceWorkspaceEvent) => void
  onSelect: (selection: Selection) => void
}) {
  const link = data.selectedLink
  const [invalidateOpen, setInvalidateOpen] = useState(false)
  const [reason, setReason] = useState("")
  if (!link) return null
  const confirmAllowed =
    data.permissionsKnown &&
    data.capabilities.confirmEvidenceLink.allowed &&
    link.knownStatus &&
    link.status === "SUGGESTED"
  const invalidateAllowed =
    data.permissionsKnown &&
    data.capabilities.invalidateEvidenceLink.allowed &&
    link.knownStatus &&
    link.status === "ACTIVE"
  return (
    <div className="m7-link-actions">
      <Button
        type="button"
        size="sm"
        variant="outline"
        onClick={() => onSelect({ kind: "link", id: link.id })}
      >
        查看 Link
      </Button>
      <Button
        type="button"
        size="sm"
        disabled={!confirmAllowed}
        title={
          confirmAllowed
            ? "确认建议 Link"
            : (data.capabilities.confirmEvidenceLink.disabledReason ??
              "Link 状态不允许确认")
        }
        onClick={() =>
          onEvent({
            action: "confirm-evidence-link",
            linkId: link.id,
            lockVersion: link.lockVersion,
          })
        }
      >
        确认
      </Button>
      <Dialog open={invalidateOpen} onOpenChange={setInvalidateOpen}>
        <DialogTrigger asChild>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={!invalidateAllowed}
            title={
              invalidateAllowed
                ? "失效 Link"
                : (data.capabilities.invalidateEvidenceLink.disabledReason ??
                  "Link 状态不允许失效")
            }
          >
            失效
          </Button>
        </DialogTrigger>
        <DialogContent className="m7-dialog">
          <DialogHeader>
            <DialogTitle>失效证据 Link</DialogTitle>
            <DialogDescription>
              历史关系会保留。必须提供原因，服务端决定正式状态。
            </DialogDescription>
          </DialogHeader>
          <label className="m7-dialog-field">
            <span>原因</span>
            <textarea
              autoFocus
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                取消
              </Button>
            </DialogClose>
            <Button
              type="button"
              variant="destructive"
              disabled={!reason.trim()}
              onClick={() => {
                onEvent({
                  action: "invalidate-evidence-link",
                  linkId: link.id,
                  lockVersion: link.lockVersion,
                  reason,
                })
                setInvalidateOpen(false)
                setReason("")
              }}
            >
              提交失效意图
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <DisabledReason show={!confirmAllowed && !invalidateAllowed}>
        {data.capabilities.confirmEvidenceLink.disabledReason ??
          data.capabilities.invalidateEvidenceLink.disabledReason ??
          "当前 Link 状态没有可用写操作。"}
      </DisabledReason>
    </div>
  )
}

function ClaimsView({
  data,
  selection,
  onSelection,
  onEvent,
}: {
  data: EvidenceWorkspaceViewModel
  selection: Selection
  onSelection: (selection: Selection) => void
  onEvent: (event: EvidenceWorkspaceEvent) => void
}) {
  const claim = data.selectedClaim
  const completeness = claim ? (data.completeness[claim.id] ?? null) : null
  return (
    <div className="m7-claims-surface" data-od-id="claims-main-surface">
      {!claim ? (
        <EmptyState
          title="未选择主张"
          message="从主张队列选择可访问的记录后查看证据与完整度。"
        />
      ) : (
        <>
          <section className="m7-claim-summary">
            <div className="m7-section-heading">
              <div>
                <span className="m7-eyebrow">{claim.claimType}</span>
                <h2>{claim.text}</h2>
              </div>
              <div className="m7-badge-row">
                <StatusBadge
                  label={
                    claim.knownStatus ? claim.status : `未知 · ${claim.status}`
                  }
                  tone={statusTone(claim.status, claim.knownStatus)}
                />
                {claim.stale ? (
                  <StatusBadge label="陈旧" tone="warning" />
                ) : null}
              </div>
            </div>
            <MetadataList
              items={[
                {
                  label: "来源对象",
                  value: `${claim.sourceObjectType} · ${shortId(claim.sourceObjectId)}`,
                },
                { label: "来源哈希", value: claim.sourceHash, mono: true },
                { label: "文本哈希", value: claim.textHash, mono: true },
                { label: "锁版本", value: claim.lockVersion },
              ]}
            />
          </section>
          <section className="m7-links-section">
            <div className="m7-section-heading">
              <div>
                <h3>存储 Link</h3>
                <p>关系记录与证据对象分开显示。</p>
              </div>
              <CreateLinkDialog data={data} onEvent={onEvent} />
            </div>
            <div className="m7-link-list">
              {data.links.map((link) => (
                <button
                  key={link.id}
                  type="button"
                  className="m7-link-row"
                  aria-current={
                    selection?.kind === "link" && selection.id === link.id
                      ? "true"
                      : undefined
                  }
                  onClick={() => onSelection({ kind: "link", id: link.id })}
                >
                  <span>
                    <StatusBadge
                      label={
                        link.knownStatus ? link.status : `未知 · ${link.status}`
                      }
                      tone={statusTone(link.status, link.knownStatus)}
                    />
                    <StatusBadge
                      label={semanticLabels[link.semantic]}
                      tone={
                        link.semantic === "CONTRADICT"
                          ? "danger"
                          : link.semantic === "QUALIFY"
                            ? "warning"
                            : "evidence"
                      }
                    />
                  </span>
                  <strong>{link.evidence.label}</strong>
                  <small>
                    {link.evidence.objectType} ·{" "}
                    {scopeLabels[link.evidence.scope]} · {link.strength}
                    {link.stale ? " · 陈旧" : ""}
                    {link.invalidated ? " · 已失效" : ""}
                  </small>
                </button>
              ))}
              {data.links.length === 0 ? (
                <EmptyState
                  title="没有存储 Link"
                  message="当前主张没有可显示的正式 Link 记录。"
                />
              ) : null}
            </div>
            <LinkActions data={data} onEvent={onEvent} onSelect={onSelection} />
          </section>
          <Completeness value={completeness} />
        </>
      )}
    </div>
  )
}

function AuditView({
  data,
  pendingAction,
  onEvent,
}: {
  data: EvidenceWorkspaceViewModel
  pendingAction: EvidenceWorkspaceEvent["action"] | null
  onEvent: (event: EvidenceWorkspaceEvent) => void
}) {
  const [requestAiExplanation, setRequestAiExplanation] = useState(false)
  const audit = data.audit
  const claim = data.selectedClaim
  const canRun = Boolean(
    data.permissionsKnown &&
      claim?.knownStatus &&
      (!audit || audit.knownStatus) &&
      data.capabilities.runClaimAudit.allowed &&
      pendingAction !== "run-claim-audit",
  )
  const executionLabel = audit?.knownStatus
    ? audit.status
    : audit
      ? `未知 · ${audit.status}`
      : "尚未运行"
  const outcomeLabel = audit?.outcomeKnown
    ? (audit.outcome ?? "未提供")
    : audit?.outcome
      ? `未知 · ${audit.outcome}`
      : "尚无确定性结果"

  return (
    <div className="m7-stage-two-surface" data-od-id="audits-main-surface">
      <section className="m7-stage-panel m7-audit-command">
        <div className="m7-section-heading">
          <div>
            <span className="m7-eyebrow">DETERMINISTIC CLAIM AUDIT</span>
            <h2>主张审计</h2>
            <p>执行状态与确定性 outcome 独立显示；AI 解释不会修改审计结论。</p>
          </div>
          <Button
            type="button"
            size="sm"
            disabled={!canRun}
            title={
              canRun
                ? "运行所选主张审计"
                : (data.capabilities.runClaimAudit.disabledReason ??
                  "权限、主张状态或提交状态不允许运行")
            }
            onClick={() =>
              claim &&
              onEvent({
                action: "run-claim-audit",
                claimId: claim.id,
                requestAiExplanation,
              })
            }
          >
            <Play aria-hidden="true" />
            {pendingAction === "run-claim-audit" ? "正在提交" : "运行审计"}
          </Button>
        </div>
        <label className="m7-check-control">
          <input
            type="checkbox"
            checked={requestAiExplanation}
            onChange={(event) => setRequestAiExplanation(event.target.checked)}
          />
          <span>
            <BrainCircuit aria-hidden="true" />
            请求 AI 解释
            <small>仅请求辅助说明，不改变 deterministic outcome。</small>
          </span>
        </label>
        {!claim ? (
          <div className="m7-inline-notice m7-inline-notice--warning">
            <AlertTriangle aria-hidden="true" />
            <span>没有可用于审计的已选主张。</span>
          </div>
        ) : null}
        <DisabledReason show={!canRun}>
          {data.capabilities.runClaimAudit.disabledReason ??
            "权限、主张状态、审计状态或提交状态不允许运行。"}
        </DisabledReason>
      </section>

      <section className="m7-stage-panel">
        <div className="m7-status-chain" aria-label="审计状态">
          <div>
            <span>执行状态</span>
            <StatusBadge
              label={executionLabel}
              tone={statusTone(
                audit?.status ?? "UNKNOWN",
                Boolean(audit?.knownStatus),
              )}
            />
          </div>
          <ChevronRight aria-hidden="true" />
          <div>
            <span>确定性结果</span>
            <StatusBadge
              label={outcomeLabel}
              tone={statusTone(
                audit?.outcome ?? "UNKNOWN",
                Boolean(audit?.outcomeKnown),
              )}
            />
          </div>
        </div>
        {audit?.status === "QUEUED" || audit?.status === "RUNNING" ? (
          <div className="m7-progress-block">
            <div>
              <Clock3 aria-hidden="true" />
              <span>
                {audit.status === "QUEUED"
                  ? "审计已进入队列，accepted 不等于 completed。"
                  : "确定性规则正在运行，当前不会推断最终 outcome。"}
              </span>
            </div>
            <div
              className="m7-indeterminate-progress"
              aria-label="审计处理中"
            />
          </div>
        ) : null}
        {audit?.degraded ? (
          <DegradedNotice
            title="AI / Provider 降级"
            message="确定性审计结果仍然有效；AI 解释能力当前受限。"
          />
        ) : null}
        {audit && !audit.knownStatus ? (
          <PermissionNotice
            title="未知审计状态"
            reason={`服务端返回 ${audit.status}；保留原始文本并关闭所有状态动作。`}
          />
        ) : null}
        {audit ? (
          <MetadataList
            items={[
              { label: "审计类型", value: audit.auditType },
              {
                label: "目标",
                value: `${audit.targetObjectType ?? "未提供"} · ${audit.targetObjectId ? shortId(audit.targetObjectId) : "未提供"}`,
              },
              {
                label: "Audit Job",
                value: data.auditJob
                  ? `${shortId(data.auditJob.id)} · ${data.auditJob.status}`
                  : "未提供",
                mono: true,
              },
              { label: "规则集", value: audit.ruleSetVersion, mono: true },
              {
                label: "来源快照",
                value: audit.sourceSnapshotHash ?? "尚未生成",
                mono: true,
              },
              {
                label: "结果哈希",
                value: audit.resultHash ?? "尚未生成",
                mono: true,
              },
            ]}
          />
        ) : (
          <EmptyState
            title="没有审计记录"
            message="运行审计后等待服务端返回正式记录。"
          />
        )}
      </section>

      <section className="m7-stage-panel">
        <div className="m7-section-heading">
          <div>
            <h3>确定性 Findings</h3>
            <p>结构化字段按纯文本显示，不执行 HTML、Markdown 或脚本。</p>
          </div>
          <StatusBadge
            label={`${audit?.findings.length ?? 0} 项`}
            tone="neutral"
          />
        </div>
        {audit?.findings.length ? (
          <div className="m7-finding-list">
            {audit.findings.map((finding, index) => (
              <article key={`${audit.id}-finding-${index}`}>
                <strong>Finding {index + 1}</strong>
                <dl>
                  {Object.entries(finding).map(([key, value]) => (
                    <div key={key}>
                      <dt>{key}</dt>
                      <dd>
                        <pre>{safeValue(value)}</pre>
                      </dd>
                    </div>
                  ))}
                </dl>
              </article>
            ))}
          </div>
        ) : (
          <div className="m7-quiet-empty">
            当前记录没有可展示的结构化 finding。
          </div>
        )}
        {audit?.limitations.length ? (
          <div className="m7-limitations">
            <strong>限制</strong>
            <ul>
              {audit.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      {audit?.status === "FAILED" ? (
        <section className="m7-stage-panel m7-action-boundary">
          <div>
            <RotateCcw aria-hidden="true" />
            <span>
              <strong>
                {data.auditJob ? "Audit Job 失败" : "无法定位审计 Job"}
              </strong>
              <small>
                {data.auditJob
                  ? `只读 Job ${shortId(data.auditJob.id)} 已投影；当前 Workspace 不开放 Audit retry 命令。`
                  : "当前投影未提供与此 Audit 绑定的 Job；不能复用导出 Job 或伪造 retry。"}
              </small>
            </span>
          </div>
          <Button type="button" size="sm" variant="outline" disabled>
            重试不可用
          </Button>
        </section>
      ) : null}
    </div>
  )
}

const candidateStatusLabels: Record<string, string> = {
  INCLUDED: "包含",
  EXCLUDED: "排除",
  METADATA_ONLY: "仅元数据",
  REFERENCE_ONLY: "仅引用",
  BLOCKED: "阻断",
  MISSING: "缺失",
}

function CandidateIcon({ candidate }: { candidate: ExportCandidateViewModel }) {
  if (!candidate.knownStatus) return <CircleHelp aria-hidden="true" />
  if (candidate.status === "INCLUDED") return <Check aria-hidden="true" />
  if (candidate.status === "MISSING") return <FileClock aria-hidden="true" />
  if (candidate.status === "BLOCKED") return <Ban aria-hidden="true" />
  if (candidate.status === "METADATA_ONLY")
    return <FileJson2 aria-hidden="true" />
  if (candidate.status === "REFERENCE_ONLY") return <Link2 aria-hidden="true" />
  return <XCircle aria-hidden="true" />
}

const defaultPackageInput: ReproPackageInput = {
  includeOriginalLiteratureFiles: false,
  includeDatasetVersions: true,
  includeSensitiveData: false,
  includeAgentLogs: false,
  includeModelOutputArtifacts: true,
  acknowledgeLicenseWarnings: false,
}

function PackageOptions({
  value,
  onChange,
}: {
  value: ReproPackageInput
  onChange: (value: ReproPackageInput) => void
}) {
  const fields: Array<[keyof ReproPackageInput, string, string]> = [
    [
      "includeOriginalLiteratureFiles",
      "原始文献文件",
      "受许可证和再分发限制约束",
    ],
    ["includeDatasetVersions", "数据集版本", "包含服务端确认可导出的版本"],
    [
      "includeSensitiveData",
      "敏感数据",
      "默认关闭；勾选不代表 read scope 或批准",
    ],
    ["includeAgentLogs", "Agent 日志", "M7 当前为 NOT_AVAILABLE"],
    ["includeModelOutputArtifacts", "模型输出 Artifact", "仅包含服务端候选项"],
    ["acknowledgeLicenseWarnings", "确认许可证警告", "不能覆盖再分发硬阻断"],
  ]
  return (
    <div className="m7-option-grid">
      {fields.map(([key, label, description]) => (
        <label key={key}>
          <input
            type="checkbox"
            checked={value[key]}
            onChange={(event) =>
              onChange({ ...value, [key]: event.target.checked })
            }
          />
          <span>
            <strong>{label}</strong>
            <small>{description}</small>
          </span>
        </label>
      ))}
    </div>
  )
}

function ManifestDialog({ data }: { data: EvidenceWorkspaceViewModel }) {
  const [open, setOpen] = useState(false)
  const packageValue = data.package
  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false)
    }
    window.addEventListener("keydown", onKeyDown, true)
    return () => window.removeEventListener("keydown", onKeyDown, true)
  }, [open])
  if (!packageValue) return null
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" size="sm" variant="outline">
          <FileJson2 aria-hidden="true" />
          查看 Manifest
        </Button>
      </DialogTrigger>
      <DialogContent
        className="m7-manifest-sheet"
        onEscapeKeyDown={() => setOpen(false)}
      >
        <DialogHeader>
          <DialogTitle>Package Manifest</DialogTitle>
          <DialogDescription>
            不可变 Package v{packageValue.packageVersion}{" "}
            的只读文件清单与运行时元数据。
          </DialogDescription>
        </DialogHeader>
        <div className="m7-manifest-summary">
          <MetadataList
            items={[
              {
                label: "Schema",
                value: packageValue.manifest.schemaVersion,
                mono: true,
              },
              {
                label: "Manifest SHA-256",
                value: packageValue.manifest.sha256,
                mono: true,
              },
              { label: "Agent logs", value: packageValue.manifest.agentLogs },
            ]}
          />
        </div>
        <div className="m7-manifest-table m7-table-scroll">
          <table>
            <thead>
              <tr>
                <th>路径 / 类型</th>
                <th>大小 / SHA-256</th>
                <th>许可证 / 再分发</th>
                <th>来源</th>
              </tr>
            </thead>
            <tbody>
              {packageValue.manifest.files.map((file) => (
                <tr key={`${file.path}-${file.sha256}`}>
                  <td>
                    <div className="m7-copy-line">
                      <code>{file.path}</code>
                      <CopyButton label="复制文件路径" value={file.path} />
                    </div>
                    <small>{file.type}</small>
                  </td>
                  <td>
                    <span>{formatBytes(file.size)}</span>
                    <div className="m7-copy-line">
                      <code>{file.sha256}</code>
                      <CopyButton label="复制文件哈希" value={file.sha256} />
                    </div>
                  </td>
                  <td>
                    <StatusBadge
                      label={file.licenseStatus}
                      tone={
                        file.licenseStatus === "PERMITTED"
                          ? "success"
                          : "warning"
                      }
                    />
                    <small>
                      {file.redistribution}
                      {file.sensitive ? " · 敏感" : ""}
                    </small>
                  </td>
                  <td>
                    <pre>{safeValue(file.source)}</pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="m7-runtime-grid">
          <section>
            <strong>Runtime dependencies</strong>
            {packageValue.manifest.runtimeDependencies.map((item, index) => (
              <pre key={`runtime-${index}`}>{safeValue(item)}</pre>
            ))}
          </section>
          <section>
            <strong>Service images</strong>
            {packageValue.manifest.serviceImages.map((item, index) => (
              <pre key={`image-${index}`}>{safeValue(item)}</pre>
            ))}
          </section>
        </div>
        {packageValue.manifest.limitations.length ? (
          <div className="m7-limitations">
            <strong>Manifest 限制</strong>
            <ul>
              {packageValue.manifest.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function CancelJobDialog({
  data,
  pendingAction,
  onEvent,
}: {
  data: EvidenceWorkspaceViewModel
  pendingAction: EvidenceWorkspaceEvent["action"] | null
  onEvent: (event: EvidenceWorkspaceEvent) => void
}) {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState("")
  const job = data.job
  const allowed = Boolean(
    data.permissionsKnown &&
      job?.knownStatus &&
      ["QUEUED", "RUNNING"].includes(job.status) &&
      data.capabilities.cancelJob.allowed &&
      pendingAction !== "cancel-job",
  )
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          type="button"
          size="sm"
          variant="destructive"
          disabled={!allowed}
          title={
            allowed
              ? "取消当前正式 Job"
              : (data.capabilities.cancelJob.disabledReason ??
                "Job 状态不允许取消")
          }
        >
          <Ban aria-hidden="true" />
          取消 Job
        </Button>
      </DialogTrigger>
      <DialogContent className="m7-dialog">
        <DialogHeader>
          <DialogTitle>取消正式导出 Job</DialogTitle>
          <DialogDescription>
            取消是破坏性请求。服务端决定最终状态，关闭窗口不会改变 Job。
          </DialogDescription>
        </DialogHeader>
        <label className="m7-dialog-field">
          <span>取消原因</span>
          <textarea
            autoFocus
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline">
              返回
            </Button>
          </DialogClose>
          <Button
            type="button"
            variant="destructive"
            disabled={!reason.trim()}
            onClick={() => {
              if (!job) return
              onEvent({ action: "cancel-job", jobId: job.id, reason })
              setOpen(false)
              setReason("")
            }}
          >
            提交取消意图
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ExportConfirmationDialog({
  data,
  pendingAction,
  onEvent,
}: {
  data: EvidenceWorkspaceViewModel
  pendingAction: EvidenceWorkspaceEvent["action"] | null
  onEvent: (event: EvidenceWorkspaceEvent) => void
}) {
  const [open, setOpen] = useState(false)
  const exportValue = data.export
  const approval = data.approval
  const allowed = Boolean(
    data.permissionsKnown &&
      exportValue?.knownStatus &&
      exportValue.status === "NEEDS_CONFIRMATION" &&
      exportValue.approvalId &&
      approval?.knownStatus &&
      approval.status === "PENDING" &&
      !approval.stale &&
      data.capabilities.requestExportConfirmation.allowed &&
      pendingAction !== "request-export-confirmation",
  )
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          type="button"
          size="sm"
          disabled={!allowed}
          title={
            allowed
              ? "处理当前正式 Export Confirmation"
              : "需要有效的 PENDING Approval 与正式 Export/Approval ID"
          }
        >
          <LockKeyhole aria-hidden="true" />
          处理正式确认
        </Button>
      </DialogTrigger>
      <DialogContent className="m7-dialog">
        <DialogHeader>
          <DialogTitle>处理正式 Export Confirmation</DialogTitle>
          <DialogDescription>
            此操作引用现有 Export 与
            Approval，不会在本地创建确认或改变正式状态。
          </DialogDescription>
        </DialogHeader>
        {exportValue && approval ? (
          <MetadataList
            items={[
              { label: "Export ID", value: exportValue.id, mono: true },
              { label: "Approval ID", value: approval.id, mono: true },
              {
                label: "Payload hash",
                value: approval.payloadHash,
                mono: true,
              },
              { label: "到期时间", value: approval.expiresAt ?? "未提供" },
            ]}
          />
        ) : null}
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline">
              返回
            </Button>
          </DialogClose>
          <Button
            type="button"
            onClick={() => {
              if (!exportValue?.approvalId) return
              onEvent({
                action: "request-export-confirmation",
                exportId: exportValue.id,
                approvalId: exportValue.approvalId,
              })
              setOpen(false)
            }}
          >
            提交确认意图
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ExportsView({
  data,
  pendingAction,
  onEvent,
}: {
  data: EvidenceWorkspaceViewModel
  pendingAction: EvidenceWorkspaceEvent["action"] | null
  onEvent: (event: EvidenceWorkspaceEvent) => void
}) {
  const [input, setInput] = useState<ReproPackageInput>(defaultPackageInput)
  const readiness = data.readiness
  const exportValue = data.export
  const approval = data.approval
  const job = data.job
  const packageValue = data.package
  const hasHardBlocker = Boolean(
    readiness?.blockers.some((item) => item.blocking),
  )
  const canReadiness =
    data.permissionsKnown &&
    data.capabilities.runExportReadiness.allowed &&
    pendingAction !== "run-export-readiness"
  const canCreate = Boolean(
    data.permissionsKnown &&
      readiness?.ready &&
      !hasHardBlocker &&
      data.capabilities.createReproPackage.allowed &&
      pendingAction !== "create-repro-package",
  )
  const canRetry = Boolean(
    data.permissionsKnown &&
      job?.knownStatus &&
      job.status === "FAILED" &&
      job.retryable &&
      data.capabilities.retryJob.allowed &&
      pendingAction !== "retry-job",
  )
  const canDownload = Boolean(
    data.permissionsKnown &&
      packageValue?.knownStatus &&
      packageValue.status === "AVAILABLE" &&
      !packageValue.tampered &&
      data.capabilities.downloadReproPackage.allowed &&
      pendingAction !== "download-repro-package",
  )

  return (
    <div className="m7-stage-two-surface" data-od-id="exports-main-surface">
      {packageValue?.tampered ? (
        <div className="m7-tampered-block m7-stage-risk-banner" role="alert">
          <ShieldAlert aria-hidden="true" />
          <div>
            <strong>Package 哈希不匹配</strong>
            <p>当前包被标记为 tampered，下载与复用均已硬阻断。</p>
          </div>
        </div>
      ) : packageValue?.knownStatus && packageValue.status !== "AVAILABLE" ? (
        <div className="m7-inline-notice m7-inline-notice--warning m7-stage-risk-banner">
          <FileClock aria-hidden="true" />
          <span>Package 状态为 {packageValue.status}，当前没有可用下载。</span>
        </div>
      ) : null}
      <section className="m7-stage-panel">
        <div className="m7-section-heading">
          <div>
            <span className="m7-eyebrow">EXPORT READINESS</span>
            <h2>可复现包配置</h2>
            <p>
              配置只生成 readiness 或 package intent；UI 不在本地计算正式结论。
            </p>
          </div>
          <StatusBadge
            label={readiness?.ready ? "服务端判定可继续" : "尚有阻断或未知项"}
            tone={readiness?.ready ? "success" : "warning"}
          />
        </div>
        <PackageOptions value={input} onChange={setInput} />
        <div className="m7-form-actions">
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={!canReadiness}
            onClick={() => onEvent({ action: "run-export-readiness", input })}
          >
            <FileCheck2 aria-hidden="true" />
            {pendingAction === "run-export-readiness"
              ? "正在提交"
              : "运行 Readiness"}
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={!canCreate}
            title={
              canCreate
                ? "创建正式 ReproPackage 请求"
                : (data.capabilities.createReproPackage.disabledReason ??
                  "Readiness、权限或阻断状态不允许创建")
            }
            onClick={() => onEvent({ action: "create-repro-package", input })}
          >
            <FolderArchive aria-hidden="true" />
            {pendingAction === "create-repro-package"
              ? "正在提交"
              : "创建 Package"}
          </Button>
        </div>
        <DisabledReason show={!canReadiness || !canCreate}>
          {!data.permissionsKnown
            ? "权限事实未知，Readiness 与 Package 写操作均已关闭。"
            : hasHardBlocker
              ? "当前 Readiness 存在硬阻断，不能创建 Package。"
              : (data.capabilities.runExportReadiness.disabledReason ??
                data.capabilities.createReproPackage.disabledReason ??
                "当前正式状态不允许继续提交。")}
        </DisabledReason>
      </section>

      <section className="m7-stage-panel">
        <div className="m7-section-heading">
          <div>
            <h3>Readiness 快照</h3>
            <p>快照或规则集变化后，历史结果不能视为当前有效。</p>
          </div>
          {readiness ? (
            <StatusBadge
              label={
                readiness.requiresConfirmation ? "需要正式确认" : "无需额外确认"
              }
              tone={readiness.requiresConfirmation ? "warning" : "neutral"}
            />
          ) : null}
        </div>
        {readiness ? (
          <>
            <MetadataList
              items={[
                {
                  label: "Audit ID",
                  value: shortId(readiness.auditId),
                  mono: true,
                },
                {
                  label: "Snapshot SHA-256",
                  value: readiness.snapshotHash,
                  mono: true,
                },
                {
                  label: "Rule set",
                  value: readiness.ruleSetVersion,
                  mono: true,
                },
              ]}
            />
            <div className="m7-readiness-issues">
              {readiness.blockers.map((issue) => (
                <article
                  className="m7-issue m7-issue--blocker"
                  key={`${issue.code}-${issue.objectId}`}
                >
                  <LockKeyhole aria-hidden="true" />
                  <div>
                    <strong>{issue.code}</strong>
                    <p>{issue.message}</p>
                    <small>
                      {issue.objectType} ·{" "}
                      {issue.objectId
                        ? shortId(issue.objectId)
                        : "未提供对象 ID"}
                    </small>
                  </div>
                </article>
              ))}
              {readiness.warnings.map((issue) => (
                <article
                  className="m7-issue m7-issue--warning"
                  key={`${issue.code}-${issue.objectId}`}
                >
                  <TriangleAlert aria-hidden="true" />
                  <div>
                    <strong>{issue.code}</strong>
                    <p>{issue.message}</p>
                    <small>确认不能覆盖许可证或再分发硬阻断。</small>
                  </div>
                </article>
              ))}
              {!readiness.blockers.length && !readiness.warnings.length ? (
                <div className="m7-quiet-empty">
                  当前快照没有服务端投影的 blocker 或 warning。
                </div>
              ) : null}
            </div>
          </>
        ) : (
          <EmptyState
            title="没有 Readiness 快照"
            message="先请求服务端运行导出准备度检查。"
          />
        )}
      </section>

      <section className="m7-stage-panel">
        <div className="m7-section-heading">
          <div>
            <h3>候选文件</h3>
            <p>include status、许可证、敏感性与再分发事实均来自服务端投影。</p>
          </div>
          <StatusBadge
            label={`${readiness?.candidates.length ?? 0} 项`}
            tone="neutral"
          />
        </div>
        <div className="m7-candidate-list">
          {readiness?.candidates.map((candidate, index) => (
            <article
              key={`${candidate.objectType}-${candidate.objectId}-${index}`}
            >
              <div className="m7-candidate-icon">
                <CandidateIcon candidate={candidate} />
              </div>
              <div>
                <strong>{candidate.packagePath}</strong>
                <small>
                  {candidate.objectType} ·{" "}
                  {candidate.objectId
                    ? shortId(candidate.objectId)
                    : "无对象 ID"}
                </small>
              </div>
              <div className="m7-badge-row">
                <StatusBadge
                  label={
                    candidate.knownStatus
                      ? (candidateStatusLabels[candidate.status] ??
                        candidate.status)
                      : `未知 · ${candidate.status}`
                  }
                  tone={statusTone(candidate.status, candidate.knownStatus)}
                />
                <StatusBadge
                  label={candidate.licenseStatus}
                  tone={
                    candidate.licenseStatus === "PERMITTED"
                      ? "success"
                      : "warning"
                  }
                />
                {candidate.sensitive ? (
                  <StatusBadge label="敏感" tone="danger" />
                ) : null}
              </div>
              <small className="m7-candidate-note">
                {candidate.redistribution}
                {candidate.exclusionReason
                  ? ` · ${candidate.exclusionReason}`
                  : ""}
              </small>
            </article>
          ))}
          {!readiness?.candidates.length ? (
            <div className="m7-quiet-empty">没有候选项。</div>
          ) : null}
        </div>
      </section>

      <section className="m7-stage-panel">
        <div className="m7-section-heading">
          <div>
            <span className="m7-eyebrow">FORMAL STATE CHAIN</span>
            <h3>Export、Approval 与 Job</h3>
            <p>每一层状态独立；Job 完成不推断 Package 可用或哈希正确。</p>
          </div>
        </div>
        <div className="m7-export-chain">
          <article>
            <FileCheck2 aria-hidden="true" />
            <span>Export</span>
            <StatusBadge
              label={
                exportValue
                  ? exportValue.knownStatus
                    ? exportValue.status
                    : `未知 · ${exportValue.status}`
                  : "未创建"
              }
              tone={statusTone(
                exportValue?.status ?? "UNKNOWN",
                Boolean(exportValue?.knownStatus),
              )}
            />
          </article>
          <ChevronRight aria-hidden="true" />
          <article>
            <LockKeyhole aria-hidden="true" />
            <span>Approval</span>
            <StatusBadge
              label={
                approval
                  ? approval.knownStatus
                    ? approval.status
                    : `未知 · ${approval.status}`
                  : "不适用"
              }
              tone={statusTone(
                approval?.status ?? "UNKNOWN",
                approval ? approval.knownStatus : true,
              )}
            />
          </article>
          <ChevronRight aria-hidden="true" />
          <article>
            <HardDriveDownload aria-hidden="true" />
            <span>Job</span>
            <StatusBadge
              label={
                job
                  ? job.knownStatus
                    ? job.status
                    : `未知 · ${job.status}`
                  : "未创建"
              }
              tone={statusTone(
                job?.status ?? "UNKNOWN",
                Boolean(job?.knownStatus),
              )}
            />
          </article>
          <ChevronRight aria-hidden="true" />
          <article>
            <PackageCheck aria-hidden="true" />
            <span>Package</span>
            <StatusBadge
              label={
                packageValue
                  ? packageValue.tampered
                    ? "哈希不匹配"
                    : packageValue.status
                  : "不可用"
              }
              tone={
                packageValue?.tampered
                  ? "danger"
                  : statusTone(
                      packageValue?.status ?? "UNKNOWN",
                      Boolean(packageValue?.knownStatus),
                    )
              }
            />
          </article>
        </div>
        {job ? (
          <div className="m7-job-progress">
            <div>
              <span>{job.taskType}</span>
              <strong>{Math.max(0, Math.min(100, job.progress))}%</strong>
            </div>
            <progress
              max={100}
              value={Math.max(0, Math.min(100, job.progress))}
            />
            {job.errorCode ? <small>错误代码：{job.errorCode}</small> : null}
          </div>
        ) : null}
        {approval &&
        ["STALE", "EXPIRED", "REJECTED"].includes(
          approval.stale ? "STALE" : approval.status,
        ) ? (
          <PermissionNotice
            title="Approval 不可执行"
            reason={
              approval.stale
                ? "Approval 已陈旧，必须等待新的正式投影。"
                : `Approval 状态为 ${approval.status}。`
            }
          />
        ) : null}
        <div className="m7-form-actions m7-form-actions--chain">
          <ExportConfirmationDialog
            data={data}
            pendingAction={pendingAction}
            onEvent={onEvent}
          />
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={!canRetry}
            onClick={() =>
              job && onEvent({ action: "retry-job", jobId: job.id })
            }
          >
            <RotateCcw aria-hidden="true" />
            重试 Job
          </Button>
          <CancelJobDialog
            data={data}
            pendingAction={pendingAction}
            onEvent={onEvent}
          />
        </div>
        <DisabledReason
          show={!canRetry || !data.capabilities.cancelJob.allowed}
        >
          {data.capabilities.retryJob.disabledReason ??
            data.capabilities.cancelJob.disabledReason ??
            "当前 Job 状态没有可用的重试或取消动作。"}
        </DisabledReason>
      </section>

      <section className="m7-stage-panel">
        <div className="m7-section-heading">
          <div>
            <span className="m7-eyebrow">IMMUTABLE PACKAGE</span>
            <h3>Package 与 Manifest</h3>
            <p>
              Export COMPLETED 与 Package AVAILABLE 分开核验；tampered
              时下载硬阻断。
            </p>
          </div>
          <div className="m7-form-actions">
            <ManifestDialog data={data} />
            <Button
              type="button"
              size="sm"
              disabled={!canDownload}
              title={
                canDownload
                  ? "下载已验证可用的 Package"
                  : "Package 未知、不可用、被篡改或权限不足"
              }
              onClick={() =>
                packageValue &&
                onEvent({
                  action: "download-repro-package",
                  packageId: packageValue.id,
                })
              }
            >
              <Download aria-hidden="true" />
              下载 Package
            </Button>
          </div>
        </div>
        {packageValue ? (
          <>
            {packageValue.tampered ? (
              <div className="m7-tampered-block">
                <ShieldAlert aria-hidden="true" />
                <div>
                  <strong>Package 哈希不匹配</strong>
                  <p>
                    当前包被标记为 tampered。下载与复用已关闭，不能用 Job
                    完成状态覆盖此阻断。
                  </p>
                </div>
              </div>
            ) : null}
            <MetadataList
              items={[
                {
                  label: "Package ID",
                  value: shortId(packageValue.id),
                  mono: true,
                },
                {
                  label: "不可变版本",
                  value: `v${packageValue.packageVersion}`,
                },
                {
                  label: "Schema",
                  value: packageValue.schemaVersion,
                  mono: true,
                },
                { label: "文件数", value: packageValue.fileCount },
                {
                  label: "总大小",
                  value: formatBytes(packageValue.totalSizeBytes),
                },
                { label: "SHA-256", value: packageValue.sha256, mono: true },
              ]}
            />
            <div className="m7-package-history">
              {data.packageHistory.map((item) => (
                <article
                  key={item.id}
                  aria-current={item.selected || undefined}
                >
                  {item.selected ? (
                    <PackageCheck aria-hidden="true" />
                  ) : (
                    <FileClock aria-hidden="true" />
                  )}
                  <div>
                    <strong>
                      v{item.packageVersion}
                      {item.selected ? " · 当前投影" : " · 历史版本"}
                    </strong>
                    <small>
                      {item.schemaVersion} · {item.fileCount} files ·{" "}
                      {formatBytes(item.totalSizeBytes)}
                    </small>
                    <small>{item.sha256}</small>
                  </div>
                </article>
              ))}
              {data.packageHistoryHasNext ? (
                <article className="m7-package-history__unavailable">
                  <FileClock aria-hidden="true" />
                  <div>
                    <strong>更早的不可变版本尚未加载</strong>
                    <small>历史列表是分页投影，当前页不代表完整历史。</small>
                  </div>
                </article>
              ) : null}
            </div>
          </>
        ) : (
          <EmptyState
            title="Package 不可用"
            message="没有正式 Package 投影，不显示伪下载链接。"
          />
        )}
        <DisabledReason show={!canDownload}>
          {data.capabilities.downloadReproPackage.disabledReason ??
            "Package 未知、不可用、被篡改或权限不足，下载已关闭。"}
        </DisabledReason>
      </section>
    </div>
  )
}

function DeferredView({ view }: { view: "audits" | "exports" }) {
  return (
    <div className="m7-deferred-view" data-od-id={`${view}-stage-boundary`}>
      <FileCheck2 aria-hidden="true" />
      <h2>{view === "audits" ? "审计" : "导出"}</h2>
      <p>当前阶段仅保留工作区入口。正式状态与操作尚未在本 UI 阶段开放。</p>
      <StatusBadge label="阶段 2 范围" tone="neutral" />
    </div>
  )
}

function ReadyWorkspace({
  data,
  pendingAction,
  mutationError,
  initialView = "graph",
  onViewChange,
  onRetry,
  onEvent,
  graphMode: controlledMode,
  onGraphModeChange,
}: EvidenceWorkspaceVisualProps & { data: EvidenceWorkspaceViewModel }) {
  const visualTheme = useVisualTheme() ?? "light"
  const [view, setView] = useState<EvidenceWorkspaceView>(initialView)
  const [localMode, setLocalMode] = useState<EvidenceGraphMode>("graph")
  const [selection, setSelection] = useState<Selection>(
    data.selectedNode
      ? { kind: "node", id: data.selectedNode.id }
      : data.selectedLink
        ? { kind: "link", id: data.selectedLink.id }
        : null,
  )
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const graphMode = controlledMode ?? localMode
  const setGraphMode = (mode: EvidenceGraphMode) => {
    setLocalMode(mode)
    onGraphModeChange?.(mode)
  }

  useEffect(() => {
    setView(initialView)
  }, [initialView])
  useEffect(() => {
    setSelection(
      data.selectedNode
        ? { kind: "node", id: data.selectedNode.id }
        : data.selectedLink
          ? { kind: "link", id: data.selectedLink.id }
          : null,
    )
  }, [data])
  const changeView = (next: EvidenceWorkspaceView) => {
    setView(next)
    onViewChange?.(next)
  }

  return (
    <div
      className="m7-evidence-workspace reca-visual-refresh"
      data-theme={visualTheme}
      data-od-id="evidence-workspace"
    >
      <WorkspaceHeader
        title="Evidence Workspace"
        context={`项目 ${shortId(data.projectId)}`}
        metadata={
          <div className="m7-header-meta">
            {data.graph.partial ? (
              <StatusBadge label="部分图谱" tone="warning" />
            ) : (
              <StatusBadge label="投影完整" tone="success" />
            )}
            {data.graph.degraded ? (
              <StatusBadge label="降级" tone="degraded" />
            ) : null}
            {!data.permissionsKnown ? (
              <StatusBadge label="权限未知" tone="unknown" />
            ) : null}
          </div>
        }
        actions={
          <>
            <IconButton
              label="刷新工作区"
              disabled={pendingAction === "refresh"}
              onClick={() => onEvent({ action: "refresh" })}
            >
              <RefreshCw aria-hidden="true" />
            </IconButton>
            <IconButton
              label="打开 Inspector"
              className="m7-inspector-trigger"
              onClick={() => setInspectorOpen(true)}
            >
              <PanelRightOpen aria-hidden="true" />
            </IconButton>
          </>
        }
      />
      <nav className="m7-view-tabs" aria-label="Evidence Workspace 视图">
        {(["graph", "claims", "audits", "exports"] as const).map((item) => (
          <button
            key={item}
            type="button"
            aria-current={view === item ? "page" : undefined}
            onClick={() => changeView(item)}
          >
            {item === "graph" ? (
              <Network aria-hidden="true" />
            ) : item === "claims" ? (
              <List aria-hidden="true" />
            ) : item === "audits" ? (
              <FileCheck2 aria-hidden="true" />
            ) : (
              <GitBranch aria-hidden="true" />
            )}
            <span>{viewLabels[item]}</span>
          </button>
        ))}
      </nav>
      {mutationError ? (
        <div className="m7-mutation-band">
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
      {!data.permissionsKnown ? (
        <div className="m7-permission-band">
          <PermissionNotice reason="服务端权限事实未知，所有写操作保持禁用。" />
        </div>
      ) : null}
      {data.routeFallback ? (
        <div className="m7-route-band">
          <PermissionNotice
            title="已回退到授权默认视图"
            reason="深链接目标不可访问；未披露对象是否存在。"
          />
        </div>
      ) : null}
      <div className="m7-workspace-grid">
        <aside className="m7-left-pane" data-od-id="evidence-claim-queue">
          <ClaimQueue data={data} />
        </aside>
        <main className="m7-main-pane">
          {view === "graph" ? (
            <>
              <div className="m7-main-toolbar">
                <div>
                  <strong>项目证据图谱</strong>
                  <span>
                    {data.graph.nodes.length} 节点 · {data.graph.edges.length}{" "}
                    关系
                  </span>
                </div>
                <div className="m7-toolbar-actions">
                  <div className="m7-mode-switch" aria-label="图谱显示模式">
                    <button
                      type="button"
                      aria-pressed={graphMode === "graph"}
                      onClick={() => setGraphMode("graph")}
                    >
                      <Network aria-hidden="true" />
                      画布
                    </button>
                    <button
                      type="button"
                      aria-pressed={graphMode === "table"}
                      onClick={() => setGraphMode("table")}
                    >
                      <Table2 aria-hidden="true" />
                      表格
                    </button>
                  </div>
                  <IconButton
                    label="刷新图谱"
                    disabled={pendingAction === "refresh-graph"}
                    onClick={() => onEvent({ action: "refresh-graph" })}
                  >
                    <RefreshCw aria-hidden="true" />
                  </IconButton>
                </div>
              </div>
              <GraphNotices data={data} />
              {graphMode === "graph" ? (
                <GraphCanvas
                  data={data}
                  selection={selection}
                  onSelection={setSelection}
                />
              ) : (
                <GraphTable
                  data={data}
                  selection={selection}
                  onSelection={setSelection}
                />
              )}
            </>
          ) : view === "claims" ? (
            <ClaimsView
              data={data}
              selection={selection}
              onSelection={setSelection}
              onEvent={onEvent}
            />
          ) : view === "audits" ? (
            <AuditView
              data={data}
              pendingAction={pendingAction}
              onEvent={onEvent}
            />
          ) : view === "exports" ? (
            <ExportsView
              data={data}
              pendingAction={pendingAction}
              onEvent={onEvent}
            />
          ) : (
            <DeferredView view={view} />
          )}
        </main>
        <aside className="m7-right-pane" data-od-id="evidence-inspector">
          <div className="m7-pane-title">
            <div>
              <strong>Inspector</strong>
              <span>服务端投影事实</span>
            </div>
          </div>
          <Inspector data={data} selection={selection} onEvent={onEvent} />
        </aside>
      </div>
      <Dialog open={inspectorOpen} onOpenChange={setInspectorOpen}>
        <DialogContent className="m7-inspector-sheet">
          <DialogHeader>
            <DialogTitle>Inspector</DialogTitle>
            <DialogDescription>
              当前选中对象的服务端投影事实。
            </DialogDescription>
          </DialogHeader>
          <Inspector data={data} selection={selection} onEvent={onEvent} />
        </DialogContent>
      </Dialog>
    </div>
  )
}

export function EvidenceWorkspace(props: EvidenceWorkspaceVisualProps) {
  const visualTheme = useVisualTheme() ?? "light"
  if (props.content.state === "loading") {
    return (
      <div
        className="m7-evidence-workspace reca-visual-refresh"
        data-theme={visualTheme}
      >
        <WorkspaceHeader
          title="Evidence Workspace"
          context="正在读取项目证据"
          metadata={<StatusBadge label="正在加载" tone="info" />}
        />
        <WorkspaceLoadingSkeleton
          layout="three-pane"
          state="loading"
          title="正在加载证据工作区"
          message={props.content.label}
        />
      </div>
    )
  }
  if (props.content.state === "empty") {
    return (
      <div
        className="m7-evidence-workspace reca-visual-refresh m7-state-workspace"
        data-theme={visualTheme}
      >
        <WorkspaceHeader title="Evidence Workspace" context="已授权范围" />
        <WorkspaceLoadingSkeleton
          layout="three-pane"
          state="empty"
          title="没有可显示的证据"
          message={props.content.message}
        />
      </div>
    )
  }
  if (props.content.state === "error") {
    const error = props.content.error
    return (
      <div
        className="m7-evidence-workspace reca-visual-refresh m7-state-workspace"
        data-theme={visualTheme}
      >
        <WorkspaceHeader
          title="Evidence Workspace"
          context="加载未完成"
          metadata={
            <StatusBadge
              label={error.forbidden ? "无权查看" : "加载失败"}
              tone="danger"
            />
          }
        />
        <WorkspaceLoadingSkeleton
          layout="three-pane"
          state={error.forbidden ? "forbidden" : "error"}
          title={error.title}
          message={error.message}
          action={
            error.retryable ? (
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={props.onRetry}
              >
                重试
              </Button>
            ) : undefined
          }
        />
      </div>
    )
  }
  return <ReadyWorkspace {...props} data={props.content.data} />
}
