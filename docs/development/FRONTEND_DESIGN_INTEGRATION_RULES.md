# Frontend Design Integration Rules

| 项目 | 内容 |
| --- | --- |
| 文档名称 | `FRONTEND_DESIGN_INTEGRATION_RULES.md` |
| 文档角色 | Open Design、Codex 与开发者的前端协作主规则 |
| 文档状态 | APPROVED FOR M1 DEVELOPMENT |
| M1 Contract Amendment | APPROVED |
| 基线兼容性 | 保留 `docs-m1-approved` 的产品、API、领域、测试与 M1 Entry 基线 |
| 适用范围 | RECA 正式 `frontend/` 内的设计、UI、业务接线与集成 |
| 最后更新 | 2026-07-31 |

## 1. 权威范围

本文档唯一完整定义：

- Codex 与 Open Design 的职责边界；
- 前端目录主责与共享修改规则；
- 围绕正式 API → UI 工程链的协作边界；
- ViewModel、Component Props 与 UI Event 契约；
- Mock ViewModel 规范；
- Design Token 接入；
- Route 协作和页面状态；
- 契约冻结后的并行开发、分支集成与 UI Integration Gate。

本文档不重新定义产品 Requirement、API Path、Schema、Error Code、Tool、Enum、领域状态机、权限、Approval、Job/SSE、安全策略或里程碑范围。对应权威为：

- 产品范围：[PRODUCT_REQUIREMENTS.md](../PRODUCT_REQUIREMENTS.md)；
- UI 产品要求：[UX_NONFUNCTIONAL_AND_TRACEABILITY.md](../product/UX_NONFUNCTIONAL_AND_TRACEABILITY.md)；
- 技术架构：[ARCHITECTURE.md](../ARCHITECTURE.md)；
- API、AI 与 Tool：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)；
- 数据与正式状态：[DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)；
- 前端 API 工程规则：[FRONTEND_API_AND_ARTIFACT_RULES.md](./FRONTEND_API_AND_ARTIFACT_RULES.md)；
- 视觉系统：[frontend/DESIGN.md](../../frontend/DESIGN.md)；
- 交付流程：[DELIVERY_WORKFLOW.md](../roadmap/DELIVERY_WORKFLOW.md)；
- 全仓强制规则：[AGENTS.md](../../AGENTS.md)。

设计稿、Mock 页面或组件完成不等于 Requirement 已实现、API 已实现、里程碑已通过。

## 2. 当前工程事实与目标边界

当前真实前端使用 React、Vite、strict TypeScript、Bun、TanStack Router、TanStack Query、Tailwind CSS、Radix UI primitives 与 Lucide icons。当前主要结构包括：

```text
frontend/src/
├── api/
│   ├── generated/        # OpenAPI generator-only
│   └── adapter/          # 手工传输、认证、错误和兼容边界
├── components/
│   ├── ui/               # 已有共享视觉 primitives
│   ├── Common/
│   ├── Sidebar/
│   └── ...
├── features/
│   └── system-status/    # 当前已实现的 M0 feature
├── hooks/
├── routes/               # TanStack Router file routes
├── shared/
├── main.tsx              # Provider 与 Router 装配
└── index.css             # 当前 CSS variables / Tailwind token source
```

目标协作边界不是本任务要求立即迁移的目录模板。后续 feature 可在实际实现时形成 `api/`、`model/`、`hooks/`、`containers/`、`ui/` 等子边界；不得为匹配示例而批量移动现有文件或创建空目录。

## 3. 协作引用的数据流

API、generated client、adapter、error、Job、Artifact、DTO 与 ViewModel integration 的唯一完整工程规则由 [Frontend, API, and Artifact Rules](./FRONTEND_API_AND_ARTIFACT_RULES.md) 定义。本文档只规定 Codex 与 Open Design 如何围绕该链路协作。

正式业务页面的数据流为：

```text
Backend
→ OpenAPI
→ frontend/src/api/generated/
→ frontend/src/api/adapter/
→ feature API / query / controller
→ ViewModel mapper
→ Page / UI Component
```

禁止以下旁路：

```text
UI Component → fetch() → backend
Open Design → generated client
Backend DTO → 大量直接散布到纯视觉组件
```

复杂业务页面原则上通过 ViewModel 或等效展示模型隔离。简单、稳定且无业务语义的最小组件可直接使用基础 props，不要求为形式完整建立 mapper。

## 4. 职责与所有权

### 4.1 Codex 主责

