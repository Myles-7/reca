# RECA Frontend Design Baseline

| 项目 | 内容 |
| --- | --- |
| 文档角色 | RECA 前端视觉系统与 UI 设计唯一主要基线 |
| 文档状态 | APPROVED FOR M1 DEVELOPMENT |
| 基线兼容性 | 保留 `docs-m1-approved` 的产品、API、领域与 M1 Entry 范围；不表示本新增视觉基线已获批准 |
| 当前实现阶段 | M0 shell available；科研业务组件多数 planned |
| 技术基线 | React、Vite、strict TypeScript、Tailwind CSS、Radix primitives、Lucide |
| 最后更新 | 2026-07-31 |

本文档定义视觉语言、Design Token 分类、组件目录和页面布局原则，不定义产品 Requirement、API、后端 DTO、权限、Approval 或业务状态机。UI 产品要求见 [UX_NONFUNCTIONAL_AND_TRACEABILITY.md](../docs/product/UX_NONFUNCTIONAL_AND_TRACEABILITY.md)，Open Design 与 Codex 的协作边界见 [FRONTEND_DESIGN_INTEGRATION_RULES.md](../docs/development/FRONTEND_DESIGN_INTEGRATION_RULES.md)。

## 1. Product Design Principles

1. **科研工作台，而非聊天机器人。** 核心页面服务于扫描、比较、定位、复核和重复操作；Agent 只作为受控辅助入口。
2. **Information dense but readable。** 信息密度高，但通过稳定层级、分组、表格和 detail pane 保持可读。
3. **Evidence first。** 结论、建议和问题应尽可能提供来源、原文、版本或运行记录入口。
4. **Status explicit。** loading、stale、degraded、partial、failed 和 approval state 必须清晰可见。
5. **High-risk action obvious。** 高风险操作展示目标、影响、版本、审批要求和不可逆性，不与普通导航混淆。
6. **AI suggestion 与 verified fact 可区分。** 不能仅用颜色区分；同时使用 label、icon、source 和说明。
7. **来源透明。** evidence、analysis、approval、cache、preprocessed 与 offline snapshot 均显示来源和限制。
8. **Failure visible。** 不把不可用、未配置、未知或回退显示为成功。
9. **Competition demo friendly。** 主流程在桌面视口中易扫描、状态稳定、关键证据可快速定位，但不伪造未实现能力。

## 2. 当前视觉实现事实

当前 `frontend/src/index.css` 使用 Tailwind CSS theme mapping 和 CSS variables，已有 light/dark mode、background/foreground、primary、muted、accent、destructive、border、ring、chart 和 sidebar tokens。`frontend/src/components/ui/` 已有 Radix/shadcn 风格 primitives，图标主库为 Lucide。

本文件不要求本任务修改现有 token 数值。Open Design 可在后续视觉评审中冻结或调整统一 token，但不得在页面内另建互不兼容的视觉系统。

## 3. Design Tokens

### 3.1 分类与命名

| 分类 | 命名语义 | 当前来源 / 状态 |
| --- | --- | --- |
| color | `background`、`foreground`、`primary`、semantic roles | 部分 available，`index.css` |
| typography | page title、section、body、metadata、data | structure planned |
| spacing | control、stack、section、workspace gutter | Tailwind scale available；语义别名 planned |
| radius | control、panel、dialog | base variables available |
| border | default、strong、focus、semantic | 部分 available |
| shadow | overlay、dialog、sticky surface | planned；按需冻结 |
| size | icon、control、sidebar、pane | 部分组件内 available；语义别名 planned |
| z-index | sticky、popover、modal、toast | 部分 available；统一层级 planned |
| motion | duration、easing、enter/exit | utilities available；语义规则 planned |
| breakpoint | desktop、tablet、small-screen degradation | Tailwind breakpoints available；产品策略见第 10 节 |

Token 优先表达用途而非某个页面，例如 `color-status-danger` 优于 `literature-red`。没有设计依据时不编造完整最终数值；先冻结语义、来源和使用规则，再由 Open Design 评审数值。

### 3.2 使用规则

- 优先使用 `index.css` 暴露的 CSS variables、Tailwind theme 和共享 component variants；
- 不在 feature 页面重复硬编码大量 hex、font-size、spacing、radius、shadow 或 z-index；
- 视觉例外必须局部并说明原因；
- 业务状态映射为 semantic presentation，但 token 不定义后端状态；
- light/dark theme 必须同时保持层级、对比度和状态可辨识性。

