import { Filter, MoreHorizontal, Search } from "lucide-react"

import {
  DegradedNotice,
  InspectorSection,
  JobProgress,
  LoadableState,
  MetadataList,
  MutationError,
  PaneHeader,
  PermissionNotice,
  SectionHeader,
  SourceBadge,
  StatusBadge,
  WorkspaceHeader,
} from "@/components/reca-visual-refresh"
import { Button } from "@/components/ui/button"

const literatureRows = [
  {
    id: "candidate-01K1WQ9M6F8TZ7A0Q3PK2J",
    title: "生成式人工智能使用与师范生学习投入的关联",
    source: "OpenAlex 候选",
    tone: "warning" as const,
    status: "待复核",
    year: "2025",
  },
  {
    id: "record-01K1WQ9M6F8TZ7A0Q3PK2K",
    title: "数字学习政策背景下的多维学习投入研究",
    source: "正式记录",
    tone: "success" as const,
    status: "已验证",
    year: "2024",
  },
  {
    id: "candidate-01K1WQ9M6F8TZ7A0Q3PK2L",
    title: "师范教育项目中的 AI 辅助学习投入",
    source: "降级候选",
    tone: "degraded" as const,
    status: "来源降级",
    year: "2023",
  },
] as const

export function VisualFoundationsPreview() {
  return (
    <div className="visual-foundations-module" data-od-id="foundations-module">
      <WorkspaceHeader
        context="RECA / 共享视觉语言"
        title="Visual Foundations"
        actions={
          <Button type="button" variant="outline" size="sm">
            查看 Token 说明
          </Button>
        }
      />

      <div className="visual-foundations-sections">
        <section
          className="visual-foundations-section"
          data-od-id="foundation-type-controls"
        >
          <SectionHeader
            title="字体、间距与控件"
            description="统一标题、正文、metadata 与控制高度；所有 letter-spacing 固定为 0。"
          />
          <div className="visual-foundations-section__content visual-foundations-grid">
            <div className="visual-foundations-type-stack">
              <div>
                <span>页面标题 · 22px</span>
                <strong>文献检索与复核</strong>
              </div>
              <div>
                <span>Section · 15px</span>
                <b>候选文献</b>
              </div>
              <div>
                <span>正文 · 14px</span>
                <p>扫描、比较并定位需要人工复核的候选记录。</p>
              </div>
              <div>
                <span>Metadata · 12px</span>
                <small>更新于 2026-08-02 · 来源 OpenAlex</small>
              </div>
            </div>
            <div className="visual-foundations-specimens">
              <div className="visual-foundations-specimen">
                <span>按钮与图标按钮</span>
                <div className="visual-foundations-actions">
                  <Button type="button" size="sm">
                    确认范围
                  </Button>
                  <Button type="button" size="sm" variant="outline">
                    保存草稿
                  </Button>
                  <Button type="button" size="sm" variant="ghost">
                    取消
                  </Button>
                  <Button
                    type="button"
                    size="icon-sm"
                    variant="outline"
                    aria-label="筛选"
                  >
                    <Filter aria-hidden="true" />
                  </Button>
                  <Button
                    type="button"
                    size="icon-sm"
                    variant="ghost"
                    aria-label="更多操作"
                  >
                    <MoreHorizontal aria-hidden="true" />
                  </Button>
                </div>
              </div>
              <div className="visual-foundations-specimen">
                <span>禁用操作与原因</span>
                <div className="visual-foundations-actions">
                  <Button type="button" size="sm" disabled>
                    写入正式记录
                  </Button>
                  <small>权限状态未知，写操作保持禁用。</small>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          className="visual-foundations-section"
          data-od-id="foundation-semantics"
        >
          <SectionHeader
            title="状态与来源语义"
            description="重要状态同时使用图标、文字和语义色；AI suggestion 与 evidence 不共用角色。"
          />
          <div className="visual-foundations-section__content visual-foundations-grid">
            <div className="visual-foundations-badge-group">
              <span>状态</span>
              <div>
                <StatusBadge label="服务端已确认" tone="success" />
                <StatusBadge label="待复核" tone="warning" />
                <StatusBadge label="请求失败" tone="danger" />
                <StatusBadge label="降级结果" tone="degraded" />
                <StatusBadge label="未知状态" tone="future-state" />
              </div>
            </div>
            <div className="visual-foundations-badge-group">
              <span>来源</span>
              <div>
                <SourceBadge label="已定位证据" kind="evidence" />
                <SourceBadge label="AI 建议" kind="ai-suggestion" />
                <SourceBadge label="人工决策" kind="human-decision" />
                <SourceBadge label="审批记录" kind="approval" />
              </div>
            </div>
          </div>
        </section>

        <section
          className="visual-foundations-section"
          data-od-id="foundation-loadable-notices"
        >
          <SectionHeader title="Loadable、Notice 与 Job" />
          <div className="visual-foundations-section__content visual-foundations-state-grid">
            <LoadableState state="loading" title="正在载入正式记录" />
            <LoadableState state="empty" message="当前范围内没有记录" />
            <DegradedNotice
              title="解析结果已降级"
              message="当前结果来自 pypdf fallback，不代表 GROBID 高置信度结果。"
            />
            <PermissionNotice
              title="写操作不可用"
              reason="权限状态未知；请等待服务端返回正式权限。"
            />
            <MutationError
              title="操作未完成"
              message="事件已记录，但 Preview 不会模拟服务端成功。"
            />
            <JobProgress
              label="解析文档"
              statusLabel="运行中"
              tone="info"
              progress={45}
              step="正在转换 TEI；进度由 fixture 提供。"
            />
          </div>
        </section>

        <section
          className="visual-foundations-section"
          data-od-id="foundation-panes"
        >
          <SectionHeader
            title="Dense table、Pane 与 Inspector"
            description="左侧集合、中间密集列表、右侧 metadata；各区域独立滚动，选中行仅表示 UI selection。"
            actions={
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                aria-label="搜索表格"
              >
                <Search aria-hidden="true" />
              </Button>
            }
          />
          <div className="visual-foundations-panes">
            <aside className="visual-foundations-pane">
              <PaneHeader title="集合" subtitle="3" />
              <nav
                className="visual-foundations-collections"
                aria-label="文献集合"
              >
                <button type="button" aria-current="page">
                  全部候选 <span>24</span>
                </button>
                <button type="button">
                  待复核 <span>8</span>
                </button>
                <button type="button">
                  已验证 <span>16</span>
                </button>
              </nav>
            </aside>
            <div className="visual-foundations-pane">
              <PaneHeader title="文献记录" subtitle="仅用于密度检查" />
              <div className="visual-foundations-table-scroll">
                <table className="visual-foundations-table">
                  <thead>
                    <tr>
                      <th>标题</th>
                      <th>来源</th>
                      <th>状态</th>
                      <th>年份</th>
                    </tr>
                  </thead>
                  <tbody>
                    {literatureRows.map((row, index) => (
                      <tr key={row.id} data-selected={index === 0}>
                        <td>
                          <button type="button" title={row.title}>
                            {row.title}
                          </button>
                        </td>
                        <td>{row.source}</td>
                        <td>
                          <StatusBadge label={row.status} tone={row.tone} />
                        </td>
                        <td>{row.year}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <aside className="visual-foundations-pane">
              <PaneHeader title="Inspector" subtitle="候选记录" />
              <InspectorSection title="元数据">
                <MetadataList
                  items={[
                    {
                      label: "DOI",
                      value: "10.1000/reca.visual-refresh.long-identifier",
                    },
                    {
                      label: "Hash",
                      value: "sha256:f8531f78a487942e5f7a0d622f786b34c748",
                    },
                    {
                      label: "文件",
                      value:
                        "teacher-education-generative-ai-systematic-review-final.pdf",
                    },
                  ]}
                />
              </InspectorSection>
              <InspectorSection title="边界">
                <p className="visual-foundations-inspector-copy">
                  该选中状态只影响 Preview 本地界面，不代表正式业务事实。
                </p>
              </InspectorSection>
            </aside>
          </div>
        </section>
      </div>
    </div>
  )
}
