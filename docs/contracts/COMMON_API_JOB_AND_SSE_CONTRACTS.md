# COMMON_API_JOB_AND_SSE_CONTRACTS

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- Migration status: COMPLETE
- M1 Contract Amendment status: APPROVED

## 权威范围

公共响应 DTO、错误码、分页、权限、Idempotency、If-Match、M0 Health API、Job、SSE、版本兼容、审计、契约测试、OpenAPI 生成和内部 Adapter Protocol。

## 不负责的内容

不完整定义业务资源 API、AI 输出 Schema 或 Agent Tool；资源路径只能在对应资源子契约完整定义。

## 文档导航

- 返回 [API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- [COMMON_API_JOB_AND_SSE_CONTRACTS.md](COMMON_API_JOB_AND_SSE_CONTRACTS.md)
- [PROJECT_RESEARCH_AND_LITERATURE_API.md](PROJECT_RESEARCH_AND_LITERATURE_API.md)
- [DATA_ANALYSIS_AND_FIGURE_API.md](DATA_ANALYSIS_AND_FIGURE_API.md)
- [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)
- [AI_SCHEMA_CONTRACTS.md](AI_SCHEMA_CONTRACTS.md)
- [AGENT_TOOL_CONTRACTS.md](AGENT_TOOL_CONTRACTS.md)

以下正文由原入口文档对应章节机械迁入。路径、字段、错误码、Schema、Tool 名称和契约语义保持原样。


# 6. 公共响应结构

## 6.1 单资源响应

```json id="j0f4ce"
{
  "data": {
    "id": "uuid",
    "type": "research_project",
    "attributes": {}
  },
  "meta": {
    "request_id": "uuid",
    "schema_version": "1.0"
  }
}
```

RECA 0.1 不要求严格实现 JSON:API 标准，但响应应保持：

* `data`；
* `meta`；
* 可选 `links`。

## 6.2 列表响应

```json id="tc3h8y"
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 126,
    "total_pages": 7,
    "has_next": true,
    "has_previous": false
  },
  "meta": {
    "request_id": "uuid",
    "schema_version": "1.0"
  }
}
```

## 6.3 删除响应

软删除成功：

```http id="v12i4b"
204 No Content
```

需要返回影响信息时可使用：

```json id="awjmkx"
{
  "data": {
    "id": "uuid",
    "status": "DELETED",
    "affected_objects": 8
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

## 6.4 异步任务响应

```json id="474nx2"
{
  "data": {
    "job_id": "uuid",
    "resource_type": "document",
    "resource_id": "uuid",
    "task_type": "DOCUMENT_PARSE",
    "status": "QUEUED",
    "status_url": "/api/v1/jobs/uuid",
    "events_url": "/api/v1/jobs/uuid/events"
  },
  "meta": {
    "request_id": "uuid",
    "idempotency_replayed": false
  }
}
```

---

# 7. 公共错误响应

## 7.1 错误结构

```json id="wtzq1y"
{
  "error": {
    "code": "ANALYSIS_PLAN_NOT_APPROVED",
    "message": "分析计划尚未获得用户批准。",
    "details": {
      "analysis_plan_id": "uuid",
      "current_status": "NEEDS_APPROVAL"
    },
    "field_errors": [],
    "request_id": "uuid",
    "retryable": false,
    "suggested_action": "请先批准分析计划。"
  }
}
```

## 7.2 字段错误

```json id="bt7y3w"
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数校验失败。",
    "details": {},
    "field_errors": [
      {
        "field": "dependent_variable_ids",
        "code": "MIN_ITEMS",
        "message": "至少选择一个因变量。"
      }
    ],
    "request_id": "uuid",
    "retryable": false
  }
}
```

## 7.3 HTTP 状态码

| 状态码 | 场景             |
| --: | -------------- |
| 200 | 查询或同步操作成功      |
| 201 | 创建资源成功         |
| 202 | 异步任务已接受        |
| 204 | 删除或无内容操作成功     |
| 400 | 请求格式或业务参数错误    |
| 401 | 未认证            |
| 403 | 无权限            |
| 404 | 资源不存在          |
| 409 | 状态冲突、幂等冲突、版本冲突 |
| 413 | 文件过大           |
| 415 | 文件类型不支持        |
| 422 | Schema 校验失败    |
| 429 | 限流             |
| 500 | 未处理内部错误        |
| 502 | 外部服务错误         |
| 503 | 依赖服务不可用        |
| 504 | 外部服务超时         |

## 7.4 公共错误码

### 认证与权限

```text id="ljl53v"
AUTH_REQUIRED
TOKEN_EXPIRED
TOKEN_INVALID
PERMISSION_DENIED
PROJECT_ACCESS_DENIED
RESOURCE_ACCESS_DENIED
```

### 资源

```text id="4ny6vu"
RESOURCE_NOT_FOUND
RESOURCE_DELETED
RESOURCE_ARCHIVED
RESOURCE_INVALIDATED
RESOURCE_VERSION_CONFLICT
MEMBER_ALREADY_ACTIVE
LAST_PROJECT_OWNER
```

### 请求

```text id="4du90h"
VALIDATION_ERROR
INVALID_ENUM
INVALID_STATE_TRANSITION
MISSING_IDEMPOTENCY_KEY
IDEMPOTENCY_CONFLICT
APPROVAL_EXPIRED
APPROVAL_STALE
```

### 文件

```text id="ycp2n2"
FILE_TOO_LARGE
FILE_TYPE_UNSUPPORTED
FILE_HASH_MISMATCH
FILE_UPLOAD_FAILED
FILE_NOT_AVAILABLE
FILE_QUARANTINED
```

### 文献

```text id="djz7cl"
LITERATURE_PROVIDER_UNAVAILABLE
LITERATURE_PROVIDER_RATE_LIMITED
LITERATURE_RECORD_UNVERIFIED
LITERATURE_DUPLICATE_CANDIDATE
DOCUMENT_PARSE_FAILED
DOCUMENT_LOW_CONFIDENCE
EVIDENCE_LOCATION_FAILED
```

### 数据

```text id="dphqbg"
DATASET_FORMAT_UNSUPPORTED
DATASET_VERSION_NOT_AVAILABLE
DATASET_VERSION_INVALIDATED
DATASET_COLUMN_NOT_CONFIRMED
CLEANING_PLAN_NOT_APPROVED
TRANSFORMATION_FAILED
```

### 分析

```text id="bvgneo"
ANALYSIS_METHOD_UNSUPPORTED
ANALYSIS_ASSUMPTION_FAILED
ANALYSIS_PLAN_NOT_APPROVED
ANALYSIS_RUN_FAILED
ANALYSIS_RESULT_INVALIDATED
```

### 图表

```text id="8v17ic"
FIGURE_PLAN_INVALID
FIGURE_RENDER_FAILED
FIGURE_DATA_VERSION_MISMATCH
FIGURE_RESULT_MISMATCH
```

### 论文

```text id="y31ihu"
MANUSCRIPT_FORMAT_UNSUPPORTED
MANUSCRIPT_PARSE_FAILED
MANUSCRIPT_LOW_CONFIDENCE
MANUSCRIPT_FIX_NOT_APPROVED
```

### Agent 与模型

```text id="a00gmy"
AGENT_TOOL_NOT_ALLOWED
AGENT_APPROVAL_REQUIRED
AGENT_CONTEXT_INVALID
MODEL_PROVIDER_UNAVAILABLE
MODEL_OUTPUT_SCHEMA_INVALID
MODEL_OUTPUT_SOURCE_MISSING
MODEL_OUTPUT_UNSAFE
```

### 外部能力

```text
EXTERNAL_CAPABILITY_UNAVAILABLE
EXTERNAL_OUTPUT_INVALID
```

这两个错误码是阶段 9 的 intentional additive change，统一覆盖非模型、非特定
文献 Provider 的第三方执行边界。不得增加 `PAPERQA_*`、`ASREVIEW_*`、
`CITEPROC_*` 或其他项目专属错误码。

### Job

```text id="xms9bh"
JOB_NOT_FOUND
JOB_ALREADY_COMPLETED
JOB_NOT_CANCELLABLE
JOB_DISPATCH_FAILED
JOB_TIMEOUT
JOB_RETRY_EXHAUSTED
```

## 7.5 M0 / M1 错误兼容

M1 新增 API 使用本章正式错误 Envelope。已通过 M0 验收的 Auth/Health 端点可在
M1 期间继续返回现有兼容 Envelope：顶层 `error` 包含 `code`、`message`，顶层
`request_id` 保留请求追踪。M1 Contract Amendment 不要求为统一 casing 或字段位置
重构 M0 端点。

前端 adapter 必须同时归一化 M0 兼容 Envelope 与 M1 正式 Envelope，并优先保留：

* HTTP status；
* `error.code`；
* `error.message`；
* 位于任一兼容位置的 `request_id`；
* M1 Envelope 中存在的 `field_errors`、`details`、`retryable`。

不得通过 adapter 将 `403` 改写为 `404`；资源不披露语义由后端资源 Service 决定。

### 开源集成错误与降级映射

| 场景 | 契约表达 |
| --- | --- |
| 文献或模型 Provider 不可用 | 既有 `LITERATURE_PROVIDER_UNAVAILABLE` 或 `MODEL_PROVIDER_UNAVAILABLE` |
| 其他外部能力、隔离服务或许可证限制导致不可用 | `EXTERNAL_CAPABILITY_UNAVAILABLE` + DegradationRecord |
| 解析回退或低可信 | 既有 `DOCUMENT_LOW_CONFIDENCE` + DegradationRecord；完全失败才使用 `DOCUMENT_PARSE_FAILED` |
| 当前检索证据不足 | 成功响应中的空候选、`limitations`、`requires_human_review`；不是错误 |
| Evidence 原文定位失败 | 既有 `EVIDENCE_LOCATION_FAILED` |
| 筛选引擎不可用但可人工继续 | DegradationRecord `UNAVAILABLE`；不改变 LiteratureDecision |
| 引用渲染器不可用 | `EXTERNAL_CAPABILITY_UNAVAILABLE`；允许回退简单确定性格式器 |
| 第三方输出不能转换为严格 DTO | `EXTERNAL_OUTPUT_INVALID`，不得部分写入 |

许可证限制是能力可用性与治理事实，不泄露法律分析或内部许可证路径到普通
错误消息；`details` 只返回可公开的 capability、fallback 和 review_required。

---

# 8. 分页、排序与过滤

## 8.1 分页参数

```text id="v6avsl"
page
page_size
```

默认：

```text id="s40v4f"
page=1
page_size=20
```

最大 `page_size`：

```text id="2gf0b4"
100
```

## 8.2 排序

```text id="7fzxcx"
sort=created_at
order=desc
```

允许排序字段由每个资源明确列出。

未知字段返回 `400 VALIDATION_ERROR`。

## 8.3 过滤

示例：

```text id="nz681z"
/literature?decision=INCLUDED&verification_status=VERIFIED
```

复杂过滤不使用任意表达式，避免注入和不可控查询。

## 8.4 搜索

通用文本搜索参数：

```text id="ar2i6s"
q=<query>
```

---

# 9. 权限模型

## 9.1 基础角色

* `OWNER`；
* `EDITOR`；
* `REVIEWER`；
* `VIEWER`。

## 9.2 权限动作

```text id="90pz9e"
project.read
project.update
project.delete
project.manage_members
artifact.read
artifact.upload
artifact.download
job.read
job.cancel
job.retry
approval.read
approval.decide
approval.cancel
audit.read
literature.read
literature.create
literature.decide
dataset.read
dataset.upload
dataset.approve_transform
analysis.create
analysis.approve
analysis.run
figure.create
figure.confirm
manuscript.upload
manuscript.review
evidence.read
claim.confirm
export.create
```

## 9.3 权限响应

资源详情可包含：

```json id="yfrx1c"
{
  "permissions": {
    "can_update": true,
    "can_delete": false,
    "can_approve": true,
    "can_run": false
  },
  "allowed_actions": [
    "edit",
    "approve"
  ]
}
```

## 9.4 后端强制校验

前端隐藏按钮不构成权限控制。

所有写操作必须后端校验。

## 9.5 M1 角色动作矩阵

| 动作 | OWNER | EDITOR | REVIEWER | VIEWER |
| --- | --- | --- | --- | --- |
| `project.read` | 允许 | 允许 | 允许 | 允许 |
| `project.update` | 允许 | 允许 | 拒绝 | 拒绝 |
| `project.delete` / archive / restore | 允许 | 拒绝 | 拒绝 | 拒绝 |
| `project.manage_members` | 允许 | 拒绝 | 拒绝 | 拒绝 |
| `artifact.read` / `artifact.download` | 允许 | 允许 | 允许 | 允许 |
| `artifact.upload` | 允许 | 允许 | 拒绝 | 拒绝 |
| `job.read` | 允许 | 允许 | 允许 | 允许 |
| `job.cancel` / `job.retry` | 允许 | 允许 | 拒绝 | 拒绝 |
| `approval.read` | 允许 | 允许 | 允许 | 允许 |
| `approval.decide` | 允许 | 拒绝 | 允许 | 拒绝 |
| `approval.cancel` | 允许；或由原 requester 执行 | 仅原 requester | 仅原 requester | 仅原 requester |
| `audit.read` | 允许 | 允许 | 允许 | 允许 |

`superuser` 不是 ProjectMember role。它只能通过后端 policy 的管理性 override 访问，
不得创建伪造 membership；每次 override 必须写入 AuditLog。普通已认证非成员读取
project-scoped 资源时返回 `404 RESOURCE_NOT_FOUND` 以避免枚举；已是成员但缺少具体
动作时返回 `403 PERMISSION_DENIED`。

每个项目始终恰好一个 active OWNER。`project.manage_members` 不允许通过普通 update/remove
删除该 OWNER；ownership transfer 使用 ProjectMember PATCH 的显式原子语义，并记录
`PROJECT_OWNERSHIP_TRANSFERRED`。

---

# 10. 幂等规则

## 10.1 幂等对象

以下接口必须接受 `Idempotency-Key`：

* `POST /projects`；
* ProjectMember add、update role、remove；
* Artifact upload initiate 与 complete；
* 所有产生 Job 的 domain command；
* Approval approve、reject、cancel；
* Job retry 与 cancel；

* `POST /documents/{id}/parse`；
* `POST /documents/{id}/extractions`；
* `POST /dataset-versions/{id}/quality-runs`；
* `POST /cleaning-plans/{id}/execute`；
* `POST /analysis-plans/{id}/runs`；
* `POST /figure-plans/{id}/render`；
* `POST /manuscript-versions/{id}/check-runs`；
* `POST /projects/{id}/exports/repro-package`；
* Agent 的所有有副作用工具。

## 10.2 幂等结果

幂等键作用域固定为：

```text
(authenticated_user_id, project_id-or-null, HTTP method, canonical path template, Idempotency-Key)
```

授权必须先于 replay lookup。相同 Key、相同作用域和相同规范化请求哈希：

* 返回首次结果；
* `meta.idempotency_replayed=true`。

相同 Key、请求内容不同：

```text id="38svsj"
409 IDEMPOTENCY_CONFLICT
```

同一个字符串 Key 可在不同项目使用，因为 `project_id` 属于作用域；不得跨项目返回
原响应。若用户在首次请求后失去权限，重放必须拒绝，不得因存在幂等记录泄露资源。

## 10.3 M1 操作矩阵

| 操作 | 规则 | 并发/重放语义 |
| --- | --- | --- |
| Project create | REQUIRED | 相同 payload 返回原 `201` 响应；不同 payload 为 `409 IDEMPOTENCY_CONFLICT` |
| Member add / update role / remove | REQUIRED | 相同 mutation 返回原业务结果；不同 payload 冲突 |
| Artifact upload initiate | REQUIRED | replay 返回同一 `upload_id`，不得分配第二个对象键 |
| Artifact content transfer | NOT APPLICABLE | upload session 的一次性 `PUT`；第二次传输拒绝，不使用幂等记录覆盖对象 |
| Artifact complete | REQUIRED | replay 返回同一 Artifact 终态；不同 hash/size 声明冲突 |
| Job-producing domain command | REQUIRED | replay 返回同一 Job reference，不创建第二个 Job |
| Approval approve / reject / cancel | REQUIRED | replay 返回同一 decision；不同 decision/payload 冲突 |
| Job retry | REQUIRED | replay 不重复增加 `retry_count`，也不重复调度 |
| Job cancel | REQUIRED | replay 返回同一取消结果，不重复产生 side effect |
| Project `PATCH` | NOT APPLICABLE | 使用 `If-Match` 和 `lock_version` 控制并发 |

## 10.4 事务、失败与保留期

M1 幂等记录至少保留 24 小时。业务结果与幂等记录必须在同一 PostgreSQL 事务中提交。

* side effect / commit 前失败：不得留下成功记录，客户端可使用同一 Key 重试；
* commit 后、外部 dispatch 前后失败：重放返回已持久化的业务事实；Job 可为
  `DISPATCH_FAILED`，不得另建 Job；
* 对象存储等不可与 PostgreSQL 原子提交的副作用必须使用显式中间状态和可恢复补偿，
  不得把未确认对象返回为 `AVAILABLE`；
* replay response 保留首次 HTTP status、`data` 和稳定错误结果，并设置
  `meta.idempotency_replayed=true`。

分析和数据转换的幂等记录可长期保存。

---

# 11. 乐观锁与并发

## 11.1 可编辑对象

适用：

* ResearchProject；
* ResearchQuestion 草稿；
* Dataset 身份证；
* DatasetColumn 用户定义；
* CleaningPlan 草稿；
* AnalysisPlan 草稿；
* FigurePlan；
* Claim 草稿。

## 11.2 更新请求

```http id="w6f65e"
If-Match: "3"
```

## 11.3 冲突响应

```json id="syl2si"
{
  "error": {
    "code": "RESOURCE_VERSION_CONFLICT",
    "message": "资源已被其他操作更新。",
    "details": {
      "expected_lock_version": 3,
      "current_lock_version": 4
    },
    "request_id": "uuid",
    "retryable": false,
    "suggested_action": "请刷新后重新提交。"
  }
}
```

---

# 11.4 M0 As-Built health API

当前已实现且唯一的 M0 业务外 API 是：

```text
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/health/dependencies
```

`live` 只验证进程；`ready` 仅在 PostgreSQL/pgvector 等核心依赖均 `HEALTHY` 时返回成功；`dependencies` 报告依赖状态。`MODEL_API_KEY`、`OPENALEX_API_KEY` 未配置时状态为 `UNCONFIGURED`，健康请求绝不发起模型生成或 OpenAlex 检索。所有端点均保留服务生成或校验后的 `X-Request-ID`。M0 不存在正式 Job API，`reca.health_ping` 只用于 Worker smoke。

# 12. 异步 Job 协议

## 12.0 创建责任与事实来源

Generic public Job creation API：**NO**。客户端不得直接调用 `POST /jobs`。
需要异步执行的 domain command 由其 owning Service 在同一业务边界内创建 Job，
并按 6.4 返回 Job reference。M1 foundation 本身不为演示而制造无领域语义的 Job。

PostgreSQL 中的 Job / ProcessingRun 是业务事实来源；Celery 只负责投递与执行，Valkey
只负责 broker、cache 和短期事件。Celery result/backend 状态不得覆盖 PostgreSQL 状态。

ProcessingRun 由 Worker 在实际领取并开始一次执行尝试时创建。入队失败或尚未被 Worker
领取的 dispatch 不创建 ProcessingRun。每次真实 retry 仍使用同一个 Job，并创建新的
ProcessingRun；`attempt_number` 单调递增。

## 12.1 Job 基本结构

```json id="8hpxep"
{
  "id": "uuid",
  "project_id": "uuid",
  "task_type": "DOCUMENT_PARSE",
  "resource_type": "document",
  "resource_id": "uuid",
  "status": "RUNNING",
  "progress_percent": 45,
  "current_step": "EXTRACTING_REFERENCES",
  "total_steps": 5,
  "completed_steps": 2,
  "retry_count": 0,
  "max_retries": 3,
  "retryable": true,
  "current_processing_run_id": "uuid",
  "created_at": "2026-07-29T08:30:00Z",
  "started_at": "2026-07-29T08:30:02Z",
  "completed_at": null,
  "error": null,
  "result": null
}
```

## 12.2 Job 状态

```text id="574f7y"
DRAFT
QUEUED
RUNNING
NEEDS_REVIEW
COMPLETED
FAILED
CANCEL_REQUESTED
CANCELLED
DISPATCH_FAILED
```

## 12.3 获取 Job

```http id="witog3"
GET /api/v1/jobs/{job_id}
```

权限：`job.read`。普通非成员按 9.5 返回 `404 RESOURCE_NOT_FOUND`；成员缺少读取动作返回
`403 PERMISSION_DENIED`。不存在或不可披露的 Job 不区分错误形状。

## 12.3.1 项目 Job 列表

```http
GET /api/v1/projects/{project_id}/jobs
```

这是只读 projection，支持公共分页以及 `status`、`task_type`、`resource_type`、
`resource_id` 过滤。权限为 `job.read`，跨项目遵循 9.5 的不披露规则。响应中的每个
Job 可包含 `current_processing_run_id`、`retry_count` 和结果引用，但不得暴露 Celery
task payload、broker metadata 或内部 traceback。

## 12.4 取消 Job

```http id="0h37qr"
POST /api/v1/jobs/{job_id}/cancel
Idempotency-Key: <required>
```

请求：

```json id="2jcm7b"
{
  "reason": "用户取消了本次批量解析。"
}
```

权限：`job.cancel`。只有 `QUEUED` 或 `RUNNING` 可请求取消；其他状态返回
`409 JOB_NOT_CANCELLABLE`，缺失幂等键返回 `400 MISSING_IDEMPOTENCY_KEY`。

## 12.5 重试 Job

```http id="izgza4"
POST /api/v1/jobs/{job_id}/retry
Idempotency-Key: <required>
```

仅当：

* 状态为 FAILED 或 DISPATCH_FAILED；
* `retryable=true`；
* 未超过最大次数；
* 输入资源仍有效。

权限：`job.retry`。不可重试状态返回 `409 INVALID_STATE_TRANSITION`；超过次数返回
`409 JOB_RETRY_EXHAUSTED`；缺失幂等键返回 `400 MISSING_IDEMPOTENCY_KEY`。

### Intentional M1 Contract Amendment: retry identity

`docs-m1-approved` 已规定 retry 会创建新的 ProcessingRun，但未显式冻结 retry 后 Job ID
是否保持不变。本 amendment 明确：Job 表示一次逻辑异步工作，ProcessingRun 表示一次
实际执行 attempt；因此 retry 使用同一个 Job、递增 `retry_count`，并在 Worker 真正开始
时创建新的 ProcessingRun。这不是把批准基线中的“新 Job”语义改掉，批准基线没有该规则；
它是对原有空白的有意澄清。当前尚无正式 M1 Job/ProcessingRun 表或业务数据，因此没有
migration 或 persisted-data compatibility 问题。

重试不创建新 Job。Service 对 Job 行加锁、增加一次 `retry_count`、恢复为可调度状态并
投递同一 Job ID；Worker 真正开始时创建下一条 ProcessingRun。幂等重放不得再次增加
计数。重复 Celery delivery 必须读取并锁定 PostgreSQL 事实；已运行、终止或已被另一
ProcessingRun claim 的 delivery 不得重复执行或覆盖结果。

取消由 API Service 将业务状态推进到 `CANCEL_REQUESTED`；Worker 在安全点确认后写入
`CANCELLED`。终止 Celery task 不能单独证明 Job 已取消。所有 retry、cancel、失败、
重复 delivery 抑制与最终结果关联均写 AuditLog，并关联 Job/ProcessingRun/request_id。

## 12.6 Job 结果

完成后：

```json id="5i64r8"
{
  "result": {
    "object_type": "literature_extraction",
    "object_id": "uuid",
    "url": "/api/v1/literature-extractions/uuid"
  }
}
```

---

# 13. SSE 任务进度协议

## 13.1 连接地址

```http id="4axl3y"
GET /api/v1/jobs/{job_id}/events
Accept: text/event-stream
```

## 13.2 事件格式

```text id="iywunv"
event: job.progress
id: 19
data: {"schema_version":"1.0","job_id":"uuid","status":"RUNNING","progress_percent":45,"current_step":"EXTRACTING_FIELDS","message":"正在提取文献字段","occurred_at":"2026-07-29T08:31:00Z"}
```

## 13.3 事件类型

```text id="tcplby"
job.created
job.queued
job.started
job.progress
job.needs_review
job.completed
job.failed
job.cancel_requested
job.cancelled
job.resync_required
job.heartbeat
```

## 13.4 公共事件 Schema

```json id="3ebc4c"
{
  "schema_version": "1.0",
  "event_id": 19,
  "event_type": "job.progress",
  "job_id": "uuid",
  "project_id": "uuid",
  "status": "RUNNING",
  "progress_percent": 45,
  "current_step": "EXTRACTING_FIELDS",
  "message": "正在提取文献字段",
  "payload": {},
  "occurred_at": "2026-07-29T08:31:00Z"
}
```

## 13.5 断线恢复

客户端使用：

```http id="i27pxz"
Last-Event-ID: 19
```

服务端应尽可能从短期事件缓存继续推送。

若无法恢复，前端重新调用 Job 详情。

当 `Last-Event-ID` 已超出短期缓存时，服务端发送一次 `job.resync_required`，payload
至少包含 `reason=EVENT_HISTORY_EXPIRED` 与 `status_url`，随后客户端通过
`GET /api/v1/jobs/{job_id}` 恢复权威状态。SSE 是通知通道，不是状态事实来源。

## 13.6 心跳

建议每 15—30 秒发送：

```text id="hnbr2h"
event: job.heartbeat
```

## 13.7 鉴权

SSE 必须校验用户对 Job 所属项目的读取权限。

首次连接与每次重连都重新执行授权；缓存事件不得绕过当前权限。SSE 不可用、断线或
无法续传时，正式 polling fallback 为 `GET /api/v1/jobs/{job_id}`。

---

# 73. API 版本兼容

## 73.1 向后兼容变更

允许：

* 新增可选字段；
* 新增新端点；
* 新增枚举时客户端已有未知值回退机制；
* 增加响应 Meta。

## 73.2 破坏性变更

包括：

* 删除字段；
* 修改字段含义；
* 修改类型；
* 修改必填性；
* 修改枚举语义；
* 改变状态机；
* 改变错误码含义。

破坏性变更必须：

* 新 API 版本；
* 或提供迁移期。

## 73.3 AI Schema 兼容

AI 输出 `schema_version` 采用：

```text id="jujjj1"
MAJOR.MINOR
```

* 增加可选字段：提高 MINOR；
* 删除或修改字段：提高 MAJOR。

## 73.4 工具版本

工具名稳定，行为变化使用 `tool_version`。

Agent 配置必须固定允许的工具版本。

---

# 74. OpenAPI 与代码生成

## 74.1 OpenAPI 是可执行契约

FastAPI 生成的 OpenAPI 必须与本文档一致。

## 74.2 前端类型生成

前端 API 类型应自动生成。

禁止在前端重复定义冲突 DTO。

## 74.3 CI 检查

CI 应检查：

* OpenAPI 是否变化；
* 变化是否提交生成客户端；
* 是否存在破坏性变更；
* 示例请求是否通过 Schema。

---

# 75. 审计要求

## 75.1 必须审计的 API

* 项目创建、更新、删除；
* 研究问题确认；
* 文献决策；
* 文献字段修正；
* 数据处理批准和执行；
* AnalysisPlan 批准；
* AnalysisRun；
* 图表确认；
* 论文建议采纳或驳回；
* Claim 关系修改；
* 审批决定；
* 导出；
* Agent ToolCall。

AuditLog 只能由 Service/Worker 的业务 side effect 创建；不存在 public
`POST /audit-logs`、`PATCH /audit-logs/{id}` 或删除入口。项目活动 UI 只能使用资源
子契约定义的 project-scoped read projection。

## 75.2 审计字段

* actor；
* action；
* object；
* before；
* after；
* reason；
* request_id；
* job_id；
* approval_id；
* timestamp。

---

# 76. 契约测试要求

## 76.1 API Contract Test

每个 API 至少测试：

* 成功；
* 未认证；
* 无权限；
* 资源不存在；
* 状态不允许；
* Schema 失败；
* 幂等重放；
* 版本冲突。

## 76.2 AI Schema Test

每个 AI Schema 至少包含：

* 合法输出；
* 缺字段；
* 错误枚举；
* 来源缺失；
* 置信度越界；
* 新增统计数字；
* 文献越界；
* 因果夸大。

## 76.3 Tool Contract Test

每个工具至少包含：

* 权限允许；
* 权限拒绝；
* 前置状态满足；
* 前置状态不满足；
* 审批存在；
* 审批缺失；
* 幂等；
* 超时；
* 外部服务失败；
* 审计记录。

---

# 77. P0 API 完成定义

一个 API 只有同时满足以下条件才可标记完成：

1. 路径符合本文档；
2. 请求和响应 Schema 完成；
3. OpenAPI 正确；
4. 权限完成；
5. 状态机完成；
6. 错误码完成；
7. 审计完成；
8. 幂等完成；
9. 测试完成；
10. 前端 Client 已更新；
11. 文档示例可运行；
12. 未返回未定义字段；
13. 未以 Mock 冒充正式能力。

---

<a id="schema-query-plan-dto"></a>
<a id="schema-literature-search-result-dto"></a>
<a id="schema-literature-record-dto"></a>
<a id="schema-literature-verification-dto"></a>
<a id="schema-parsed-scholarly-document-dto"></a>
<a id="schema-evidence-candidate-dto"></a>
<a id="schema-dataset-profile-dto"></a>
<a id="schema-analysis-plan-dto"></a>
<a id="schema-analysis-result-dto"></a>
<a id="schema-figure-plan-dto"></a>
<a id="schema-figure-render-result-dto"></a>
<a id="schema-manuscript-project-context-dto"></a>
<a id="schema-manuscript-check-result-dto"></a>

# 79. 附录B：内部 Adapter 契约

```python id="vut73w"
class LiteratureProvider(Protocol):
    async def search(
        self,
        query_plan: QueryPlanDTO,
    ) -> LiteratureSearchResultDTO:
        ...

    async def verify(
        self,
        literature_record: LiteratureRecordDTO,
    ) -> LiteratureVerificationDTO:
        ...