## 4. Semantic Colors

视觉系统至少需要以下语义角色：

| 角色 | 用途 | 状态 |
| --- | --- | --- |
| neutral | 默认内容、边界和非强调信息 | available |
| info | 一般说明和进行中信息 | planned semantic role |
| success | 成功且已由正式结果确认 | partial |
| warning | 风险、待复核、低置信度 | planned semantic role |
| danger | 失败、破坏性操作、严重问题 | destructive available |
| AI suggestion | 模型建议或候选，不是事实 | planned semantic role |
| evidence | 原文证据、来源定位 | planned semantic role |
| approval | 待确认、已批准、已拒绝的展示 | planned semantic role |
| degraded | 回退、缓存、部分可用 | planned semantic role |

重要状态必须同时使用文本、icon 或结构提示，不得只靠颜色。`success` 不得用于未验证候选；`AI suggestion` 不得与 verified evidence 使用相同呈现。

## 5. Typography

| 角色 | 使用原则 |
| --- | --- |
| Page title | 仅用于页面主标题，保持紧凑，不占用工作台过多首屏 |
| Section heading | 标识工作区或 detail pane 分区 |
| Body | 默认解释与操作文本，优先可读性 |
| Dense table | 更紧凑行高，仍保持可点击目标和横向扫描 |
| Metadata | 来源、时间、版本、ID、限制等次级信息 |
| Code / data | 哈希、参数、结构化结果和技术标识 |
| Evidence quote | 与解释文本区分，保留来源和定位入口 |
| Status label | 简短、明确、不可仅依赖颜色 |

工作台内标题按容器尺度使用，不使用营销 landing page 式超大标题。letter spacing 保持 `0`；不以 viewport width 连续缩放字号。

## 6. Core Components

状态含义：

- `AVAILABLE`：当前仓库存在可复用实现；
- `PARTIAL`：存在基础 primitive，但缺少 RECA semantic wrapper 或完整状态；
- `PLANNED`：设计系统目标，不代表已实现。

### 6.1 通用组件

| 组件 | 状态 | 当前说明 |
| --- | --- | --- |
| Button | AVAILABLE | `components/ui/button.tsx` |
| Input | AVAILABLE | `components/ui/input.tsx` |
| Textarea | PLANNED | 尚无共享 primitive |
| Select | AVAILABLE | `components/ui/select.tsx` |
| Search | PLANNED | 可由 Input 组合，尚无冻结 contract |
| Checkbox | AVAILABLE | `components/ui/checkbox.tsx` |
| Radio | PARTIAL | Radix dependency 已存在，尚无共享 wrapper |
| Switch | PLANNED | 尚无共享 primitive |
| Tabs | AVAILABLE | `components/ui/tabs.tsx` |
| Card | AVAILABLE | `components/ui/card.tsx` |
| Table | AVAILABLE | table primitive 与 `Common/DataTable` |
| Badge | AVAILABLE | `components/ui/badge.tsx` |
| StatusBadge | PARTIAL | 需冻结 semantic tones 与 source rules |
| Alert | AVAILABLE | `components/ui/alert.tsx` |
| Dialog | AVAILABLE | `components/ui/dialog.tsx` |
| Drawer | PARTIAL | `sheet.tsx` 可提供基础，contract 未冻结 |
| Toast | AVAILABLE | Sonner wrapper |
| Tooltip | AVAILABLE | `components/ui/tooltip.tsx` |
| Breadcrumb | PLANNED | 尚无共享 primitive |
| Pagination | AVAILABLE | `components/ui/pagination.tsx` |
| Stepper | PLANNED | 尚无共享 primitive |
| Progress | PLANNED | 尚无共享 primitive |
| Skeleton | AVAILABLE | `components/ui/skeleton.tsx` |
| EmptyState | PARTIAL | 当前 `PageState` 需扩展 |
| ErrorState | AVAILABLE | 当前 `PageState` / error components |
| PermissionState | PLANNED | 需与服务端 permission result 对接 |

### 6.2 RECA 领域展示组件

以下全部是设计分类，不代表当前工程已实现：

