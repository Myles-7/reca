# COMMON_API_JOB_AND_SSE_CONTRACTS

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

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

# 11.4 M0 As-Built health API

当前已实现且唯一的 M0 业务外 API 是：

```text
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/health/dependencies
```

`live` 只验证进程；`ready` 仅在 PostgreSQL/pgvector 等核心依赖均 `HEALTHY` 时返回成功；`dependencies` 报告依赖状态。`MODEL_API_KEY`、`OPENALEX_API_KEY` 未配置时状态为 `UNCONFIGURED`，健康请求绝不发起模型生成或 OpenAlex 检索。所有端点均保留服务生成或校验后的 `X-Request-ID`。M0 不存在正式 Job API，`reca.health_ping` 只用于 Worker smoke。

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

以下字符串从原附录 A 原样迁入，仅保留旧 `{id}` 参数命名和总览兼容性。它们不是第二份完整端点定义；请求、响应、错误和前置条件以本文件对应资源章节为准。不得在本阶段擅自将 `{id}` 与更具体的参数名合并或重命名。

```text
GET    /api/v1/jobs/{id}
GET    /api/v1/jobs/{id}/events
POST   /api/v1/jobs/{id}/cancel
POST   /api/v1/jobs/{id}/retry
```
