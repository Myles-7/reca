# 研证链 AI（RECA）API、AI 与智能体工具契约

> 面向高校科研训练的全流程可信科研智能体
> Research Evidence Chain Agent

---

## 文档信息

| 项目     | 内容                                                                                               |
| ------ | ------------------------------------------------------------------------------------------------ |
| 文档名称   | `API_AI_TOOL_CONTRACTS.md`                                                                       |
| 文档版本   | 1.0.0                                                                                            |
| 适用项目版本 | RECA 0.1 Competition Edition                                                                     |
| 文档状态   | Draft                                                                                            |
| 文档类型   | REST API、AI 输出与智能体工具统一契约                                                                         |
| 主要读者   | 前端开发、后端开发、AI 开发、测试人员、Codex                                                                       |
| 负责人    | RECA Team                                                                                        |
| 最后更新时间 | 2026-07-29                                                                                       |
| 上位文档   | `README.md`、`AGENTS.md`、`PRODUCT_REQUIREMENTS.md`、`ARCHITECTURE.md`、`DATA_MODEL_AND_WORKFLOW.md` |
| 关联文档   | `TEST_AND_ACCEPTANCE.md`、`SECURITY_AND_OPEN_SOURCE.md`                                           |

---

## 变更记录

| 版本    | 日期         | 状态    | 变更说明                                        | 负责人       |
| ----- | ---------- | ----- | ------------------------------------------- | --------- |
| 1.0.0 | 2026-07-29 | Draft | 合并 REST API、AI 结构化输出、异步 Job、SSE 与智能体白名单工具契约 | RECA Team |

---

# 1. 文档目的

本文档定义 RECA 0.1 中前端、后端、异步任务、模型服务和科研总控智能体之间的统一契约。

本文档回答：

1. API 路径如何命名；
2. 请求与响应采用什么结构；
3. 错误如何返回；
4. 权限如何表达；
5. 长任务如何提交和查询；
6. SSE 如何推送任务进度；
7. AI 输出必须满足哪些 Schema；
8. AI 输出失败时如何处理；
9. 智能体能够调用哪些工具；
10. 每个工具有哪些前置状态、审批要求和副作用；
11. 幂等、并发和版本兼容如何实现；
12. 前端、后端和 Agent 如何避免各自猜测数据格式。

本文档中的契约是 RECA 0.1 前后端并行开发和 Codex 分任务实现的直接依据。

---

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
```

### 请求

```text id="4du90h"
VALIDATION_ERROR
INVALID_ENUM
INVALID_STATE_TRANSITION
MISSING_IDEMPOTENCY_KEY
IDEMPOTENCY_CONFLICT
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

### Job

```text id="xms9bh"
JOB_NOT_FOUND
JOB_ALREADY_COMPLETED
JOB_NOT_CANCELLABLE
JOB_DISPATCH_FAILED
JOB_TIMEOUT
JOB_RETRY_EXHAUSTED
```

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

---

# 10. 幂等规则

## 10.1 幂等对象

以下接口必须接受 `Idempotency-Key`：

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

相同 Key、相同用户、相同接口和相同请求哈希：

* 返回首次结果；
* `meta.idempotency_replayed=true`。

相同 Key、请求内容不同：

```text id="38svsj"
409 IDEMPOTENCY_CONFLICT
```

## 10.3 幂等保留期

P0 建议至少保留 24 小时。

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

# 12. 异步 Job 协议

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

## 12.4 取消 Job

```http id="0h37qr"
POST /api/v1/jobs/{job_id}/cancel
```

请求：

```json id="2jcm7b"
{
  "reason": "用户取消了本次批量解析。"
}
```

## 12.5 重试 Job

```http id="izgza4"
POST /api/v1/jobs/{job_id}/retry
```

仅当：

* 状态为 FAILED 或 DISPATCH_FAILED；
* `retryable=true`；
* 未超过最大次数；
* 输入资源仍有效。

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

## 13.6 心跳

建议每 15—30 秒发送：

```text id="hnbr2h"
event: job.heartbeat
```

## 13.7 鉴权

SSE 必须校验用户对 Job 所属项目的读取权限。

---

# 14. Projects API

## 14.1 创建项目

```http id="bl26io"
POST /api/v1/projects
```

权限：

```text id="fdt8q1"
authenticated user
```

请求：

```json id="ykt0w8"
{
  "name": "生成式AI与师范生学习投入研究",
  "description": "比赛演示项目",
  "discipline": "教育学",
  "research_direction": "教育技术",
  "project_type": "RESEARCH",
  "current_stage": "INTENT",
  "expected_completion_date": "2026-10-31",
  "resource_constraints": {
    "available_weeks": 8,
    "available_sample": "校内师范生"
  },
  "ethical_constraints": {
    "contains_human_participants": true
  }
}
```

响应：

```http id="gqujpb"
201 Created
```

```json id="bryws8"
{
  "data": {
    "id": "uuid",
    "name": "生成式AI与师范生学习投入研究",
    "status": "ACTIVE",
    "current_stage": "INTENT",
    "owner_id": "uuid",
    "lock_version": 1,
    "created_at": "2026-07-29T08:30:00Z",
    "permissions": {
      "can_update": true,
      "can_delete": true
    }
  },
  "meta": {
    "request_id": "uuid",
    "schema_version": "1.0"
  }
}
```

错误：

* `VALIDATION_ERROR`；
* `PERMISSION_DENIED`。

审计：

* 必须记录 `PROJECT_CREATED`。

---

## 14.2 项目列表

```http id="91q1kv"
GET /api/v1/projects
```

过滤：

```text id="ledlh9"
status
current_stage
project_type
q
page
page_size
sort
order
```

---

## 14.3 项目详情

```http id="sucwqk"
GET /api/v1/projects/{project_id}
```

---

## 14.4 更新项目

```http id="bj46sn"
PATCH /api/v1/projects/{project_id}
If-Match: "3"
```

请求只包含修改字段。

审计：

* 保存前后摘要。

---

## 14.5 项目总览

```http id="mtxtzb"
GET /api/v1/projects/{project_id}/overview
```

响应：

```json id="d40t1u"
{
  "data": {
    "project_id": "uuid",
    "current_stage": "LITERATURE",
    "current_research_question": {
      "version_id": "uuid",
      "text": "生成式AI使用频率与师范生学习投入之间是否存在关联？",
      "status": "CONFIRMED"
    },
    "counts": {
      "literature_total": 12,
      "literature_included": 8,
      "literature_uncertain": 3,
      "datasets": 1,
      "dataset_versions": 2,
      "analysis_runs": 1,
      "figures": 2,
      "manuscript_issues": 7,
      "high_risk_issues": 2
    },
    "pending_actions": [],
    "evidence_completeness": {
      "score": 0.72,
      "label": "PARTIAL",
      "missing_items": []
    },
    "recent_activity": []
  }
}
```

`score` 仅用于流程完整度提示，不代表科研质量。

---

## 14.6 归档项目

```http id="nsnj3x"
POST /api/v1/projects/{project_id}/archive
```

## 14.7 恢复项目

```http id="jn0cch"
POST /api/v1/projects/{project_id}/restore
```

## 14.8 删除项目

```http id="xkqiwk"
DELETE /api/v1/projects/{project_id}
```

请求可包含删除原因。

---

# 15. Research Questions API

## 15.1 创建研究问题

```http id="fj72d7"
POST /api/v1/projects/{project_id}/research-questions
```

请求：

```json id="bz8dgj"
{
  "raw_input": "我想研究生成式AI对师范生学习的影响。"
}
```

响应：

```http id="ll29n4"
201 Created
```

---

## 15.2 AI 解析研究问题

```http id="crgkqe"
POST /api/v1/research-question-versions/{version_id}/parse
Idempotency-Key: <key>
```

请求：

```json id="34k0fe"
{
  "max_follow_up_questions": 3,
  "language": "zh-CN"
}
```

响应：

```http id="f70ypa"
202 Accepted
```

任务结果为 `ResearchQuestionSpec`。

---

## 15.3 获取研究问题版本

```http id="mdngve"
GET /api/v1/research-question-versions/{version_id}
```

---

## 15.4 更新草稿版本

```http id="q1capb"
PATCH /api/v1/research-question-versions/{version_id}
If-Match: "2"
```

仅允许草稿或待输入状态。

---

## 15.5 创建新版本

```http id="efra3r"
POST /api/v1/research-questions/{research_question_id}/versions
```

请求：

```json id="6tvkde"
{
  "based_on_version_id": "uuid",
  "change_reason": "将研究目标从因果影响调整为相关关系。",
  "fields": {
    "relationship_type": "ASSOCIATION"
  }
}
```

---

## 15.6 请求确认

```http id="6i0oy7"
POST /api/v1/research-question-versions/{version_id}/approval-requests
```

---

## 15.7 确认研究问题

```http id="fn5ydg"
POST /api/v1/approvals/{approval_id}/approve
```

---

# 16. Literature Search API

## 16.1 创建 QueryPlan

```http id="5dg72l"
POST /api/v1/projects/{project_id}/query-plans
```

请求：

```json id="pt6t0z"
{
  "research_question_version_id": "uuid",
  "filters": {
    "from_year": 2020,
    "to_year": 2026,
    "languages": ["zh", "en"],
    "work_types": ["article"],
    "open_access_only": false
  }
}
```

可同步创建空计划，也可提交 AI 生成任务。

---

## 16.2 AI 生成 QueryPlan

```http id="jjtm71"
POST /api/v1/query-plans/{query_plan_id}/generate
Idempotency-Key: <key>
```

返回 Job。

---

## 16.3 更新 QueryPlan

```http id="ei2s4v"
PATCH /api/v1/query-plans/{query_plan_id}
If-Match: "1"
```

---

## 16.4 执行文献检索

```http id="ttn1ip"
POST /api/v1/query-plans/{query_plan_id}/search-runs
Idempotency-Key: <key>
```

