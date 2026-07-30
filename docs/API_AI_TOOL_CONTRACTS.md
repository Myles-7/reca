# 研证链 AI（RECA）API、AI Schema 与 Agent Tool 契约

> 面向高校科研训练的全流程可信科研智能体
> Research Evidence Chain Agent

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档名称 | `API_AI_TOOL_CONTRACTS.md` |
| 文档版本 | 1.2.0 |
| 文档状态 | Conditional Approval |
| 文档类型 | API、AI Schema 与 Agent Tool 契约入口 |
| 最后更新时间 | 2026-07-30 |

# 1. 文档目的

本入口文档定义契约权威边界、基础 API 约定、请求头以及公共响应、错误、权限、Job/SSE、AI Envelope、Tool、兼容性和 OpenAPI 生成规则的摘要。所有资源路径、错误码、AI Schema 和 Tool 的完整定义只存在于对应子契约。

# 2. 契约权威性

## 2.1 本文档负责

本文档是以下内容的唯一正式基准：

* REST API 路径；
* HTTP Method；
* 请求 Schema；
* 响应 Schema；
* 公共错误结构；
* 分页、排序与过滤；
* 身份认证头；
* 幂等头；
* 乐观锁；
* 异步 Job 协议；
* SSE 事件结构；
* AI 输出 Schema；
* AI 输出公共 Envelope；
* 智能体白名单工具；
* 工具参数和返回结构；
* 工具审批和副作用；
* 契约版本兼容规则。

## 2.2 本文档不负责

| 内容         | 权威文档                          |
| ---------- | ----------------------------- |
| 功能范围       | `PRODUCT_REQUIREMENTS.md`     |
| 数据对象含义     | `DATA_MODEL_AND_WORKFLOW.md`  |
| 技术实现方式     | `ARCHITECTURE.md`             |
| 测试和验收      | `TEST_AND_ACCEPTANCE.md`      |
| 安全和开源合规    | `SECURITY_AND_OPEN_SOURCE.md` |
| Codex 行为约束 | `AGENTS.md`                   |

## 2.3 契约优先原则

当代码与本文档不一致时：

* 前端不得通过猜测适配后端；
* 后端不得临时返回未定义字段；
* Agent 不得读取自由文本代替结构化对象；
* 应修改代码或正式更新本文档；
* 所有破坏性变更必须提高 API 或 Schema 版本。

---

# 3. 契约设计原则

## 3.1 API 资源化

API 围绕领域资源设计：

* Projects；
* Research Questions；
* Literature；
* Documents；
* Datasets；
* Analysis；
* Figures；
* Manuscripts；
* Evidence；
* Approvals；
* Jobs；
* Exports；
* Agent Runs。

## 3.2 计划、审批、执行和结果分离

不得使用一个 API 同时完成：

```text id="xd04oi"
生成建议
→ 自动批准
→ 执行修改
→ 写入正式结果
```

必须拆分为：

```text id="1rhp58"
创建计划
→ 获取预览
→ 请求批准
→ 用户批准
→ 执行
→ 获取结果
```

## 3.3 同步与异步分离

轻量操作同步返回。

耗时操作必须返回 Job。

## 3.4 AI 输出不是业务事实

AI 输出需要：

1. Schema 校验；
2. 来源校验；
3. 业务规则校验；
4. 必要时人工确认；
5. 再转化为正式业务对象。

## 3.5 数字由确定性程序提供

正式统计数字只能从 `AnalysisResult` API 获取。

AI 输出不得成为数字事实来源。

## 3.6 所有高风险操作可审计

API 和工具调用必须关联：

* `request_id`；
* `project_id`；
* `user_id`；
* `job_id`；
* `agent_run_id`；
* `tool_call_id`；
* `approval_record_id`。

## 3.7 幂等优先

以下操作必须支持幂等：

* 文件上传确认；
* 异步任务提交；
* 数据转换执行；
* AnalysisRun 创建；
* 图表生成；
* DOCX 检查；
* 复现包导出；
* Agent 工具调用。

## 3.8 明确失败

不得返回：

```json id="xqwy4d"
{
  "success": false
}
```

而无错误码、原因和重试提示。

## 3.9 来源 ID 必须保留

所有重要 AI 和工具结果必须包含来源对象 ID。

## 3.10 Schema 可版本化

AI Schema、API DTO、SSE Event 和 ReproPackage Manifest 必须拥有版本。

---

# 4. API 基础约定

## 4.1 API 前缀

```text id="1ogght"
/api/v1
```

## 4.2 内容类型

请求：

```http id="kcepuj"
Content-Type: application/json
```

文件上传：

```http id="e24nrr"
Content-Type: multipart/form-data
```

SSE：

```http id="2znj4i"
Accept: text/event-stream
```

## 4.3 字符编码

统一使用 UTF-8。

## 4.4 日期时间

API 使用 ISO 8601 UTC：

```text id="ac7o8e"
2026-07-29T08:30:00Z
```

不得返回无时区时间。

## 4.5 ID

所有业务资源 ID 使用 UUID 字符串：

```text id="ub8e8b"
550e8400-e29b-41d4-a716-446655440000
```