- Router、正式 route semantics 与 route params；
- Provider、Auth integration 与全局错误边界；
- OpenAPI generated client 和生成流程；
- API adapter、错误归一化与兼容处理；
- feature query、mutation、controller 与 ViewModel mapper；
- 服务端权限结果、Job/SSE、Approval action 和正式状态的 UI 映射；
- API integration、contract、Playwright 与 E2E；
- 与正式 Domain、Service、API 契约和测试基线同步。

### 4.2 Open Design 主责

- Design System 与 Design Token；
- layout、page visual composition 与 reusable UI component；
- typography、spacing、semantic presentation 与 responsive behavior；
- loading、empty、error、forbidden、degraded 等状态的视觉表达；
- 基于冻结 ViewModel 和 Mock fixture 的纯 UI 页面；
- keyboard、focus-visible、contrast、reduced motion 等视觉可访问性。

### 4.3 Open Design 禁止

- 直接调用正式后端 API 或手写正式 API DTO；
- 修改 `frontend/src/api/generated/` 或绕过 `adapter/`；
- 自建认证、权限、Approval 或业务状态机；
- 把 button state 当作 `ApprovalRecord`；
- 把 table selection 当作 `LiteratureDecision`；
- 把 React Flow edge 当作证据关系事实；
- 把 PDF viewer 坐标自动当作 `EvidenceSpan`；
- 把 Mock、demo fixture 或视觉状态写成正式科研事实；
- 发明新的正式 URL 语义；
- 建立第二套 Vite/React 产品工程替代 `frontend/`。

### 4.4 目录主责矩阵

| 区域 | 主责 | 修改规则 |
| --- | --- | --- |
| `backend/**` | Codex | Open Design 不修改 |
| `frontend/src/api/generated/**` | generator-only | 只通过正式生成命令修改 |
| `frontend/src/api/adapter/**` | Codex | Open Design 不依赖其内部传输表示 |
| `frontend/src/routes/**`、`main.tsx` | Codex | Navigation 视觉可协作，route semantics 需工程审查 |
| feature API/model/query/controller | Codex | 对 UI 暴露冻结 ViewModel 与 event contract |
| feature page composition / `ui` | Open Design 主责 | 不直接访问 API，不持有正式状态 |
| `frontend/src/components/ui/**` | Open Design 主责 | 冻结后改动需评估跨页面影响 |
| `frontend/src/index.css`、未来 design-system | Open Design 主责 | Token 变更需视觉审查，不写业务逻辑 |
| shared layout / Common components | 协同 | 先指定单一修改人；Props 变化需双方审查 |
| integration / E2E tests | Codex | Open Design 提供视觉验收输入 |

共享文件采用“单一主修改人 + Review”规则。并行分支不得同时大范围重写 route、layout、token source 或共享组件。

### 4.5 可执行 UI Contract 落点

TypeScript 是 UI Contract 的可执行事实来源；Markdown 只解释语义、owner、dependency、freeze 状态和 integration notes。

在 production implementation 尚被 Contract Amendment approval 阻塞时，Markdown 可将
Route、ViewModel、Props/Event 和 Mock semantics 标为 `FROZEN`，表示语义已足够
审查和并行设计，但不表示文件存在或功能实现。批准后，Codex 必须将其落实为 TypeScript；
一旦 TypeScript 存在，它重新成为唯一可执行事实来源。不得为了把 registry 填成
`FROZEN` 而预建空文件。

| Contract | 可执行事实来源 | Markdown 职责 |
| --- | --- | --- |
| Route | `frontend/src/routes/` 中真实 TanStack Router route 定义，以及必要的 feature integration documentation | 记录 owner、里程碑、freeze 状态；未冻结 route 写 `TBD` |
| ViewModel | feature 内的 TypeScript `interface` / `type` 与 mapper 输入输出 | 解释字段语义和正式来源，不长期复制完整类型 |
| Component Props / Events | 对应 React component 的 TypeScript props；复杂页面可抽取共享 contract 文件 | 记录 contract owner、review 与 breaking change |
| Mock ViewModel | 导入正式 ViewModel 类型的 typed fixture | 记录 fixture 用途、覆盖状态和 production guard |

当前工程只有 `features/system-status/` 形成实际 feature。后续复杂 feature 可在真实实现时采用：

```text
frontend/src/features/<feature>/
├── model/
│   ├── view-model.ts
│   └── contracts.ts
├── ui/
└── mocks/
```