请求：

```json id="6p2knc"
{
  "provider": "OPENALEX",
  "page_size": 25,
  "use_cache": true
}
```

响应：

* 一般为 `202 Accepted`；
* 返回 Job 和 SearchRun ID。

---

## 16.5 获取检索结果

```http id="z1epqi"
GET /api/v1/literature-search-runs/{run_id}/results
```

过滤：

```text id="cv20a5"
verification_status
open_access_status
from_year
to_year
q
```

---

## 16.6 将结果加入项目

```http id="i1xtvh"
POST /api/v1/projects/{project_id}/literature/import
```

请求：

```json id="i65o2u"
{
  "search_run_id": "uuid",
  "result_ids": [
    "provider-result-id-1",
    "provider-result-id-2"
  ]
}
```

---

## 16.7 DOI 导入

```http id="jijxxp"
POST /api/v1/projects/{project_id}/literature/import-doi
```

请求：

```json id="cx1w4n"
{
  "doi": "10.xxxx/example"
}
```

---

## 16.8 文献列表

```http id="v09n9u"
GET /api/v1/projects/{project_id}/literature
```

过滤：

* `decision`；
* `verification_status`；
* `has_document`；
* `year_from`；
* `year_to`；
* `q`。

---

## 16.9 文献详情

```http id="xp222r"
GET /api/v1/literature/{literature_id}
```

---

## 16.10 文献验证

```http id="3vihwp"
POST /api/v1/literature/{literature_id}/verify
Idempotency-Key: <key>
```

返回同步结果或 Job。

---

## 16.11 文献决策

```http id="7v2cn2"
POST /api/v1/literature/{literature_id}/decisions
```

请求：

```json id="iq6ctf"
{
  "decision": "INCLUDED",
  "reason_code": "RELEVANT_OBJECT_AND_METHOD",
  "reason_text": "研究对象和变量与当前问题匹配。"
}
```

响应创建新的 LiteratureDecision，不覆盖旧记录。

---

## 16.12 文献决策历史

```http id="6jfrpp"
GET /api/v1/literature/{literature_id}/decisions
```

---

# 17. Documents API

## 17.1 上传 PDF

```http id="r4ceeu"
POST /api/v1/projects/{project_id}/documents
Content-Type: multipart/form-data
```

字段：

```text id="2r47zf"
file
document_type=SCHOLARLY_PDF
literature_record_id=<optional uuid>
```

响应：

```http id="p7um7x"
201 Created
```

返回 Artifact 和 Document。

---

## 17.2 启动解析

```http id="b45kx6"
POST /api/v1/documents/{document_id}/parse
Idempotency-Key: <key>
```

请求：

```json id="t533fw"
{
  "preferred_parser": "GROBID",
  "allow_fallback": true,
  "extract_coordinates": true
}
```

返回 Job。

---

## 17.3 文档详情

```http id="xmp0tj"
GET /api/v1/documents/{document_id}
```

---

## 17.4 文档页面

```http id="6xxvni"
GET /api/v1/documents/{document_id}/pages
```

## 17.5 单页信息

```http id="zj3rge"
GET /api/v1/documents/{document_id}/pages/{page_number}
```

---

## 17.6 创建文献抽取

```http id="ggdr78"
POST /api/v1/documents/{document_id}/literature-extractions
Idempotency-Key: <key>
```

请求：

```json id="3neht8"
{
  "literature_record_id": "uuid",
  "field_codes": [
    "RESEARCH_OBJECT",
    "SAMPLE_SIZE",
    "CORE_VARIABLES",
    "RESEARCH_DESIGN",
    "ANALYSIS_METHOD",
    "MAIN_CONCLUSION",
    "LIMITATION"
  ]
}
```

返回 Job。

---

## 17.7 获取抽取结果

```http id="pr6ygp"
GET /api/v1/literature-extractions/{extraction_id}
```

---

## 17.8 修正文献字段

```http id="xnz8wa"
PATCH /api/v1/literature-extraction-fields/{field_id}
If-Match: "2"
```

请求：

```json id="bov81z"
{
  "value_text": "本科师范生",
  "evidence_span_id": "uuid",
  "correction_reason": "原抽取遗漏了本科层次限定。",
  "confirmation_status": "CONFIRMED"
}
```

审计：

* 必须记录原值和新值。

---

## 17.9 创建 EvidenceSpan

仅允许用户从实际文档内容中选取：

```http id="8ys00t"
POST /api/v1/documents/{document_id}/evidence-spans
```

请求：

```json id="v1ehwb"
{
  "page_number": 8,
  "source_text": "本研究选取某高校本科师范生……",
  "bounding_boxes": [],
  "evidence_type": "SAMPLE_DESCRIPTION"
}
```

服务端必须验证 `source_text` 与文档页文本基本一致。

---

## 17.10 文献矩阵

```http id="2499ca"
GET /api/v1/projects/{project_id}/literature-matrix
```

参数：

```text id="774xvq"
included_only
field_codes
page
page_size
sort
order
```

---

# 18. Evidence Retrieval 与文献分析 API

## 18.1 检索 EvidenceSpan

```http id="wif6k7"
POST /api/v1/projects/{project_id}/evidence-search
```

请求：

```json id="36u6nc"
{
  "query": "这些研究主要采用了哪些研究设计？",
  "document_ids": ["uuid"],
  "top_k": 10,
  "retrieval_mode": "HYBRID",
  "include_uncertain_literature": false
}
```

响应：

```json id="p4fz6y"
{
  "data": {
    "query": "这些研究主要采用了哪些研究设计？",
    "candidates": [
      {
        "evidence_span_id": "uuid",
        "literature_record_id": "uuid",
        "document_id": "uuid",
        "page_number": 6,
        "source_text": "……",
        "keyword_score": 0.74,
        "vector_score": 0.81,
        "fused_rank": 1,
        "rerank_score": 0.88
      }
    ],
    "limitations": []
  }
}
```

---

## 18.2 创建证据集合总结

```http id="049ob5"
POST /api/v1/projects/{project_id}/evidence-set-summaries
Idempotency-Key: <key>
```

请求：

```json id="9weygf"
{
  "included_literature_ids": ["uuid"],
  "summary_types": [
    "CONSENSUS",
    "CONTROVERSY",
    "EVIDENCE_GAP"
  ],
  "require_evidence_spans": true
}
```

返回 Job。

---

## 18.3 获取证据集合总结

```http id="r4q1oz"
GET /api/v1/evidence-set-summaries/{summary_id}
```

---

## 18.4 生成候选研究问题

```http id="6ehwzs"
POST /api/v1/projects/{project_id}/topic-generation-runs
Idempotency-Key: <key>
```

请求：

```json id="3f2vly"
{
  "research_question_version_id": "uuid",
  "evidence_set_summary_id": "uuid",
  "candidate_count": 3,
  "user_constraints": {
    "available_weeks": 8,
    "data_access": "校内问卷或公开数据",
    "method_skill": "基础统计",
    "ethical_constraints": []
  }
}
```

返回 Job。

---

# 19. Datasets API

## 19.1 上传数据集

```http id="2y20jl"
POST /api/v1/projects/{project_id}/datasets
Content-Type: multipart/form-data
```

字段：

```text id="938r0m"
file
name
source_type
publisher
source_platform
source_identifier
license_name
license_status
```

响应创建 Dataset 和 Original DatasetVersion。

---

## 19.2 数据集列表

```http id="32sxce"
GET /api/v1/projects/{project_id}/datasets
```

---

## 19.3 数据集详情

```http id="k1ao5i"
GET /api/v1/datasets/{dataset_id}
```

---

## 19.4 更新数据身份证

```http id="6pj07f"
PATCH /api/v1/datasets/{dataset_id}
If-Match: "2"
```

---

## 19.5 数据版本详情

```http id="dtthth"
GET /api/v1/dataset-versions/{version_id}
```

---

## 19.6 数据预览

```http id="itw2i4"
GET /api/v1/dataset-versions/{version_id}/preview
```

参数：

```text id="3b5wpk"
offset
limit
columns
```

最大预览行数建议 200。

---

## 19.7 字段列表

```http id="mt4zi0"
GET /api/v1/dataset-versions/{version_id}/columns
```

---

## 19.8 更新字段定义

```http id="rxokg8"
PATCH /api/v1/dataset-columns/{column_id}
If-Match: "1"
```

请求：

```json id="j3w4cy"
{
  "display_name": "生成式AI使用频率",
  "confirmed_type": "NUMERIC",
  "semantic_role": "INDEPENDENT_VARIABLE",
  "unit": "次/周",
  "description": "过去一周使用生成式AI的次数",
  "confirmation_status": "CONFIRMED"
}
```

---

## 19.9 数据版本比较

```http id="99icgb"
GET /api/v1/datasets/{dataset_id}/version-comparison
```

参数：

```text id="dm6ty9"
from_version_id
to_version_id
```

---

# 20. 数据质量与清洗 API

## 20.1 启动质量检查

```http id="7aatg7"
POST /api/v1/dataset-versions/{version_id}/quality-runs
Idempotency-Key: <key>
```

请求：

```json id="urudc4"
{
  "rule_set": "RECA_P0_DEFAULT",
  "include_sensitive_field_detection": true
}
```

返回 Job。

---

## 20.2 获取质量检查

```http id="4vimhl"
GET /api/v1/data-quality-runs/{run_id}
```

## 20.3 获取问题列表

```http id="yp98qt"
GET /api/v1/data-quality-runs/{run_id}/issues
```

过滤：

```text id="zgkcar"
severity
issue_type
status
column_id
```

---

## 20.4 标记问题

```http id="nv16w2"
POST /api/v1/data-quality-issues/{issue_id}/acknowledge
```

或：

```http id="yr3tsw"
POST /api/v1/data-quality-issues/{issue_id}/ignore
```

忽略需要原因。

---

## 20.5 创建 CleaningPlan