class ScholarlyDocumentParser(Protocol):
    async def parse(
        self,
        artifact: ArtifactReference,
    ) -> ParsedScholarlyDocumentDTO:
        ...


class EvidenceRetriever(Protocol):
    async def retrieve(
        self,
        project_id: UUID,
        query: str,
        document_ids: list[UUID],
        top_k: int,
    ) -> list[EvidenceCandidateDTO]:
        ...


class DatasetProfiler(Protocol):
    async def profile(
        self,
        dataset_version_id: UUID,
        rule_set: str,
    ) -> DatasetProfileDTO:
        ...


class StatisticalEngine(Protocol):
    async def run(
        self,
        analysis_plan: AnalysisPlanDTO,
    ) -> AnalysisResultDTO:
        ...


class FigureRenderer(Protocol):
    async def render(
        self,
        figure_plan: FigurePlanDTO,
    ) -> FigureRenderResultDTO:
        ...


class ManuscriptChecker(Protocol):
    async def check(
        self,
        manuscript_version_id: UUID,
        context: ManuscriptProjectContextDTO,
    ) -> ManuscriptCheckResultDTO:
        ...


class ModelGateway(Protocol):
    async def structured_generate(
        self,
        task_type: str,
        prompt_version: str,
        input_data: dict,
        output_schema: type[BaseModel],
    ) -> BaseModel:
        ...
```

# 兼容性路径索引：Job

以下索引保留原附录 A Job 基线，并加入本次 M1 additive amendment 的 project-scoped Job
list。它不是第二份完整端点定义；请求、响应、错误和前置条件以本文件对应资源章节为准。
既有 `{id}` 参数命名保持兼容；新增路径使用本次冻结的具体参数名。

```text
GET    /api/v1/projects/{project_id}/jobs
GET    /api/v1/jobs/{id}
GET    /api/v1/jobs/{id}/events
POST   /api/v1/jobs/{id}/cancel
POST   /api/v1/jobs/{id}/retry
```