也可按 feature 规模使用 `<feature>.view-model.ts`、`<feature>.contracts.ts` 和 `*.mock.ts` 共置。选择应服从当前 feature 风格，不要求本任务创建目录或移动文件。

## 5. ViewModel Contract

ViewModel 用于隔离后端 DTO / Domain State 与纯展示 UI。它是前端展示合同，不是新的公共 API Schema，也不是第二套领域模型。

正式 ViewModel 必须在 feature TypeScript source 中定义，并由 mapper 或 controller 产生。本文档不复制可执行类型，避免 Markdown 与代码漂移。

ViewModel 可以：

- 组合多个 API DTO；
- 格式化日期、数量和用户可读 label；
- 将正式状态映射为 semantic tone；
- 传递服务端已决定的 `canXXX` 或 disabled reason；
- 暴露来源、stale、degraded 和 partial 等展示信息。

ViewModel 不得：

- 发明科研事实、权限或正式状态；
- 替代服务端审批；
- 在浏览器创建正式状态转换；
- 隐藏来源不确定、失败或降级；
- 让 Provider-specific DTO 成为 UI 公共依赖。

## 6. Component Contract

关键业务页面组件优先采用：

```text
Props in
Events out
```

正式 Props / Event contract 由 React component 的 TypeScript props 或 feature contract 文件定义。组件负责呈现 props、发出用户意图并展示可访问状态；Controller 负责把事件接到 query、mutation、Service/API 结果和重新加载逻辑。Event 的存在不表示 UI 有权决定正式确认结果。

契约冻结至少记录：

- Route 与必要 params；
- ViewModel types 与字段来源；
- Props、events、loading/error semantics；
- disabled/permission reason；
- Mock fixture 名称；
- 视觉 token 或组件依赖；
- 变更负责人和验证方式。

## 7. Mock Contract

Open Design 可使用 Mock ViewModel 独立运行页面。后续需要共享 fixture 时，优先放在 `frontend/src/mocks/` 或 feature 内明确命名的 `*.mock.ts` / `fixtures/`；创建位置必须随真实实现落地，不为本规则预建空目录。

Mock 必须：

- 基于冻结 ViewModel，而不是复制后端 DTO；
- 明确标注 `mock`、`demo` 或 `fixture`；
- 不进入正式 adapter，不伪装成 backend success；
- 不包含真实用户或未授权科研数据；
- 不被正式验收当作业务实现证据；
- 覆盖页面适用的成功与失败状态。

状态库按页面能力裁剪：

```text
SUCCESS
LOADING
EMPTY
ERROR
FORBIDDEN
DEGRADED
PARTIAL
STALE
JOB_RUNNING
JOB_FAILED
APPROVAL_REQUIRED
```

Mock API 用于传输/契约测试；Mock ViewModel 用于纯 UI 开发。两者不得混为正式 API adapter，也不得构成第二套公共 DTO。

### 7.1 Production Mock Guard

普通 Open Design Mock ViewModel / fixture 允许用于 tests、component/design preview、development fixture，以及由当前 `VITE_DEMO_MODE` 边界显式启用并明确标识的 Demo Mode。本文档不重新定义 Demo Mode 的产品语义。

禁止：

- 普通 design mock 被 production code path 未标记引用；
- fixture 静态替代正式 API integration；
- 正式科研结果页面误用 Mock；
- Mock 被正式验收当作 backend success。

Production build/runtime 应有静态检查或测试，防止普通 design mock 意外进入正式数据路径。具体实现由后续前端任务完成。

## 8. Route 协作

- 当前 Router 为 TanStack Router file-based routes；
- Router 和正式 URL 语义由 Codex/工程契约主责；
- Open Design 可设计 navigation、breadcrumb 和 stage navigation；
- 页面必须接收正式 route params，项目资源保留 `projectId` 等作用域；
- deep link 与刷新后上下文恢复必须由正式 route、query 和 API 结果支持；
- forbidden、not found、stale 等结果由正式 API 决定；
- 未冻结路径只能标为示意，不得写成 Requirement 或 API 事实。

### 8.1 M1 Route Contract

本次 amendment 冻结 M1 浏览器 route（TanStack Router source 文件在后续实现创建）：

| Browser URL | Route param | Responsibility |
| --- | --- | --- |
| `/projects` | none | project list 与 create entry |
| `/projects/$projectId` | `projectId` UUID | project-scoped workspace；Member、Artifact、Job、Approval、Audit 使用内部 section/tab，不新增稳定 browser URL |

