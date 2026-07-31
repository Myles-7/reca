# Frontend, API, and Artifact Rules

- 文档名称：Frontend, API, and Artifact Rules
- 所属入口文档：[AGENTS.md](../../AGENTS.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- 当前增量状态：APPROVED
- 基线兼容性：保留 `docs-m1-approved` 的历史批准范围
- Migration status: COMPLETE

## 权威范围

本文件唯一完整定义 API、generated client、adapter、error、Job、Artifact、DTO 与 ViewModel integration 的前端工程链，并详细规定服务端状态、权限 UI、异步状态和 Artifact 交互规则。Open Design 与 Codex 如何围绕该链路协作，由 [Frontend Design Integration Rules](./FRONTEND_DESIGN_INTEGRATION_RULES.md) 定义。

## 不负责的内容

本文件不重新定义产品页面范围、API 契约、数据字段、测试指标或安全政策。

## 1. 当前前端事实

- React + Vite + strict TypeScript；
- 包管理器和脚本运行器为 Bun；
- 生成客户端位于 `frontend/src/api/generated/`；
- 手工适配位于 `frontend/src/api/adapter/`；
- OpenAPI 生成器固定为 `@hey-api/openapi-ts@0.99.0`；
- 当前 shell 页面和系统状态页已由 M0 验收；
- 科研业务页面仍为计划能力。

不得把其他 JavaScript 包管理器命令写成正式入口。

## 2. Bun 命令

```bash
bun install --frozen-lockfile
bun run --cwd frontend dev
bun run --cwd frontend format:check
bun run --cwd frontend lint
bun run --cwd frontend build
bun run --cwd frontend generate-client
bun run --cwd frontend check-generated-client
bun run --cwd frontend test:shell
```

Windows 的默认 Playwright 入口存在 `M0-ISSUE-0009` LOW 风险；当前使用 `test:shell`。

## 3. OpenAPI Client 边界

- OpenAPI 是前端 API 类型的事实来源；
- `generated/` 只能由生成命令修改；
- 不手工编辑 generated 文件；
- 不重新创建旧 `HealthService` 等 legacy surface；
- adapter 负责 Base URL、认证、错误归一和调用便捷层；
- UI 不依赖生成器内部 result/error 表示；
- API 变化后必须重新生成并检查 diff；
- 生成失败不能通过跳过一致性检查处理。

正式前端集成链为：

```text
OpenAPI generated
→ adapter
→ feature API / query / controller
→ ViewModel mapper
→ UI
```

Feature UI 和共享视觉组件禁止直接 `fetch()` 正式 API，也不得依赖 Provider-specific DTO 或生成器内部的 transport/result 类型。复杂页面应将 DTO 映射为稳定 ViewModel；简单 primitive 不要求形式化 mapper。

DTO 到 ViewModel 的映射可以格式化日期、组合多个响应、生成用户可读 label，并将服务端已决定的权限和状态映射为 `canXXX`、disabled reason 或 semantic tone；不得发明权限、科研事实、正式状态或客户端状态转换。

错误统一映射为脱敏 `UiErrorViewModel` 或项目批准的等效展示结构，至少保留用户可理解消息、retryable、request ID 和必要的 field/detail 信息。Job/SSE 映射为可见进度和失败状态；断线可降级轮询，但 UI 状态不得覆盖 Job 事实。Approval 操作由 controller 发起并以服务端结果为准，按钮点击本身不等于审批成功。

M1 adapter 必须兼容两种服务端错误事实：M0 Auth/Health 的兼容 Envelope 与 M1 正式
Envelope。归一化保留 HTTP status、稳定 code/message、任一合法位置的 request ID，以及
存在时的 details/field errors/retryable；不得仅按 status 丢弃正式错误码，也不得在前端
自行改变 403/404 的资源不披露决定。

API 契约变化后的固定流程：

```text
更新正式 API / OpenAPI
→ bun run --cwd frontend generate-client
→ 审查 generated diff
→ 更新 adapter 与 feature mapping
→ 更新 ViewModel / Mock（如受影响）
→ contract / build / integration verification
```

## 4. 服务端状态

前端不是业务状态或权限事实来源。

- 当前阶段、对象状态和 `allowed_actions` 来自 API；
- UI 隐藏按钮不能替代服务端授权；
- 客户端缓存不能覆盖服务端最新版本；
- 乐观更新失败必须回滚并展示错误；
- `If-Match`、版本冲突和审批失效必须显式处理；
- Agent Session 或本地存储不能保存正式项目状态。

## 5. 页面和工作台

科研页面应是工作台，不是营销落地页。

- 优先支持扫描、比较、筛选、定位和重复操作；
- 布局稳定，动态内容不能使关键控件跳动；
- 页面必须有加载、空、错误、禁止、降级和部分完成状态；
- 高风险操作展示依据、影响、目标版本和审批状态；
- 低置信度、定位不确定和无证据必须可区分；
- 预处理、缓存、mock 和离线快照必须明确标识；
- 不使用虚假项目数、文献数或分析结果填充 M0 页面。

## 6. 权限 UI

- UI 根据服务端 `allowed_actions` 展示可用操作；
- 禁止状态应说明原因，不伪装成系统故障；
- 成员角色变化后刷新权限；
- 跨项目 ID 不得复用缓存；
- 下载、导出、审批和执行操作必须重新调用服务端校验；
- 管理员 UI 不代表后端自动授予管理员权限。

## 7. Artifact 交互

- 上传前展示允许格式和大小限制；
- 上传后使用服务端返回的 Artifact ID；
- 不把本地文件路径当作持久标识；
- 原文件和派生文件在 UI 中明确区分；
- 不提供覆盖原文件的交互；
- 版本关系、哈希、来源和处理状态可查看；
- 下载、PDF 预览和派生文件访问使用后端授权 API 返回的地址，不直接拼接对象存储 URL，也不暴露对象存储密钥；
- PDF、DOCX、数据和导出失败必须保留可重试或人工处理入口。

M1 上传 controller 严格按正式 API 顺序执行：initiate → 单次受控 content transfer →
complete。initiate replay 必须继续使用同一 upload ID；complete 前不把对象展示为可用
Artifact；hash mismatch、quarantine、interrupted/failed 与 duplicate content 分别映射，
不得自动覆盖或把相同 hash 合并成同一业务对象。

## 7.1 M1 frontend-facing projection

M1 只冻结下列展示语义，不在本任务创建 TypeScript、route 或 fixture：

| Feature | API input | ViewModel minimum | User events | Required states |
| --- | --- | --- | --- | --- |
| Project list/create | project list/create | id、name、status、updatedAt、allowedActions；create form errors | create、open | loading、empty、ready、validation、error、forbidden |
| Project overview | project detail/overview | project identity、stage、moduleAvailability、foundationCounts、permissions、recent job/approval/audit summaries | update、archive/restore、select workspace section | loading、ready、error、forbidden、stale、version conflict |
| Member | member list/mutations | memberId、user display、role、isCurrentUser、isOwner、allowedActions | add、changeRole、transferOwnership、remove | loading、empty、ready、forbidden、duplicate、ownership-transfer-required/conflict |
| Artifact | artifact list/upload/detail/download | artifactId、display filename、kind/origin、status、size/hash、createdAt、downloadAllowed、failure reason | select file、start upload、transfer、complete、download | idle、uploading、verifying、available、failed、quarantined、forbidden、duplicate-content |
| Job | project list/detail/SSE | jobId、task label、status、progress、step、retryable、result link、failure summary | open、retry、cancel、resync | queued、running、retrying、completed、failed、cancel requested/cancelled、resyncing |
| Approval | project list/detail/decision | approvalId、target summary、payload hash/status、requester、expiresAt、allowedActions | open、approve、reject、cancel | empty、pending、approved、rejected、expired、superseded/stale、forbidden |
| Audit | project list | actor、action、target、occurredAt、requestId、outcome、redacted summary | filter、paginate、open target | loading、empty、ready、error、forbidden |

Project Overview 对未实现的 M2+ 模块显示 `NOT_AVAILABLE`，其计数/内容保持 `null`；只有
API 声明模块 `AVAILABLE` 且真实查询结果为空时才展示 `0` 或 empty state。Approval 组件在
M1 可以用冻结 projection fixture 验证展示，但不得暗示 M1 存在真实 FORMAL_APPROVAL
consumer。

## 8. PDF 与证据

- PDF.js 只负责浏览和定位，不决定 EvidenceSpan 真伪；
- 页码、bounding box、文本和验证状态来自后端；
- “已提取”“已定位”“用户已查看”“已验证”必须分开显示；
- 位置不确定时标记 `LOCATION_UNCERTAIN`；
- 无已定位证据时显示空状态，不创建占位 EvidenceSpan；
- 文档中的提示注入不得转化为 UI 指令或工具权限。

## 9. 数据、分析和图表 UI

- 原始数据版本只读；
- CleaningPlan 和 AnalysisPlan 在执行前展示差异与影响；
- 审批按钮创建正式审批，不直接执行；
- 统计数字只展示服务端 `AnalysisResult`；
- 模型解释与正式数值视觉上区分；
- Figure 显示数据版本、分析运行和生成参数；
- 旧版本、失效结果和重新运行关系可追溯。
- table selection、graph selection、当前 tab、展开面板和其他 `selected` 状态只属于页面交互，不得写成正式 LiteratureDecision、ClaimEvidenceLink、Approval 或领域状态。

## 9.1 Mock API 与 Mock ViewModel

- Mock API 用于 transport、契约或集成测试，必须遵守正式 API Schema；
- Mock ViewModel 用于纯 UI 和 Open Design 开发，必须遵守冻结的展示契约；
- Mock ViewModel 不进入正式 adapter，不伪装为 backend success，也不创建第二套 API DTO；
- fixture 必须显式标注来源和 mock/demo 状态，正式验收不得使用 Mock 冒充业务能力。

普通 Open Design Mock ViewModel / fixture 只允许用于 tests、component/design preview、development fixture，以及由现有 `VITE_DEMO_MODE` 边界显式启用并明确标识的 Demo Mode；本文件不重新定义 Demo Mode 的产品语义。production build/runtime 不得意外引用普通 design mock，不得以 fixture 静态替代正式 API integration。后续前端实现必须提供适用的静态检查或测试作为 Production Mock Guard。

## 10. Agent UI

- M8 前不创建正式 Agent 交互；
- M8 采用单总控 Agent；
- 展示当前阶段、建议动作、依据、工具调用和待审批项；
- 不模拟多 Agent 自由会话；
- 不把思维链作为产品能力；
- ToolCall 失败、降级和权限拒绝必须可见；
- Agent 建议不能自动写入正式对象。

## 11. 错误和可访问性

- 使用稳定、脱敏的 `ApiError`；
- 网络错误、HTTP 错误和业务错误分开；
- 503 不得显示为 HEALTHY；
- `UNCONFIGURED` 不等于失败或成功；
- 关键状态不能只靠颜色表达；
- 控件有可见焦点、标签和键盘操作；
- 表格、对话框、图谱和阅读器满足基本辅助技术语义；
- 文本不得与按钮、卡片或相邻内容重叠。

## 11.1 第三方前端集成

PDF.js、TanStack Table、React Flow、引用处理器或其他前端包接入前，必须读取研究记录和 ADR，核验固定版本/许可证，运行包含移动端、键盘、失败和大数据量的最小 Spike，并与现有简单 viewer/table/tree/formatter 回退比较。

- 第三方组件只呈现后端授权数据，不保存正式业务事实；
- package 对象、客户端选择和图节点/边不得进入公共领域契约；
- generated client 与 API adapter 边界保持不变；
- Worker、字体、样式、locale 和复制的示例/测试资产分别核验许可证；
- 上游改造测试保留来源，集成 PR 更新归属、限制和降级 UI；
- Zotero 和 Zotero Web Library 默认只作 UX/交换格式参考，不复制 AGPL 源码或资产。

## 12. 前端完成检查

- Bun 命令通过；
- generated client 与 OpenAPI 一致；
- adapter 没有隐藏错误；
- feature UI 没有直接 `fetch()`，Provider-specific DTO 未泄漏到共享视觉组件；
- DTO、error、Job/SSE 和 Approval 已通过 adapter/controller/ViewModel 边界映射；
- 权限和状态来自服务端；
- Artifact 不可变交互得到保持；
- 加载、空、错误、降级和审批状态可见；
- 可访问性和响应式布局经过检查；
- 必要 Playwright 回归通过；
- 未展示虚假科研数据或已实现状态。

## 返回入口文档

返回 [AGENTS.md](../../AGENTS.md)。