```http id="exk74c"
POST /api/v1/dataset-versions/{version_id}/cleaning-plans
```

请求：

```json id="q565v9"
{
  "title": "统一缺失编码和性别分类",
  "rationale": "将999标记为缺失，并统一性别编码。",
  "actions": [
    {
      "action_type": "MARK_MISSING",
      "target_columns": ["uuid"],
      "row_selector": {
        "operator": "VALUE_EQUALS",
        "value": 999
      },
      "parameters": {
        "replacement": null
      },
      "reason": "999为数据说明中的缺失编码。",
      "source_issue_ids": ["uuid"]
    },
    {
      "action_type": "MAP_CATEGORY",
      "target_columns": ["uuid"],
      "parameters": {
        "mapping": {
          "M": "男",
          "male": "男",
          "F": "女",
          "female": "女"
        }
      },
      "reason": "统一类别编码。"
    }
  ]
}
```

---

## 20.6 AI 建议 CleaningPlan

```http id="ae76ax"
POST /api/v1/dataset-versions/{version_id}/cleaning-plan-suggestions
Idempotency-Key: <key>
```

AI 只生成建议，不执行。

---

## 20.7 获取处理预览

```http id="yl066q"
POST /api/v1/cleaning-plans/{plan_id}/preview
Idempotency-Key: <key>
```

响应：

```json id="6rdupu"
{
  "data": {
    "cleaning_plan_id": "uuid",
    "source_dataset_version_id": "uuid",
    "affected_row_count": 36,
    "affected_column_count": 2,
    "row_count_before": 1020,
    "row_count_after": 1020,
    "sample_changes": [],
    "warnings": [],
    "ready_for_approval": true
  }
}
```

---

## 20.8 请求审批

```http id="o7840q"
POST /api/v1/cleaning-plans/{plan_id}/approval-requests
```

---

## 20.9 执行批准计划

```http id="0n01gz"
POST /api/v1/cleaning-plans/{plan_id}/execute
Idempotency-Key: <key>
```

前置：

* Plan 状态为 APPROVED；
* Approval 未失效；
* Source DatasetVersion 可用；
* Plan 内容哈希与审批快照一致。

返回 Job。

---

# 21. Analysis API

## 21.1 创建 AnalysisPlan

```http id="spb7kf"
POST /api/v1/projects/{project_id}/analysis-plans
```

请求：

```json id="dv3ts4"
{
  "research_question_version_id": "uuid",
  "dataset_version_id": "uuid",
  "analysis_goal": "CORRELATION",
  "method": "PEARSON_CORRELATION",
  "dependent_variable_ids": ["uuid"],
  "independent_variable_ids": ["uuid"],
  "control_variable_ids": [],
  "missing_data_policy": {
    "mode": "PAIRWISE_COMPLETE"
  },
  "sample_filter": null,
  "parameters": {
    "confidence_level": 0.95
  }
}
```

---

## 21.2 AI 建议 AnalysisPlan

```http id="se5k2j"
POST /api/v1/projects/{project_id}/analysis-plan-suggestions
Idempotency-Key: <key>
```

请求必须包括：

* 研究问题版本；
* 数据版本；
* 已确认字段角色；
* 用户分析目标。

---

## 21.3 验证前提

```http id="m2bxzx"
POST /api/v1/analysis-plans/{plan_id}/validate
Idempotency-Key: <key>
```

可同步或异步。

响应：

```json id="1zgw5g"
{
  "data": {
    "analysis_plan_id": "uuid",
    "status": "READY",
    "checks": [
      {
        "check_code": "DATA_TYPE",
        "status": "PASSED",
        "explanation": "两个变量均已确认为数值型。"
      },
      {
        "check_code": "LINEARITY",
        "status": "WARNING",
        "explanation": "散点关系存在轻微非线性迹象。"
      }
    ],
    "warnings": [
      "相关分析不支持因果解释。"
    ]
  }
}
```

---

## 21.4 更新 AnalysisPlan

```http id="jz6fnz"
PATCH /api/v1/analysis-plans/{plan_id}
If-Match: "2"
```

仅 DRAFT、NEEDS_INPUT、READY 状态可修改。

---

## 21.5 请求审批

```http id="6bt7rd"
POST /api/v1/analysis-plans/{plan_id}/approval-requests
```

---

## 21.6 执行分析

```http id="w29jby"
POST /api/v1/analysis-plans/{plan_id}/runs
Idempotency-Key: <key>
```

请求：

```json id="qpyon2"
{
  "run_reason": "执行已确认的主演示相关分析。"
}
```

前置：

* Plan 已批准；
* 数据版本可用；
* 变量确认；
* 方法 P0 支持；
* 审批快照一致。

返回 Job 和 AnalysisRun ID。

---

## 21.7 AnalysisRun 详情

```http id="ilwfqv"
GET /api/v1/analysis-runs/{run_id}
```

---

## 21.8 AnalysisResult

```http id="mixw79"
GET /api/v1/analysis-runs/{run_id}/results
```

示例：

```json id="eyawpo"
{
  "data": {
    "analysis_run_id": "uuid",
    "dataset_version_id": "uuid",
    "method": "PEARSON_CORRELATION",
    "variables": [
      {
        "column_id": "uuid",
        "role": "X",
        "display_name": "生成式AI使用频率"
      },
      {
        "column_id": "uuid",
        "role": "Y",
        "display_name": "学习投入"
      }
    ],
    "sample_size": 984,
    "statistics": {
      "coefficient": 0.31,
      "p_value": 0.00001
    },
    "confidence_intervals": {
      "coefficient": {
        "lower": 0.25,
        "upper": 0.37,
        "level": 0.95
      }
    },
    "assumption_results": [],
    "warnings": [
      "该结果仅表示相关关系，不支持因果推断。"
    ],
    "environment": {
      "python": "3.11.x",
      "scipy": "locked-version",
      "pandas": "locked-version"
    },
    "code_artifact_id": "uuid",
    "created_at": "2026-07-29T09:00:00Z"
  }
}
```

---

## 21.9 AI 解释分析结果

```http id="ha1e0o"
POST /api/v1/analysis-runs/{run_id}/interpretations
Idempotency-Key: <key>
```

AI 输入只读取结构化结果。

输出不得出现输入中不存在的新数字。

---

## 21.10 失效 AnalysisRun

```http id="hd0awz"
POST /api/v1/analysis-runs/{run_id}/invalidate
```

请求：

```json id="mtlfqp"
{
  "reason": "上游数据版本被确认包含错误编码。"
}
```

---

# 22. Figures API

## 22.1 创建 FigurePlan

```http id="yro86f"
POST /api/v1/projects/{project_id}/figure-plans
```

请求：

```json id="f8u1b4"
{
  "dataset_version_id": "uuid",
  "analysis_run_id": "uuid",
  "chart_type": "SCATTER",
  "x_column_id": "uuid",
  "y_column_id": "uuid",
  "group_column_id": null,
  "parameters": {
    "show_regression_line": true,
    "show_confidence_interval": true,
    "width_inches": 8,
    "height_inches": 6,
    "dpi": 300
  },
  "caption_draft": "生成式AI使用频率与学习投入的散点关系。"
}
```

---

## 22.2 AI 图表推荐

```http id="44yd4s"
POST /api/v1/projects/{project_id}/figure-recommendations
Idempotency-Key: <key>
```

---

## 22.3 渲染图表

```http id="hlta75"
POST /api/v1/figure-plans/{plan_id}/render
Idempotency-Key: <key>
```

返回 Job。

---

## 22.4 图表详情

```http id="ksaqi1"
GET /api/v1/figures/{figure_id}
```

---

## 22.5 图表规范问题

```http id="den2dp"
GET /api/v1/figures/{figure_id}/validation-issues
```

---

## 22.6 确认图表

```http id="3vc7uw"
POST /api/v1/figures/{figure_id}/approval-requests
```

确认通过 Approval API 完成。

---

## 22.7 下载图表

```http id="mtf5ds"
GET /api/v1/figures/{figure_id}/artifacts/{format}
```

`format`：

* `png`；
* `svg`；
* `pdf`；
* `code`。

---

# 23. Manuscripts API

## 23.1 上传 DOCX

```http id="639mso"
POST /api/v1/projects/{project_id}/manuscripts
Content-Type: multipart/form-data
```

字段：

```text id="u3pzsc"
file
title
```

响应创建 Manuscript 和 ManuscriptVersion。

---

## 23.2 论文详情

```http id="ijpl44"
GET /api/v1/manuscripts/{manuscript_id}
```

---

## 23.3 论文版本

```http id="s4akv0"
GET /api/v1/manuscript-versions/{version_id}
```

---

## 23.4 启动检查

```http id="7ln2d5"
POST /api/v1/manuscript-versions/{version_id}/check-runs
Idempotency-Key: <key>
```

请求：

```json id="wq7fs6"
{
  "checks": [
    "CITATION",
    "NUMERIC_CONSISTENCY",
    "CAUSALITY",
    "TERMINOLOGY",
    "BASIC_FORMAT"
  ],
  "use_project_literature": true,
  "use_project_analysis_results": true,
  "use_project_figures": true
}
```

返回 Job。

---

## 23.5 获取检查结果

```http id="0v6ygq"
GET /api/v1/manuscript-check-runs/{run_id}
```

## 23.6 获取问题列表

```http id="7g6o7y"
GET /api/v1/manuscript-check-runs/{run_id}/issues
```

过滤：

* `severity`；
* `issue_type`；
* `status`；
* `auto_fixable`。

---

## 23.7 问题详情

```http id="3xkt99"
GET /api/v1/manuscript-issues/{issue_id}
```

---

## 23.8 接受建议

```http id="4fgo4z"
POST /api/v1/manuscript-issues/{issue_id}/accept
```

高风险问题仅表示用户接受建议，不自动修改。

---

## 23.9 驳回建议