## 4.6 布尔值

只使用：

```text id="8xpmw8"
true
false
```

不得使用 `0/1` 或字符串 `"true"`。

## 4.7 空值

无值使用 `null`。

空数组与未知值应区分：

```json id="mx11vd"
{
  "authors": [],
  "publication_year": null
}
```

## 4.8 金额

RECA 0.1 不包含金额型核心业务字段。

## 4.9 语言

用户可见消息默认中文。

枚举和错误码使用英文大写标识。

---

# 5. 请求头

## 5.1 Authorization

```http id="7g5125"
Authorization: Bearer <access_token>
```

## 5.2 X-Request-ID

客户端可提交：

```http id="0uk505"
X-Request-ID: <uuid>
```

未提交时由服务端生成。

所有响应返回：

```http id="y6ys8t"
X-Request-ID: <uuid>
```

## 5.3 Idempotency-Key

创建高风险或异步操作时使用：

```http id="bvtjvn"
Idempotency-Key: <uuid-or-stable-string>
```

适用：

* 数据转换；
* 分析执行；
* 图表生成；
* DOCX 检查；
* 导出；
* 文档解析；
* Agent 工具执行。

## 5.4 If-Match

修改可编辑资源时使用乐观锁：

```http id="l0efwm"
If-Match: "7"
```

其中 `7` 为 `lock_version`。

版本冲突返回：

```text id="tgvy89"
409 RESOURCE_VERSION_CONFLICT
```

## 5.5 X-Project-ID

一般不要求通过 Header 提交项目 ID，项目 ID 应体现在路径中。

仅内部工具调用可使用上下文注入，不对公共前端暴露。

---

# 6. 公共响应与错误摘要

同步单资源、列表、删除和异步接受响应必须使用统一 Envelope。公共错误必须包含稳定错误码、消息、字段错误、请求 ID、可重试性和必要详情；不得返回堆栈、密钥、原始 Provider 响应或敏感输入。

公共 DTO、HTTP 状态、完整错误码清单和 M0 健康响应由 [COMMON_API_JOB_AND_SSE_CONTRACTS.md](contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md) 唯一定义。

# 7. 权限、分页、幂等与并发摘要

所有项目资源必须由 Service 校验用户、项目成员关系、对象归属和操作权限。前端权限提示不是安全边界。

列表接口使用统一分页、排序、过滤和搜索约定。创建运行、执行计划、生成图表、导出和其他可重试副作用必须支持 Idempotency-Key；可编辑对象使用 If-Match 或等效版本检查，冲突必须显式失败。

完整规则见 [COMMON_API_JOB_AND_SSE_CONTRACTS.md](contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md)。

# 8. Job 与 SSE 摘要

耗时操作返回 Job 引用，不在 API 请求内同步执行。Job 状态、结果、取消、重试和 SSE 事件必须保持项目隔离、幂等、断线恢复和审计；SSE 不得成为绕过权限的旁路。

M0 仅实现健康 API 和无业务副作用的 Worker smoke，不存在正式 Job 业务。完整定义见 [COMMON_API_JOB_AND_SSE_CONTRACTS.md](contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md)。

# 9. AI 公共 Envelope 摘要

关键 AI 输出必须经过登记的 PromptContract 和严格输出 Schema。公共 Envelope 至少承载任务类型、Schema 版本、结果、置信度、来源 ID、限制、人工复核要求和可追溯信息。解析失败、来源缺失、数字来源错误或 Schema 不匹配不得写入业务表。

Prompt manifest、ModelInvocation、所有 AI 输出 Schema、校验和降级结构只在 [AI_SCHEMA_CONTRACTS.md](contracts/AI_SCHEMA_CONTRACTS.md) 完整定义。

# 10. Agent Tool 公共规则摘要

Agent 只能调用登记的白名单 Tool。Tool 必须声明输入输出 Schema、版本、权限、项目状态、前置条件、副作用、审批、幂等、审计和数据访问上限，并且只能通过 Service 访问业务能力。

禁止任意代码、Shell、SQL、文件系统、未登记网络请求、直接数据库 Session 和绕过 Approval。全部 Tool 名称和完整合同只在 [AGENT_TOOL_CONTRACTS.md](contracts/AGENT_TOOL_CONTRACTS.md) 定义。

# 11. 版本兼容与 OpenAPI Client 边界

向后兼容变更不得删除字段、改变语义或扩大权限；破坏性 API、AI Schema 或 Tool 变更必须创建新版本并执行契约测试。OpenAPI 是前端生成客户端的可执行来源。

生成代码仅位于 `frontend/src/api/generated/`，不得手工修改；Base URL、认证、错误归一化和兼容逻辑位于 `frontend/src/api/adapter/`。完整版本、审计和生成规则见 [COMMON_API_JOB_AND_SSE_CONTRACTS.md](contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md)。

# 12. 契约所有权矩阵