刷新与 deep link 必须从 `projectId` 重新获取授权后的 Project Overview；未知或不可披露项目
显示 not found，已知成员缺少某个 action 只禁用相应 command。section/tab 可以是本地 UI
状态或兼容 query parameter，但本轮不把 query parameter 冻结为 stable route contract。

### 8.2 M1 Component / Event Contract

Project Workspace 的语义输入采用
[Frontend, API, and Artifact Rules](./FRONTEND_API_AND_ARTIFACT_RULES.md#71-m1-frontend-facing-projection)
定义的七类 projection。组件只发出 `createProject`、`updateProject`、`manageMember`、`transferOwnership`、
`uploadArtifact`、`downloadArtifact`、`retryJob`、`cancelJob`、`decideApproval`、
`cancelApproval`、`filterAudit` 和 `refresh` 用户意图；controller 执行正式 API、处理
Idempotency-Key/If-Match 并重新映射服务端结果。

Mock contract 必须覆盖 loading、empty、ready、error、forbidden、stale、pending、degraded，
以及 Artifact mismatch/interruption、Job resync/failure、Approval expired/superseded。fixture
明确标注 `M1_CONTRACT_MOCK`，Approval fixture 不代表真实 M1 consumer。

## 9. 页面状态

重要页面至少评估：

```text
loading · empty · ready · error · forbidden · degraded · partial · disabled · stale
```

异步页面额外评估：

```text
queued · running · retrying · completed · failed · cancelled
```

审批页面仅在正式领域支持时映射：

```text
approval required · pending · approved · rejected · expired/stale
```

这些是展示状态集合，不替代后端 Enum。每个展示状态必须可追溯到 API 结果、Controller 状态或明确的本地交互状态。

## 10. Design Token 接入

视觉实现以 [frontend/DESIGN.md](../../frontend/DESIGN.md) 和项目统一 token source 为准。当前 token source 是 `frontend/src/index.css` 中的 CSS variables 与 Tailwind theme mapping。

页面避免重复硬编码 color、font-size、spacing、radius、border、shadow、z-index 和 motion。必要例外应局部、可说明且不形成第二套视觉系统。业务逻辑文件不得定义视觉系统。

## 11. 并行开发与合并

标准流程：

```text
1. Requirement 与领域契约确认
2. Route / ViewModel / Component Contract Freeze
3. Open Design 与 Codex 在明确主责范围并行
4. Open Design 使用 Mock ViewModel 完成 UI
5. Codex 完成 API / adapter / controller / mapper
6. Integration
7. Component / Contract / E2E Test
8. Visual + Functional Review
9. Merge
```

禁止两边各自生成完整前端后在项目结束时一次性合并。分支应围绕同一冻结 contract，尽早以小批量集成验证 props、events、route 和 states。

设计变更分级：

| 变更 | 处理 |
| --- | --- |
| 纯视觉或 token | Design 层修改与视觉审查 |
| Component Props / Event | UI contract review |
| ViewModel | Codex + Open Design review，更新 mapper 与 Mock |
| API / Schema / Error Code | 正式 API Contract 流程并重新生成 client |
| Requirement / Milestone | 正式产品或路线图变更流程 |

## 12. UI Integration Gate

页面只有在适用项满足后才算完成设计接入：

- Route 可访问，params 与 deep link 行为正确；
- Props 与 ViewModel 类型检查通过；
- Mock 页面通过；
- real API mapping 通过；
- loading、empty、error 可见；
- forbidden、degraded、partial、stale 在适用时可见；
- UI 无直接 `fetch()`；
- generated client 未被手改；
- 权限和正式状态不由 UI 自行判断；
- Approval、Job/SSE 和状态转换经过 Controller / Service 边界；
- Artifact/PDF 使用授权 API 地址；
- keyboard、focus、label、contrast 与 reduced motion 经过检查；
- TypeScript build、lint、format 通过；
- 关键 component/contract/E2E 通过；
- 视觉审查和功能审查结论均已记录。

Gate 通过只证明该页面已按已实现契约集成，不自动证明整个 Requirement 或 Milestone 完成。

## 13. UI Contract Registry

Registry 记录协作准备度，不是领域状态机。`AVAILABLE`、`DRAFT`、`READY_FOR_DESIGN`、`FROZEN`、`PLANNED`、`NOT_STARTED`、`INTEGRATING`、`INTEGRATED` 仅用于本表。

| Feature / Workspace | Milestone | Route Contract | ViewModel Contract | UI Contract | Mock | Design Status | Integration Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Public shell / home | M0 | `AVAILABLE` | local presentation only | `AVAILABLE` | `NOT_STARTED` | `AVAILABLE` | `INTEGRATED` |
| Auth / account / admin | M0 | `AVAILABLE` | adapter DTO usage; no frozen feature VM | `AVAILABLE` | `NOT_STARTED` | `AVAILABLE` | `INTEGRATED` |
| System Status | M0 | `/system-status` `AVAILABLE` | local TypeScript display model `AVAILABLE` | `AVAILABLE` | `NOT_STARTED` | `AVAILABLE` | `INTEGRATED` |
| Project Workspace | M1 | `/projects`, `/projects/$projectId` `FROZEN` | semantic projection `FROZEN`; TypeScript `NOT_STARTED` | events/states `FROZEN` | fixture semantics `FROZEN`; files `NOT_STARTED` | `READY_FOR_DESIGN` after amendment approval | `NOT_STARTED` |
| Research Question | M2 | `TBD` | `NOT_STARTED` | `NOT_STARTED` | `NOT_STARTED` | `PLANNED` | `NOT_STARTED` |
| Literature / PDF Workspace | M2-M3 | `TBD` | `NOT_STARTED` | `NOT_STARTED` | `NOT_STARTED` | `PLANNED` | `NOT_STARTED` |
| Data Quality Workspace | M4 | `TBD` | `NOT_STARTED` | `NOT_STARTED` | `NOT_STARTED` | `PLANNED` | `NOT_STARTED` |
| Analysis / Figure Workspace | M5 | `TBD` | `NOT_STARTED` | `NOT_STARTED` | `NOT_STARTED` | `PLANNED` | `NOT_STARTED` |
| Manuscript Review | M6 | `TBD` | `NOT_STARTED` | `NOT_STARTED` | `NOT_STARTED` | `PLANNED` | `NOT_STARTED` |
| Evidence Graph / Export | M7 | `TBD` | `NOT_STARTED` | `NOT_STARTED` | `NOT_STARTED` | `PLANNED` | `NOT_STARTED` |
| Agent Workspace | M8 | `TBD` | `NOT_STARTED` | `NOT_STARTED` | `NOT_STARTED` | `PLANNED` | `NOT_STARTED` |

Open Design 只有在对应行的 Route、ViewModel、UI 与 Mock contract 达到任务要求的 `READY_FOR_DESIGN` 或 `FROZEN` 后，才可将该页面视为正式并行开发；`PLANNED` 只允许视觉探索，不表示 contract 已冻结。

### 13.1 M1 Open Design readiness

| Feature | API frozen | ViewModel frozen | Route frozen | Mock contract frozen | Open Design ready |
| --- | --- | --- | --- | --- | --- |
| Project | YES | YES | YES | YES | YES, after Project Owner approval |
| Member | YES | YES | project workspace section | YES | YES, after Project Owner approval |
| Artifact | YES | YES | project workspace section | YES | YES, after Project Owner approval |
| Job | YES | YES | project workspace section | YES | YES, after Project Owner approval |
| Approval | YES | YES | project workspace section | YES | YES, after Project Owner approval; projection only |
| Audit | YES | YES | project workspace section | YES | YES, after Project Owner approval |

`Open Design ready=YES` 只表示 contract 足以并行设计；typed fixtures、route source、real API
mapping 和 production integration 均仍为 `NOT_STARTED`。

Registry 更新必须引用真实 TypeScript/route/fixture 路径。不得为了填表创建空文件、发明 URL 或把设计稿状态写成业务完成状态。

## 14. 最终自审

完成 Open Design 接入前确认：

- Open Design 可仅依赖 Mock ViewModel 与 Component Contract 完成纯 UI；
- Codex 可仅依赖正式 API 与 ViewModel Contract 完成业务接线；
- generated 仍为 generator-only，adapter 仍为兼容边界；
- UI、Mock、table/PDF/graph selection 不拥有后端事实；
- 可执行 ViewModel、Props/Event 与 Mock contract 位于 TypeScript source，Registry 只记录状态；
- 普通 design mock 不进入未标记 production path；
- 没有第二套 API DTO、状态机或独立前端工程；
- Design System 独立于业务逻辑；
- 契约冻结后才并行，且共享高冲突文件有单一主修改人；
- Requirement、API、Schema、Tool、Enum、Milestone 与 M0 regression baseline 未被改变。