```http id="r0rnqh"
POST /api/v1/manuscript-issues/{issue_id}/reject
```

请求需要原因。

---

## 23.10 创建低风险修复计划

```http id="c7depl"
POST /api/v1/manuscript-versions/{version_id}/fix-plans
```

只允许自动修复项。

---

## 23.11 执行批准修复

```http id="5ecjly"
POST /api/v1/manuscript-fix-plans/{plan_id}/execute
Idempotency-Key: <key>
```

输出新 ManuscriptVersion。

---

# 24. Claims 与 Evidence API

## 24.1 创建 Claim

```http id="l2bcb1"
POST /api/v1/projects/{project_id}/claims
```

请求：

```json id="9fr7ch"
{
  "claim_type": "MANUSCRIPT_STATEMENT",
  "source_object_type": "manuscript_version",
  "source_object_id": "uuid",
  "source_location": {
    "paragraph_index": 42
  },
  "claim_text": "生成式AI使用频率与师范生学习投入呈正相关。",
  "scope_statement": "基于当前公开数据集和相关分析。"
}
```

---

## 24.2 Claim 详情

```http id="w32063"
GET /api/v1/claims/{claim_id}
```

---

## 24.3 创建证据关系

```http id="si6m14"
POST /api/v1/claims/{claim_id}/evidence-links
```

请求：

```json id="35fgzq"
{
  "evidence_object_type": "ANALYSIS_RESULT",
  "evidence_object_id": "uuid",
  "relation_type": "SUPPORTED_BY",
  "strength": "STRONG",
  "explanation": "相关分析结果支持该表述。"
}
```

服务端校验同项目。

---

## 24.4 Claim 审核

```http id="e2fpvo"
POST /api/v1/claims/{claim_id}/audits
Idempotency-Key: <key>
```

返回 Job 或同步 AuditResult。

---

## 24.5 证据图

```http id="mjmwc0"
GET /api/v1/projects/{project_id}/evidence-graph
```

参数：

```text id="qyuukj"
root_claim_id
depth
node_types
risk_only
include_invalidated
```

响应：

```json id="axsywd"
{
  "data": {
    "nodes": [
      {
        "id": "claim:uuid",
        "node_type": "CLAIM",
        "object_id": "uuid",
        "label": "生成式AI使用频率与学习投入呈正相关",
        "status": "SUPPORTED",
        "risk_level": "LOW",
        "detail_url": "/api/v1/claims/uuid"
      }
    ],
    "edges": [
      {
        "id": "uuid",
        "source": "claim:uuid",
        "target": "analysis_result:uuid",
        "relation_type": "SUPPORTED_BY",
        "status": "ACTIVE"
      }
    ],
    "scope": {
      "literature_count": 8,
      "dataset_version_id": "uuid",
      "analysis_run_ids": ["uuid"],
      "generated_at": "2026-07-29T10:00:00Z"
    }
  }
}
```

---

## 24.6 Claim 确认

通过 Approval API，不允许直接设置 `CONFIRMED`。

---

# 25. Approvals API

## 25.1 审批列表

```http id="r39whm"
GET /api/v1/projects/{project_id}/approvals
```

过滤：

* `status`；
* `approval_type`；
* `target_object_type`；
* `requested_by_actor_type`。

---

## 25.2 审批详情

```http id="0rd817"
GET /api/v1/approvals/{approval_id}
```

---

## 25.3 批准

```http id="1zbzba"
POST /api/v1/approvals/{approval_id}/approve
```

请求：

```json id="cxff74"
{
  "decision_reason": "已核对处理预览，确认执行。",
  "item_decisions": []
}
```

---

## 25.4 拒绝

```http id="hnmlp8"
POST /api/v1/approvals/{approval_id}/reject
```

拒绝原因必填。

---

## 25.5 取消审批请求

```http id="wu9v8h"
POST /api/v1/approvals/{approval_id}/cancel
```

仅发起者或有管理权限用户可执行。

---

# 26. Exports API

## 26.1 创建复现包

```http id="7rczfr"
POST /api/v1/projects/{project_id}/exports/repro-package
Idempotency-Key: <key>
```

请求：

```json id="duun5u"
{
  "include_original_literature_files": true,
  "include_dataset_versions": true,
  "include_sensitive_data": false,
  "include_agent_logs": true,
  "include_model_output_artifacts": false,
  "acknowledge_license_warnings": false
}
```

系统先执行导出就绪审核。

可能返回：

* `202 Accepted`；
* 或 `409`，要求用户处理许可证或敏感信息问题。

---

## 26.2 导出就绪检查

```http id="i7iluh"
POST /api/v1/projects/{project_id}/exports/readiness-check
```

响应：

```json id="bf35wf"
{
  "data": {
    "ready": false,
    "blocking_issues": [
      {
        "code": "DATASET_LICENSE_UNKNOWN",
        "object_id": "uuid",
        "message": "数据集许可证未知。"
      }
    ],
    "warnings": [],
    "requires_confirmation": true
  }
}
```

---

## 26.3 导出详情

```http id="o4krbs"
GET /api/v1/exports/{export_id}
```

## 26.4 下载导出包

```http id="7scudj"
GET /api/v1/repro-packages/{package_id}/download
```

---

# 27. Agent API

## 27.1 启动 AgentRun

```http id="3g8jdg"
POST /api/v1/projects/{project_id}/agent-runs
```

请求：

```json id="ld9k3a"
{
  "goal": "检查当前项目缺少哪些步骤，并建议下一步。",
  "mode": "PLAN_AND_EXPLAIN",
  "allow_tool_calls": true
}
```

响应：

```http id="6dsmhi"
202 Accepted
```

---

## 27.2 AgentRun 详情

```http id="iq3di7"
GET /api/v1/agent-runs/{agent_run_id}
```

---

## 27.3 ToolCall 列表

```http id="pgx5dk"
GET /api/v1/agent-runs/{agent_run_id}/tool-calls
```

---

## 27.4 继续 AgentRun

当 Agent 等待用户输入：

```http id="mcjocz"
POST /api/v1/agent-runs/{agent_run_id}/messages
```

请求：

```json id="fpk00k"
{
  "message": "研究目标是分析相关关系，不进行因果推断。"
}
```

---

## 27.5 取消 AgentRun

```http id="9gn1lm"
POST /api/v1/agent-runs/{agent_run_id}/cancel
```

---

# 28. AI 输出公共 Envelope

所有重要 AI 输出统一采用：

```json id="3uc6tg"
{
  "schema_version": "1.0",
  "task_type": "RESEARCH_QUESTION_PARSE",
  "result": {},
  "source_ids": [],
  "confidence": 0.0,
  "confidence_label": "LOW",
  "limitations": [],
  "warnings": [],
  "requires_human_review": true,
  "review_reasons": [],
  "generated_at": "2026-07-29T08:30:00Z",
  "model_metadata": {
    "model_invocation_id": "uuid",
    "provider": "configured-provider",
    "model": "configured-model",
    "prompt_version": "rq-parse-1.0"
  }
}
```

## 28.1 必填字段

* `schema_version`；
* `task_type`；
* `result`；
* `source_ids`；
* `confidence`；
* `limitations`；
* `requires_human_review`；
* `generated_at`；
* `model_metadata.model_invocation_id`。

## 28.2 confidence

范围：

```text id="o07vs5"
0.0 <= confidence <= 1.0
```

仅用于系统复核排序，不视为统计概率。

## 28.3 confidence_label

映射：

|        数值 | 标签     |
| --------: | ------ |
| 0.00—0.49 | LOW    |
| 0.50—0.79 | MEDIUM |
| 0.80—1.00 | HIGH   |

可根据测试调整，但必须统一。

## 28.4 source_ids

只能包含实际输入对象 ID，例如：

* ResearchQuestionVersion；
* LiteratureRecord；
* DocumentChunk；
* EvidenceSpan；
* DatasetVersion；
* AnalysisResult；
* Figure；
* ManuscriptVersion。

不得使用自然语言文献名称代替 ID。

## 28.5 requires_human_review

以下情况必须为 `true`：

* 研究问题正式确认；
* 文献字段低置信度；
* 文献纳入或排除建议；
* 当前证据不足判断；
* 选题采用；
* 数据处理建议；
* 统计方法选择；
* 因果表达修改；
* 高风险论文问题；
* Claim 正式确认。

---

# 29. AI 输出校验流程

```text id="pzhlp2"
模型原始输出
→ JSON解析
→ Schema校验
→ 枚举校验
→ 来源ID校验
→ 业务规则校验
→ 安全规则校验
→ 保存候选结果
→ 必要时人工复核
```

## 29.1 JSON 解析失败

允许一次结构化修复重试。

仍失败：

```text id="61lyki"
MODEL_OUTPUT_SCHEMA_INVALID
```

## 29.2 来源缺失

当任务要求来源但 `source_ids` 为空：

```text id="xetulx"
MODEL_OUTPUT_SOURCE_MISSING
```

不得将结果保存为正式结论。

## 29.3 数字检查

AI 输出中出现统计数字时：

* 必须与输入 AnalysisResult 完全匹配；
* 不得新增；
* 不得改变精度含义；
* 不得将 `p=0.051` 表述为显著。

## 29.4 文献检查

AI 不得输出输入文献集合之外的论文元数据。

## 29.5 Prompt 版本

每个任务必须固定 `prompt_version`。

Prompt 更新必须：

* 更新版本；
* 运行黄金测试；
* 记录变更；
* 不静默覆盖。

---

# 30. ResearchQuestionSpec

## 30.1 task_type

```text id="a4wmxd"
RESEARCH_QUESTION_PARSE
```

## 30.2 result Schema