| 组件 | 状态 |
| --- | --- |
| ProjectStageNav | PLANNED |
| EvidenceCard | PLANNED |
| EvidenceSpanViewer | PLANNED |
| ApprovalPanel | PLANNED |
| JobProgress | PLANNED |
| DataIdentityCard | PLANNED |
| QualityIssueTable | PLANNED |
| AnalysisResultCard | PLANNED |
| ManuscriptIssueCard | PLANNED |
| EvidenceGraphNode | PLANNED |
| SourceTrace | PLANNED |
| AiSuggestionPanel | PLANNED |

领域组件只消费 ViewModel/Props 并发出 Events，不直接调用正式 API，也不保存正式业务状态。

## 7. Page Layout Patterns

| Pattern | 主要用途 | 关键约束 |
| --- | --- | --- |
| Project Workspace | 项目内主要上下文 | 保留 project scope、stage、task status 与 deep link |
| Split Pane | 文献/PDF、问题/原文 | pane 尺寸稳定，detail 可独立滚动 |
| Dense Table + Detail | 矩阵、质量、审批 | selection 是页面状态，不是业务决策 |
| Review Queue | 文献、论文问题、审批 | next item、reason、source 与 action 明确 |
| Evidence Viewer | 原文、定位、上下文 | viewer 坐标不是 EvidenceSpan 事实 |
| Analysis Workspace | plan、result、figure | 输入版本、运行、结果和解释分离 |
| Manuscript Review | issue list + source context | 不建设完整在线 Word editor |
| Evidence Graph | 关系导航与风险检查 | node/edge 是后端图数据的投影 |

页面 section 使用全宽或 unframed layout；Card 只用于独立重复项或确需边界的工具，不把每个 section 都做成浮动 card，也不嵌套装饰性 card。

## 8. Interaction States

所有 interactive component 至少定义：

```text
hover · focus-visible · active · selected · disabled · loading · error · warning · success
```

- `selected` 只表示当前 UI 选择，除非正式 action 成功返回，否则不表示已批准或已写入；
- `disabled` 应在适用时提供原因；
- loading 不改变控件稳定尺寸；
- destructive action 使用明确 icon、文案、影响说明和确认层级；
- optimistic feedback 失败时必须回滚并显示真实错误。

## 9. Accessibility

- 核心流程支持 keyboard navigation；
- 使用 `focus-visible`，焦点不得被 outline removal 隐藏；
- 表单控件有可关联 label，错误与字段建立语义关系；
- 文本与交互对比度达到基础可读性；
- 状态使用 icon + text 或等效结构，不只靠颜色；
- dense table 保持 header、row、selection 与横向滚动语义；
- dialog/drawer 管理 focus trap、初始焦点和关闭后焦点恢复；
- tooltip 不承载唯一关键信息；
- 尊重 `prefers-reduced-motion`，长任务状态不依赖持续动画理解。

## 10. Responsive Strategy

### Desktop

主要比赛与科研工作台视口。支持 dense table、split pane、PDF、graph、persistent navigation 和并行上下文。

### Tablet

保持核心查看、筛选和确认；允许 detail pane 变为 drawer 或顺序布局，避免内容重叠。

### Small screen degradation

优先保留状态查看、来源追踪、简单表单和关键审批信息。复杂 PDF/table/graph 工作台可降低同时显示的功能密度、改为单 pane 或只读摘要；不得假装与桌面等价，也不得因降级隐藏风险、来源或失败。

所有固定格式区域使用明确的 grid、min/max、overflow 或 aspect constraints，动态标签、loading 和 hover 不应使布局跳动或文字互相遮挡。

## 11. Open Design 交付检查

- 基于真实 `frontend/` 技术栈和现有 primitives；
- 未建立第二套产品工程；
- 已标明 AVAILABLE / PARTIAL / PLANNED；
- 使用冻结 ViewModel、Props、Events 和 Mock fixtures；
- 不直接调用 API，不修改 generated client；
- loading、empty、error、forbidden、degraded 等适用状态有视觉方案；
- AI suggestion、verified fact、approval 和 degraded 状态可区分；
- desktop、tablet 和 small-screen degradation 已检查；
- keyboard、focus、contrast、labels 和 reduced motion 已检查；
- token 与共享组件修改已记录影响范围；
- 设计完成未被描述为业务实现完成。