| 契约类型 | 完整定义位置 | 入口允许内容 |
| --- | --- | --- |
| 公共响应和错误 | Common 子契约 | 结构和失败原则摘要 |
| 权限、分页、幂等和并发 | Common 子契约 | 强制边界摘要 |
| Job、SSE 和 Health | Common 子契约 | 同步/异步边界摘要 |
| 项目、研究、文献、审批和 AgentRun API | Project/Research/Literature 子契约 | 资源范围索引 |
| 数据、质量、分析和图表 API | Data/Analysis/Figure 子契约 | 资源范围索引 |
| 论文、Claim、证据和导出 API | Manuscript/Evidence/Export 子契约 | 资源范围索引 |
| AI Envelope、Prompt 和输出 Schema | AI Schema 子契约 | 治理原则摘要 |
| 白名单 Tool | Agent Tool 子契约 | 权限和副作用红线摘要 |
| 兼容性旧参数别名 | 对应资源子契约的兼容性索引 | 不复制别名 |
| Adapter Protocol | Common 子契约 | generated/adapter 边界摘要 |

API Path 只能在对应资源子契约完整定义。公共错误码清单只能在 Common 子契约完整定义。AI Schema 和 Tool 名称分别只能在 AI Schema 与 Agent Tool 子契约完整定义。

# 13. 契约执行顺序

一次 API、模型或 Tool 请求必须按以下顺序处理：

1. 解析并验证请求头、内容类型和基础 Schema；
2. 认证调用者；
3. 校验项目成员关系和对象归属；
4. 校验资源当前状态和允许动作；
5. 校验乐观锁、幂等键和审批前置条件；
6. 计算最小必要数据访问范围；
7. 调用 Service 或已登记 Adapter；
8. 对外部响应执行转换和严格 Schema 校验；
9. 在同一业务边界记录结果对象和审计引用；
10. 返回公共响应或公共错误 Envelope。

任何步骤失败都必须停止后续副作用。模型、外部 Provider、前端或文档内容不能改变这个顺序。

# 14. 失败与降级原则

契约失败必须可分类、可追踪且默认安全：

* 输入 Schema 失败不进入 Service；
* 权限和项目隔离失败不披露目标资源是否存在；
* 乐观锁冲突不静默覆盖；
* 幂等冲突返回原结果或明确冲突，不重复执行；
* 审批不足时进入等待或拒绝，不执行副作用；
* 外部 Provider 失败必须映射为内部错误或显式降级；
* AI 输出 Schema 失败不得部分写入；
* Tool 输出失败必须记录 ToolCall 状态；
* SSE 失败可以降级轮询，但不能丢失 Job 事实状态；
* 未配置能力不得伪装为可用；
* 缓存结果、Recorded 响应和离线快照必须明确标识；
* 回退不得扩大权限、数据访问或工具范围；
* 任何失败不得修改原始 Artifact 或已完成的不可变版本。

# 15. 契约变更流程

任何 Path、Error Code、Schema、Tool、枚举或公共字段变化必须：

1. 确认唯一权威子契约；
2. 更新对应领域模型和产品需求引用；
3. 判断是否向后兼容；
4. 对破坏性变化创建新版本；
5. 更新 OpenAPI 或 Prompt/Tool 注册表；
6. 重新生成并校验前端客户端；
7. 增加或更新契约测试和黄金测试；
8. 验证项目隔离、审批、幂等和审计；
9. 更新迁移、发布和降级说明；
10. 比较稳定标识基线，确认无意外删除、重命名或重复完整定义。

不得为了让文档“更整齐”而合并旧别名、重命名错误码或统一历史参数占位符。发现旧契约重复、别名或缺口时，应记录为未决问题并等待正式决定。

契约评审必须同时覆盖实现方、调用方、权限与项目隔离、失败路径、审计证据和向后兼容影响。任何一方尚未确认时，契约状态不能被描述为已完成。

评审结论必须能够由契约测试或明确的人工证据复核。

# 16. 子契约导航

* [COMMON_API_JOB_AND_SSE_CONTRACTS.md](contracts/COMMON_API_JOB_AND_SSE_CONTRACTS.md)：公共 DTO、错误、权限、幂等、并发、Job、SSE、健康 API、兼容性和 Adapter Protocol。
* [PROJECT_RESEARCH_AND_LITERATURE_API.md](contracts/PROJECT_RESEARCH_AND_LITERATURE_API.md)：项目、研究问题、文献、文档、EvidenceSpan、审批和 AgentRun 资源 API。
* [DATA_ANALYSIS_AND_FIGURE_API.md](contracts/DATA_ANALYSIS_AND_FIGURE_API.md)：数据、质量、清洗、分析和图表 API。
* [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](contracts/MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)：论文、Claim、证据图、审核与导出 API。
* [AI_SCHEMA_CONTRACTS.md](contracts/AI_SCHEMA_CONTRACTS.md)：Prompt、ModelInvocation、AI 输出和降级 Schema。
* [AGENT_TOOL_CONTRACTS.md](contracts/AGENT_TOOL_CONTRACTS.md)：白名单 Tool、审批、状态、数据访问与审计。

本入口与六份子契约共同构成正式开发基准。入口只负责公共决策、红线和索引；完整定义发生冲突或重复属于文档缺陷，开发者和 Codex 不得自行猜测。