```json id="k7q6dc"
{
  "normalized_question": "生成式AI使用频率与师范生学习投入之间是否存在关联？",
  "research_object": "师范生",
  "population": {
    "education_level": "本科",
    "major_scope": "师范类专业",
    "other_constraints": []
  },
  "context": "高校学习场景",
  "independent_variables": [
    {
      "name": "生成式AI使用频率",
      "definition": null,
      "measurement_hint": null
    }
  ],
  "dependent_variables": [
    {
      "name": "学习投入",
      "definition": null,
      "measurement_hint": null
    }
  ],
  "control_variables": [],
  "research_goal": "RELATE",
  "relationship_type": "ASSOCIATION",
  "method_preference": [],
  "time_scope": null,
  "region_scope": null,
  "language_scope": ["zh", "en"],
  "resource_constraints": [],
  "ethical_constraints": [],
  "uncertainties": [
    {
      "field": "population.education_level",
      "reason": "用户未明确本科或研究生。"
    }
  ],
  "follow_up_questions": [
    "研究对象限定本科师范生吗？"
  ]
}
```

## 30.3 规则

* 不生成文献；
* 不自动声称因果；
* 用户使用“影响”时应判断是否需要改为相关、比较或预测；
* 最多输出 3 个高价值追问；
* 不填充用户未提供且无法推断的事实。

---

# 31. QueryPlan AI Schema

## 31.1 task_type

```text id="abnjss"
QUERY_PLAN_GENERATION
```

## 31.2 result Schema

```json id="enbkfn"
{
  "chinese_terms": {
    "core": ["生成式人工智能", "学习投入", "师范生"],
    "synonyms": [],
    "object_terms": ["师范生", "教师教育学生"],
    "method_terms": ["问卷", "相关研究"]
  },
  "english_terms": {
    "core": [
      "generative artificial intelligence",
      "learning engagement",
      "pre-service teachers"
    ],
    "synonyms": [
      "student engagement",
      "teacher education students"
    ],
    "method_terms": [
      "survey",
      "correlational study"
    ]
  },
  "boolean_query": "(\"generative artificial intelligence\" OR \"generative AI\") AND (\"learning engagement\" OR \"student engagement\") AND (\"pre-service teacher*\" OR \"teacher education student*\")",
  "filters": {
    "from_year": 2020,
    "to_year": 2026,
    "languages": ["zh", "en"],
    "work_types": ["article"]
  },
  "expansion_options": [],
  "narrowing_options": [],
  "limitations": [
    "检索词用于查询规划，不代表已检索到真实文献。"
  ]
}
```

## 31.3 规则

* 查询词和真实检索结果必须区分；
* 不输出论文题目；
* 不伪造数据库特定语法能力；
* Provider Adapter 负责最终查询转换。

---

# 32. LiteratureExtraction AI Schema

## 32.1 task_type

```text id="0z7wuu"
LITERATURE_FIELD_EXTRACTION
```

## 32.2 result Schema

```json id="q1meva"
{
  "literature_record_id": "uuid",
  "document_id": "uuid",
  "fields": [
    {
      "field_code": "RESEARCH_OBJECT",
      "value": {
        "text": "本科师范生",
        "structured": {
          "education_level": "本科",
          "population_type": "师范生"
        }
      },
      "evidence_span_ids": ["uuid"],
      "confidence": 0.91,
      "requires_human_review": false,
      "notes": []
    },
    {
      "field_code": "SAMPLE_SIZE",
      "value": {
        "text": "312",
        "structured": {
          "n": 312
        }
      },
      "evidence_span_ids": ["uuid"],
      "confidence": 0.87,
      "requires_human_review": false,
      "notes": []
    }
  ],
  "document_level_limitations": []
}
```

## 32.3 规则

* 每个语义字段尽可能绑定 EvidenceSpan；
* 无证据时字段应为 `null` 或低置信度；
* 不从摘要之外推完整方法；
* 不把研究假设当结论；
* 样本量必须来自原文；
* 主要结论必须保留限定条件。

---

# 33. EvidenceSetSummary AI Schema

## 33.1 task_type

```text id="py0gfn"
EVIDENCE_SET_SUMMARY
```

## 33.2 result Schema

```json id="mfc1tk"
{
  "included_literature_ids": ["uuid"],
  "scope_statement": "基于当前纳入的8篇文献。",
  "consensus_items": [
    {
      "claim_text": "多数纳入研究报告生成式AI使用与学习相关结果之间存在正向关联。",
      "supporting_literature_ids": ["uuid"],
      "contradicting_literature_ids": [],
      "evidence_span_ids": ["uuid"],
      "strength": "MODERATE",
      "limitations": [
        "多数研究采用横断面设计。"
      ]
    }
  ],
  "controversy_items": [],
  "evidence_gap_items": [
    {
      "claim_text": "在当前文献集合中，纵向研究证据较少。",
      "basis": {
        "included_count": 8,
        "longitudinal_count": 1
      },
      "evidence_span_ids": ["uuid"],
      "limitations": [
        "该判断仅适用于当前纳入文献。"
      ]
    }
  ],
  "counterexamples": [],
  "missing_information": []
}
```

## 33.3 规则

禁止：

* “学术界从未研究”；
* “已经证明不存在研究”；
* 隐藏反例；
* 将单篇文献作为共识；
* 引用未纳入文献。

---

# 34. TopicCandidate AI Schema

## 34.1 task_type

```text id="a54p7n"
TOPIC_CANDIDATE_GENERATION
```

## 34.2 result Schema

```json id="wab71p"
{
  "candidates": [
    {
      "candidate_order": 1,
      "question_text": "生成式AI使用频率与本科师范生学习投入之间的关系：AI素养的调节作用",
      "research_object": "本科师范生",
      "variables": {
        "independent": ["生成式AI使用频率"],
        "dependent": ["学习投入"],
        "moderator": ["AI素养"]
      },
      "literature_basis": "基于当前纳入文献中的相关研究与测量建议。",
      "literature_record_ids": ["uuid"],
      "evidence_span_ids": ["uuid"],
      "possible_innovation": "在当前文献集合中，AI素养作为调节变量的研究较少。",
      "data_requirements": {
        "minimum_fields": [
          "生成式AI使用频率",
          "学习投入",
          "AI素养"
        ],
        "sample_notes": "需具备足够样本进行基础回归分析。"
      },
      "recommended_method": "相关分析；调节分析不进入P0自动执行范围。",
      "literature_basis_level": "MEDIUM",
      "data_availability": "MEDIUM",
      "method_difficulty": "MEDIUM",
      "time_feasibility": "HIGH",
      "ethical_risk": "LOW",
      "major_risks": [],
      "supervisor_confirmation_items": [
        "确认AI素养的理论角色。"
      ]
    }
  ]
}
```

## 34.3 规则

* 固定返回 3 个候选项；
* 不使用 93 分等伪精确分数；
* 超出 P0 方法时必须明确；
* 每项必须有文献依据和数据要求；
* 最终采用需用户和导师确认。

---

# 35. CleaningPlanSuggestion AI Schema

## 35.1 task_type

```text id="ut7n9w"
CLEANING_PLAN_SUGGESTION
```

## 35.2 result Schema

```json id="xqoa0d"
{
  "dataset_version_id": "uuid",
  "suggested_actions": [
    {
      "source_issue_ids": ["uuid"],
      "action_type": "MARK_MISSING",
      "target_column_ids": ["uuid"],
      "row_selector": {
        "operator": "VALUE_EQUALS",
        "value": 999
      },
      "parameters": {
        "replacement": null
      },
      "reason": "数据说明中将999定义为缺失编码。",
      "risk_level": "MEDIUM",
      "expected_effect": {
        "affected_rows": 18,
        "row_count_change": 0
      },
      "alternatives": [
        "保留原值并在分析时排除。"
      ],
      "requires_approval": true
    }
  ],
  "warnings": [],
  "limitations": []
}
```

## 35.3 规则

* 只能引用已检测问题；
* 不自动执行；
* 不输出任意代码；
* 异常值不能默认删除；
* 处理影响必须可预览。

---

# 36. AnalysisPlanSuggestion AI Schema

## 36.1 task_type

```text id="2f00si"
ANALYSIS_PLAN_SUGGESTION
```

## 36.2 result Schema

```json id="wzsbdm"
{
  "research_question_version_id": "uuid",
  "dataset_version_id": "uuid",
  "analysis_goal": "CORRELATION",
  "recommended_method": "PEARSON_CORRELATION",
  "variable_mapping": {
    "independent_variable_ids": ["uuid"],
    "dependent_variable_ids": ["uuid"],
    "control_variable_ids": [],
    "group_variable_id": null
  },
  "missing_data_policy": {
    "mode": "PAIRWISE_COMPLETE"
  },
  "required_assumption_checks": [
    "DATA_TYPE",
    "SAMPLE_SIZE",
    "LINEARITY",
    "OUTLIER_INFLUENCE"
  ],
  "recommendation_reason": "研究目标为两个连续变量之间的相关关系。",
  "alternative_methods": [
    {
      "method": "SPEARMAN_CORRELATION",
      "condition": "线性或分布前提不足时。"
    }
  ],
  "limitations": [
    "相关分析不能支持因果推断。"
  ],
  "requires_human_review": true
}
```

## 36.3 规则

* 只能推荐 P0 方法；
* 变量角色必须由用户确认；
* 不直接执行；
* 不生成统计数字；
* 前提不明确时必须说明。

---

# 37. AnalysisInterpretation AI Schema

## 37.1 task_type

```text id="dfx7z0"
ANALYSIS_RESULT_INTERPRETATION
```

## 37.2 result Schema

```json id="vqbypm"
{
  "analysis_run_id": "uuid",
  "result_summary": "在当前样本中，生成式AI使用频率与学习投入呈正相关。",
  "numeric_statements": [
    {
      "text": "相关系数为0.31。",
      "analysis_result_path": "statistics.coefficient",
      "value": 0.31
    }
  ],
  "statistical_significance_statement": "该相关在当前分析中达到统计显著。",
  "practical_interpretation": "关联强度较弱至中等，仍需结合研究背景解释。",
  "causal_boundary": "该分析不能说明生成式AI使用导致学习投入变化。",
  "sample_scope": "结论仅适用于当前数据版本中的有效样本。",
  "limitations": [],
  "recommended_follow_up": []
}
```

