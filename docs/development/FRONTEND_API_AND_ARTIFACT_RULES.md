# Frontend, API, and Artifact Rules

- 文档名称：Frontend, API, and Artifact Rules
- 所属入口文档：[AGENTS.md](../../AGENTS.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

本文件详细规定前端工程、OpenAPI Client、服务端状态、权限 UI、异步状态和 Artifact 交互规则。

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
- 下载使用后端授权地址，不暴露对象存储密钥；
- PDF、DOCX、数据和导出失败必须保留可重试或人工处理入口。

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

## 12. 前端完成检查

- Bun 命令通过；
- generated client 与 OpenAPI 一致；
- adapter 没有隐藏错误；
- 权限和状态来自服务端；
- Artifact 不可变交互得到保持；
- 加载、空、错误、降级和审批状态可见；
- 可访问性和响应式布局经过检查；
- 必要 Playwright 回归通过；
- 未展示虚假科研数据或已实现状态。

## 返回入口文档

返回 [AGENTS.md](../../AGENTS.md)。