## 37.3 规则

* 所有数字必须绑定 `analysis_result_path`；
* 值必须与 AnalysisResult 完全一致；
* 不把不显著写成显著；
* 不把相关写成因果；
* 不扩大样本范围。

---

# 38. FigureRecommendation AI Schema

## 38.1 task_type

```text id="u2zsl4"
FIGURE_RECOMMENDATION
```

## 38.2 result Schema

```json id="fgzxu8"
{
  "recommendations": [
    {
      "chart_type": "SCATTER",
      "x_column_id": "uuid",
      "y_column_id": "uuid",
      "group_column_id": null,
      "reason": "用于展示两个连续变量之间的关系。",
      "required_parameters": {
        "show_regression_line": true,
        "show_confidence_interval": true
      },
      "caption_elements": [
        "变量名称",
        "样本量",
        "数据版本",
        "相关不等于因果"
      ],
      "risks": [
        "大量重叠点可能影响可读性。"
      ]
    }
  ],
  "not_recommended": [
    {
      "chart_type": "BAR",
      "reason": "柱状图不适合展示两个连续变量之间的关系。"
    }
  ]
}
```

---

# 39. ManuscriptIssueSuggestion AI Schema

## 39.1 task_type

```text id="pmf8sd"
MANUSCRIPT_ISSUE_SUGGESTION
```

## 39.2 result Schema

```json id="focjtw"
{
  "manuscript_version_id": "uuid",
  "issues": [
    {
      "issue_type": "CAUSAL_OVERCLAIM",
      "severity": "HIGH",
      "section_name": "讨论",
      "paragraph_index": 42,
      "original_text": "生成式AI使用提高了师范生学习投入。",
      "reason": "项目中仅执行了相关分析，不能支持因果表述。",
      "evidence": [
        {
          "object_type": "ANALYSIS_RESULT",
          "object_id": "uuid"
        }
      ],
      "suggestion": "可改为“生成式AI使用频率与学习投入呈正相关”。",
      "auto_fixable": false,
      "requires_human_review": true
    }
  ]
}
```

## 39.3 规则

* 高风险问题不自动修复；
* 建议不得新增不存在的引用或数字；
* 问题必须有位置；
* 数字问题必须关联 AnalysisResult；
* 文献问题必须关联 LiteratureRecord 或 EvidenceSpan。

---

# 40. AuditResult AI Schema

## 40.1 task_type

```text id="jjoz37"
TRUST_AUDIT
```

## 40.2 result Schema

```json id="7q5crn"
{
  "audit_type": "CLAIM_COMPLETENESS_AUDIT",
  "target_object_type": "CLAIM",
  "target_object_id": "uuid",
  "status": "NEEDS_REVIEW",
  "findings": [
    {
      "finding_code": "MISSING_QUALIFYING_EVIDENCE",
      "severity": "MEDIUM",
      "message": "当前Claim缺少横断面设计限制说明。",
      "evidence_object_ids": ["uuid"],
      "recommended_action": "补充限定性证据或修改Claim表述。"
    }
  ],
  "evidence_coverage": {
    "has_source": true,
    "has_page_location": true,
    "has_dataset_version": true,
    "has_analysis_result": true,
    "has_user_confirmation": false
  },
  "limitations": []
}
```

## 40.3 规则

* Audit 不直接修改目标对象；
* 审核结果必须关联证据；
* 无法验证时应返回 `INSUFFICIENT_EVIDENCE`；
* 不得使用“已验证”掩盖来源缺失。

---

# 41. 智能体工具公共契约

## 41.1 工具定义字段

每个工具必须定义：

| 字段                     | 说明            |
| ---------------------- | ------------- |
| name                   | 唯一工具名称        |
| version                | 工具版本          |
| description            | 工具用途          |
| input_schema           | 参数 Schema     |
| output_schema          | 返回 Schema     |
| required_permissions   | 所需权限          |
| allowed_project_states | 允许项目状态        |
| preconditions          | 前置条件          |
| side_effect_level      | 副作用等级         |
| requires_approval      | 是否需要批准        |
| idempotent             | 是否幂等          |
| timeout_seconds        | 超时            |
| retry_policy           | 重试策略          |
| audit_required         | 是否记录 ToolCall |
| prohibited_behaviors   | 禁止行为          |
| error_codes            | 工具错误码         |

## 41.2 副作用等级

```text id="383qeq"
NONE
READ_ONLY
CREATE_DRAFT
CREATE_VERSION
EXECUTE_APPROVED_CHANGE
EXPORT_DATA
```

## 41.3 公共工具输入

所有工具内部输入自动注入：

```json id="hwewmk"
{
  "context": {
    "project_id": "uuid",
    "user_id": "uuid",
    "agent_run_id": "uuid",
    "request_id": "uuid"
  }
}
```

模型不得自行填写或修改上下文 ID。

## 41.4 公共工具输出

```json id="m92cjh"
{
  "tool_name": "get_project_state",
  "tool_version": "1.0",
  "status": "COMPLETED",
  "result": {},
  "output_object_ids": [],
  "warnings": [],
  "limitations": [],
  "audit": {
    "tool_call_id": "uuid"
  }
}
```

## 41.5 工具错误

```json id="8y10nv"
{
  "tool_name": "run_correlation",
  "tool_version": "1.0",
  "status": "FAILED",
  "error": {
    "code": "ANALYSIS_PLAN_NOT_APPROVED",
    "message": "分析计划尚未批准。",
    "retryable": false
  },
  "audit": {
    "tool_call_id": "uuid"
  }
}
```

---

# 42. 工具白名单总表

## 42.1 只读工具

```text id="qwyf3a"
get_project_state
get_pending_approvals
get_research_question
list_project_literature
get_literature_record
get_literature_matrix
retrieve_evidence
get_dataset_profile
get_dataset_version
get_analysis_plan
get_analysis_result
get_figure
get_manuscript_issues
get_claim_evidence_graph
get_export_readiness
```

## 42.2 创建草稿或建议工具

```text id="ps76ff"
parse_research_question
generate_query_plan
suggest_literature_decision
extract_literature_fields
summarize_evidence_set
generate_topic_candidates
suggest_cleaning_plan
suggest_analysis_plan
recommend_figure
suggest_manuscript_issues
audit_claim
```

## 42.3 确定性执行工具

```text id="ce0nrc"
search_literature
verify_literature_record
parse_document
profile_dataset
preview_cleaning_plan
apply_approved_transformations
validate_analysis_assumptions
run_descriptive_statistics
run_group_comparison
run_correlation
run_simple_linear_regression
render_figure
check_manuscript
export_repro_package
```

## 42.4 禁止工具

不得注册：

```text id="43wdfx"
execute_shell
execute_python
execute_sql
run_arbitrary_code
delete_original_file
overwrite_dataset
modify_analysis_result
approve_on_behalf_of_user
download_paid_fulltext
generate_complete_thesis
bypass_permission
```

---

# 43. get_project_state

## 43.1 作用

读取当前项目阶段、核心对象、待办和阻断原因。

## 43.2 输入

```json id="86xj5r"
{}
```

Project ID 从上下文注入。

## 43.3 输出

```json id="9xu6xz"
{
  "project_id": "uuid",
  "current_stage": "ANALYSIS",
  "research_question_status": "CONFIRMED",
  "literature": {
    "total": 12,
    "included": 8,
    "needs_review": 2
  },
  "datasets": {
    "current_version_id": "uuid",
    "pending_cleaning_plan_id": null
  },
  "analysis": {
    "approved_plan_id": "uuid",
    "latest_run_id": null
  },
  "pending_approvals": [],
  "blocking_reasons": [],
  "recommended_next_actions": [
    "执行已批准的相关分析。"
  ]
}
```

## 43.4 契约

| 属性  | 值            |
| --- | ------------ |
| 副作用 | READ_ONLY    |
| 审批  | 否            |
| 幂等  | 是            |
| 超时  | 10秒          |
| 权限  | project.read |
| 审计  | 是            |

---

# 44. parse_research_question

## 44.1 输入

```json id="23k3sn"
{
  "research_question_version_id": "uuid",
  "max_follow_up_questions": 3
}
```

## 44.2 输出

`ResearchQuestionSpec Envelope`

## 44.3 契约

| 属性  | 值                |
| --- | ---------------- |
| 副作用 | CREATE_DRAFT     |
| 审批  | 正式确认需要，工具执行本身不需要 |
| 幂等  | 是                |
| 超时  | 90秒              |
| 权限  | project.update   |
| 前置  | 版本属于当前项目         |
| 禁止  | 自动确认问题           |

---

# 45. generate_query_plan

输入：

```json id="wi87xp"
{
  "research_question_version_id": "uuid",
  "filters": {
    "from_year": 2020,
    "to_year": 2026,
    "languages": ["zh", "en"]
  }
}
```

输出：

`QueryPlan Envelope`

副作用：

```text id="z4dtqa"
CREATE_DRAFT
```

不得调用外部文献检索；只生成检索计划。

---

# 46. search_literature

输入：

```json id="9vyusu"
{
  "query_plan_id": "uuid",
  "provider": "OPENALEX",
  "page_size": 25,
  "use_cache": true
}
```

输出：

```json id="cb1mvl"
{
  "search_run_id": "uuid",
  "job_id": "uuid",
  "status": "QUEUED"
}
```

契约：

| 属性  | 值                                 |
| --- | --------------------------------- |
| 副作用 | CREATE_DRAFT                      |
| 审批  | 否                                 |
| 幂等  | 是                                 |
| 超时  | 30秒提交，实际异步                        |
| 权限  | literature.create                 |
| 禁止  | 模型生成论文列表                          |
| 错误  | PROVIDER_UNAVAILABLE、RATE_LIMITED |

---

# 47. verify_literature_record

输入：

```json id="qgu3z5"
{
  "literature_record_id": "uuid"
}
```

输出：

```json id="hwu9qa"
{
  "literature_record_id": "uuid",
  "verification_status": "VERIFIED",
  "matched_fields": {},
  "conflicts": [],
  "sources": [
    {
      "provider": "OPENALEX",
      "identifier": "..."
    }
  ]
}
```

只允许使用真实 Provider 或缓存。

---

# 48. parse_document

输入：

```json id="er67xr"
{
  "document_id": "uuid",
  "preferred_parser": "GROBID",
  "allow_fallback": true
}
```

输出 Job。

副作用：

```text id="obn1mz"
CREATE_VERSION
```

实际生成 DocumentPage、Chunk 和解析记录。

禁止覆盖原始 PDF。

---

# 49. extract_literature_fields

输入：

```json id="0t8q1a"
{
  "document_id": "uuid",
  "literature_record_id": "uuid",
  "field_codes": [
    "RESEARCH_OBJECT",
    "SAMPLE_SIZE",
    "CORE_VARIABLES",
    "RESEARCH_DESIGN",
    "ANALYSIS_METHOD",
    "MAIN_CONCLUSION",
    "LIMITATION"
  ]
}
```

输出 LiteratureExtraction Envelope 或 Job。

规则：

* 只能基于该文档；
* 字段证据必须来自 DocumentChunk；
* 不自动确认；
* 低置信度需复核。

---

# 50. retrieve_evidence

输入：

```json id="qos4xl"
{
  "query": "研究采用了哪些方法？",
  "document_ids": ["uuid"],
  "top_k": 10
}
```

输出 EvidenceCandidate 列表。

副作用：

```text id="9c58zo"
READ_ONLY
```

禁止引用未召回内容。

---

# 51. summarize_evidence_set

输入：

```json id="8u9gli"
{
  "included_literature_ids": ["uuid"],
  "summary_types": [
    "CONSENSUS",
    "CONTROVERSY",
    "EVIDENCE_GAP"
  ]
}
```

输出 EvidenceSetSummary Envelope。

副作用：

```text id="x7u8te"
CREATE_DRAFT
```

所有总结必须限定当前文献集合。

---

# 52. generate_topic_candidates

输入：

```json id="t4cx5s"
{
  "research_question_version_id": "uuid",
  "evidence_set_summary_id": "uuid",
  "candidate_count": 3,
  "user_constraints": {}
}
```

输出 TopicCandidate Envelope。

规则：

* `candidate_count` P0 固定为 3；
* 不自动采用；
* 不生成无文献依据题目；
* 超出 P0 方法需标注。

---

# 53. profile_dataset

输入：

```json id="qzsfv1"
{
  "dataset_version_id": "uuid",
  "rule_set": "RECA_P0_DEFAULT"
}
```

输出 Job。

确定性执行，不调用模型计算质量指标。

---

# 54. suggest_cleaning_plan

输入：

```json id="99akj0"
{
  "dataset_version_id": "uuid",
  "data_quality_issue_ids": ["uuid"]
}
```

输出 CleaningPlanSuggestion Envelope。

副作用：

```text id="47qsff"
CREATE_DRAFT
```

不得执行转换。

---

# 55. preview_cleaning_plan

输入：

```json id="022vyl"
{
  "cleaning_plan_id": "uuid"
}
```

输出预览。

确定性执行。

不得创建正式 DatasetVersion。

---

# 56. apply_approved_transformations

输入：

```json id="snpmyk"
{
  "cleaning_plan_id": "uuid"
}
```

前置：

* Plan APPROVED；
* Approval 有效；
* Source DatasetVersion AVAILABLE；
* 审批快照哈希一致。

输出 Job 和 DataTransformation ID。

| 属性  | 值                         |
| --- | ------------------------- |
| 副作用 | EXECUTE_APPROVED_CHANGE   |
| 审批  | 必须                        |
| 幂等  | 必须                        |
| 权限  | dataset.approve_transform |
| 禁止  | 任意代码、覆盖原始版本               |

---

# 57. suggest_analysis_plan

输入：

```json id="wb9xje"
{
  "research_question_version_id": "uuid",
  "dataset_version_id": "uuid",
  "analysis_goal": "CORRELATION"
}
```

输出 AnalysisPlanSuggestion Envelope。

不得执行统计。

---

# 58. validate_analysis_assumptions

输入：

```json id="2wqnni"
{
  "analysis_plan_id": "uuid"
}
```

输出：

* AssumptionCheck；
* 警告；
* 是否可进入审批。

确定性程序负责计算指标。

模型可在之后解释，但不能替代检查结果。

---

# 59. run_descriptive_statistics

输入：

```json id="6bp3ic"
{
  "analysis_plan_id": "uuid"
}
```

前置：

* AnalysisPlan APPROVED；
* 方法为 DESCRIPTIVE_STATISTICS。

输出 Job 和 AnalysisRun。

禁止模型生成均值等数字。

---

# 60. run_group_comparison

输入：

```json id="k87hv4"
{
  "analysis_plan_id": "uuid"
}
```

支持：

* `INDEPENDENT_TWO_GROUP`；
* `PAIRED_TWO_GROUP`。

前置：

* 用户确认样本独立性或配对关系；
* Plan 已批准。

---

# 61. run_correlation

输入：

```json id="cqwwgz"
{
  "analysis_plan_id": "uuid"
}
```

支持：

* Pearson；
* Spearman。

输出 AnalysisRun。

强制警告：

```text id="oa7whf"
相关关系不等于因果关系。
```

---

# 62. run_simple_linear_regression

输入：

```json id="np2sew"
{
  "analysis_plan_id": "uuid"
}
```

P0 仅简单线性回归。

控制变量和复杂模型超出范围时返回：

```text id="11ql1f"
ANALYSIS_METHOD_UNSUPPORTED
```

---

# 63. recommend_figure

输入：

```json id="n48ss3"
{
  "dataset_version_id": "uuid",
  "analysis_run_id": "uuid",
  "expression_goal": "RELATIONSHIP"
}
```

输出 FigureRecommendation Envelope。

不得生成图像。

---

# 64. render_figure

输入：

```json id="kdkbcn"
{
  "figure_plan_id": "uuid"
}
```

输出 Job。

确定性 Matplotlib 渲染。

禁止 Agent 修改 AnalysisResult。

---

# 65. check_manuscript

输入：

```json id="o9ss6k"
{
  "manuscript_version_id": "uuid",
  "checks": [
    "CITATION",
    "NUMERIC_CONSISTENCY",
    "CAUSALITY",
    "TERMINOLOGY",
    "BASIC_FORMAT"
  ]
}
```

输出 Job。

论文数字核对必须读取项目 AnalysisResult。

---

# 66. suggest_manuscript_issues

输入：

```json id="1i8y23"
{
  "manuscript_version_id": "uuid",
  "rule_findings": [],
  "project_context_ids": {
    "literature_record_ids": ["uuid"],
    "analysis_result_ids": ["uuid"],
    "figure_ids": ["uuid"]
  }
}
```

输出 ManuscriptIssueSuggestion Envelope。

模型建议不得自动修改 DOCX。

---

# 67. audit_claim

输入：

```json id="27pfpd"
{
  "claim_id": "uuid",
  "audit_types": [
    "CLAIM_COMPLETENESS_AUDIT",
    "CAUSALITY_AUDIT",
    "NUMERIC_CONSISTENCY_AUDIT"
  ]
}
```

输出 AuditResult Envelope。

只读审核，不修改 Claim。

---

# 68. export_repro_package

输入：

```json id="7czrn8"
{
  "include_original_literature_files": true,
  "include_dataset_versions": true,
  "include_sensitive_data": false,
  "include_agent_logs": true
}
```

前置：

* 用户权限；
* 导出就绪检查；
* 必要确认；
* 许可证和敏感数据规则通过。

输出 Job。

副作用：

```text id="erf6gk"
EXPORT_DATA
```

---

# 69. 智能体工具审批矩阵

| 工具                             | 是否修改业务数据 |           是否需要审批 |
| ------------------------------ | -------: | ---------------: |
| get_project_state              |        否 |                否 |
| parse_research_question        |     创建候选 |           正式确认需要 |
| generate_query_plan            |     创建草稿 |                否 |
| search_literature              |   创建检索记录 |                否 |
| verify_literature_record       |   更新验证状态 |                否 |
| parse_document                 |   创建解析产物 |                否 |
| extract_literature_fields      |   创建候选抽取 |           字段确认需要 |
| retrieve_evidence              |        否 |                否 |
| summarize_evidence_set         |   创建候选总结 |        Claim确认需要 |
| generate_topic_candidates      |     创建候选 |             采用需要 |
| profile_dataset                |   创建质量报告 |                否 |
| suggest_cleaning_plan          |     创建草稿 |                否 |
| preview_cleaning_plan          |        否 |                否 |
| apply_approved_transformations |  创建新数据版本 |                是 |
| suggest_analysis_plan          |     创建草稿 |                否 |
| validate_analysis_assumptions  |   创建检查结果 |                否 |
| run_descriptive_statistics     |   创建正式结果 |           是，批准计划 |
| run_group_comparison           |   创建正式结果 |           是，批准计划 |
| run_correlation                |   创建正式结果 |           是，批准计划 |
| run_simple_linear_regression   |   创建正式结果 |           是，批准计划 |
| recommend_figure               |     创建建议 |                否 |
| render_figure                  |     创建图表 | FigurePlan确认策略决定 |
| check_manuscript               |     创建问题 |                否 |
| suggest_manuscript_issues      |   创建候选问题 |          高风险采纳需要 |
| audit_claim                    |     创建审核 |                否 |
| export_repro_package           |     导出数据 |          是或需导出确认 |

---

# 70. 智能体禁止行为

科研总控 Agent 必须禁止：

1. 调用未注册工具；
2. 构造任意 URL 调用外部服务；
3. 执行 Shell；
4. 执行用户 Python；
5. 执行任意 SQL；
6. 直接修改数据库；
7. 覆盖原始文件；
8. 未经批准修改数据；
9. 批准自己的建议；
10. 生成未检索文献；
11. 伪造 DOI；
12. 口算统计数字；
13. 修改 AnalysisResult；
14. 把相关描述为因果；
15. 自动生成完整论文；
16. 将 Mock 数据宣称为真实结果；
17. 隐藏工具失败；
18. 隐藏低置信度；
19. 跨项目读取数据；
20. 将敏感数据发送给未批准模型服务。

---

# 71. 工具调用状态

```text id="01ptqs"
REQUESTED
WAITING_APPROVAL
RUNNING
COMPLETED
FAILED
DENIED
CANCELLED
```

## 71.1 WAITING_APPROVAL

Agent 必须停止执行链路并向用户说明：

* 操作内容；
* 影响；
* 风险；
* 目标对象；
* 审批入口。

## 71.2 FAILED

Agent 不得假装成功。

必须展示：

* 错误；
* 是否可重试；
* 是否影响原始文件；
* 下一步。

---

# 72. 模型调用契约

## 72.1 模型调用输入

必须包含：

* task_type；
* prompt_version；
* schema_name；
* schema_version；
* source_ids；
* sanitized_input；
* output_requirements；
* prohibited_behaviors。

## 72.2 敏感数据

默认不向模型发送：

* 完整数据表；
* 身份证号；
* 手机号；
* 姓名列表；
* 未脱敏论文附件；
* 系统密钥；
* 对象存储凭据。

## 72.3 模型重试

可重试：

* 临时网络错误；
* 模型超时；
* JSON 解析失败；
* Schema 轻微失败。

不可自动重试：

* 内容安全拒绝；
* 来源缺失；
* 输入权限错误；
* 数据敏感规则阻止；
* 任务超出产品范围。

## 72.4 最大重试

建议：

```text id="m766p0"
2
```

超过后进入人工处理。

## 72.5 模型回退

允许配置备用模型，但必须记录实际模型。

不得将备用模型结果伪装成主模型结果。

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

# 78. 附录A：核心 API 路径总览

```text id="57awqh"
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
GET    /api/v1/projects/{project_id}/overview
POST   /api/v1/projects/{project_id}/archive
POST   /api/v1/projects/{project_id}/restore
DELETE /api/v1/projects/{project_id}

POST   /api/v1/projects/{project_id}/research-questions
POST   /api/v1/research-question-versions/{version_id}/parse
GET    /api/v1/research-question-versions/{version_id}
PATCH  /api/v1/research-question-versions/{version_id}
POST   /api/v1/research-questions/{id}/versions
POST   /api/v1/research-question-versions/{id}/approval-requests

POST   /api/v1/projects/{project_id}/query-plans
POST   /api/v1/query-plans/{id}/generate
PATCH  /api/v1/query-plans/{id}
POST   /api/v1/query-plans/{id}/search-runs
GET    /api/v1/literature-search-runs/{id}/results
POST   /api/v1/projects/{project_id}/literature/import
POST   /api/v1/projects/{project_id}/literature/import-doi
GET    /api/v1/projects/{project_id}/literature
GET    /api/v1/literature/{id}
POST   /api/v1/literature/{id}/verify
POST   /api/v1/literature/{id}/decisions
GET    /api/v1/literature/{id}/decisions

POST   /api/v1/projects/{project_id}/documents
POST   /api/v1/documents/{id}/parse
GET    /api/v1/documents/{id}
GET    /api/v1/documents/{id}/pages
GET    /api/v1/documents/{id}/pages/{page_number}
POST   /api/v1/documents/{id}/literature-extractions
GET    /api/v1/literature-extractions/{id}
PATCH  /api/v1/literature-extraction-fields/{id}
POST   /api/v1/documents/{id}/evidence-spans
GET    /api/v1/projects/{project_id}/literature-matrix

POST   /api/v1/projects/{project_id}/evidence-search
POST   /api/v1/projects/{project_id}/evidence-set-summaries
GET    /api/v1/evidence-set-summaries/{id}
POST   /api/v1/projects/{project_id}/topic-generation-runs

POST   /api/v1/projects/{project_id}/datasets
GET    /api/v1/projects/{project_id}/datasets
GET    /api/v1/datasets/{id}
PATCH  /api/v1/datasets/{id}
GET    /api/v1/dataset-versions/{id}
GET    /api/v1/dataset-versions/{id}/preview
GET    /api/v1/dataset-versions/{id}/columns
PATCH  /api/v1/dataset-columns/{id}
GET    /api/v1/datasets/{id}/version-comparison

POST   /api/v1/dataset-versions/{id}/quality-runs
GET    /api/v1/data-quality-runs/{id}
GET    /api/v1/data-quality-runs/{id}/issues
POST   /api/v1/data-quality-issues/{id}/acknowledge
POST   /api/v1/data-quality-issues/{id}/ignore
POST   /api/v1/dataset-versions/{id}/cleaning-plans
POST   /api/v1/dataset-versions/{id}/cleaning-plan-suggestions
POST   /api/v1/cleaning-plans/{id}/preview
POST   /api/v1/cleaning-plans/{id}/approval-requests
POST   /api/v1/cleaning-plans/{id}/execute

POST   /api/v1/projects/{project_id}/analysis-plans
POST   /api/v1/projects/{project_id}/analysis-plan-suggestions
POST   /api/v1/analysis-plans/{id}/validate
PATCH  /api/v1/analysis-plans/{id}
POST   /api/v1/analysis-plans/{id}/approval-requests
POST   /api/v1/analysis-plans/{id}/runs
GET    /api/v1/analysis-runs/{id}
GET    /api/v1/analysis-runs/{id}/results
POST   /api/v1/analysis-runs/{id}/interpretations
POST   /api/v1/analysis-runs/{id}/invalidate

POST   /api/v1/projects/{project_id}/figure-plans
POST   /api/v1/projects/{project_id}/figure-recommendations
POST   /api/v1/figure-plans/{id}/render
GET    /api/v1/figures/{id}
GET    /api/v1/figures/{id}/validation-issues
POST   /api/v1/figures/{id}/approval-requests
GET    /api/v1/figures/{id}/artifacts/{format}

POST   /api/v1/projects/{project_id}/manuscripts
GET    /api/v1/manuscripts/{id}
GET    /api/v1/manuscript-versions/{id}
POST   /api/v1/manuscript-versions/{id}/check-runs
GET    /api/v1/manuscript-check-runs/{id}
GET    /api/v1/manuscript-check-runs/{id}/issues
GET    /api/v1/manuscript-issues/{id}
POST   /api/v1/manuscript-issues/{id}/accept
POST   /api/v1/manuscript-issues/{id}/reject
POST   /api/v1/manuscript-versions/{id}/fix-plans
POST   /api/v1/manuscript-fix-plans/{id}/execute

POST   /api/v1/projects/{project_id}/claims
GET    /api/v1/claims/{id}
POST   /api/v1/claims/{id}/evidence-links
POST   /api/v1/claims/{id}/audits
GET    /api/v1/projects/{project_id}/evidence-graph

GET    /api/v1/projects/{project_id}/approvals
GET    /api/v1/approvals/{id}
POST   /api/v1/approvals/{id}/approve
POST   /api/v1/approvals/{id}/reject
POST   /api/v1/approvals/{id}/cancel

POST   /api/v1/projects/{project_id}/exports/readiness-check
POST   /api/v1/projects/{project_id}/exports/repro-package
GET    /api/v1/exports/{id}
GET    /api/v1/repro-packages/{id}/download

GET    /api/v1/jobs/{id}
GET    /api/v1/jobs/{id}/events
POST   /api/v1/jobs/{id}/cancel
POST   /api/v1/jobs/{id}/retry

POST   /api/v1/projects/{project_id}/agent-runs
GET    /api/v1/agent-runs/{id}
GET    /api/v1/agent-runs/{id}/tool-calls
POST   /api/v1/agent-runs/{id}/messages
POST   /api/v1/agent-runs/{id}/cancel
```

---

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

---

# 80. 最终契约结论

RECA 0.1 的前端、后端、模型和智能体必须遵守以下统一链路：

```text id="uqjbqh"
用户操作
→ REST API
→ 权限与状态校验
→ Application Service
→ 计划或业务对象
→ 必要时 ApprovalRecord
→ 异步 Job
→ 白名单确定性工具
→ ProcessingRun
→ 结构化结果
→ AuditResult
→ 前端展示
```

AI 相关链路必须遵守：

```text id="9112r5"
实际来源对象
→ 脱敏输入
→ 固定Prompt版本
→ 固定AI Schema
→ Schema校验
→ 来源校验
→ 业务规则校验
→ 候选结果
→ 人工确认或确定性执行
```

智能体必须遵守：

```text id="0j15cs"
读取项目状态
→ 发现缺失信息
→ 生成下一步计划
→ 调用白名单工具
→ 遇到高风险操作请求审批
→ 汇总结构化结果
→ 执行可信审核
```

绝不能采用：

```text id="i80c8d"
用户提出目标
→ Agent自由生成代码
→ Agent自行执行
→ Agent直接修改数据
→ Agent自行解释为正式结论
```

本文档定义的 API、AI Schema 和工具契约共同保证：

1. 前端不猜测后端结构；
2. 后端不接受未经校验的 AI 输出；
3. Agent 不绕过业务服务；
4. 统计数字不由模型生成；
5. 数据修改必须经过审批；
6. 文献结论必须保留真实来源；
7. 图表必须绑定数据和分析版本；
8. 论文问题必须能够定位和核验；
9. 所有高风险操作可审计；
10. 整个科研流程可追溯、可复核、可复现。
