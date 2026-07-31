# PROJECT_RESEARCH_AND_LITERATURE_API

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- 当前增量状态：APPROVED
- Migration status: COMPLETE

## 权威范围

Projects、ProjectMember、Artifact、Research Questions、Scoping、QueryPlan、Literature、Documents、Extraction、EvidenceSpan、TopicCandidate、Approvals、AuditLog read projection 和 AgentRun 资源 API 的唯一完整定义。

## 不负责的内容

不定义数据分析、论文导出、AI 输出 Schema 或 Agent Tool。Job/SSE 的公共契约由 `COMMON_API_JOB_AND_SSE_CONTRACTS.md` 定义。

## 文档导航

- 返回 [API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- [COMMON_API_JOB_AND_SSE_CONTRACTS.md](COMMON_API_JOB_AND_SSE_CONTRACTS.md)
- [PROJECT_RESEARCH_AND_LITERATURE_API.md](PROJECT_RESEARCH_AND_LITERATURE_API.md)
- [DATA_ANALYSIS_AND_FIGURE_API.md](DATA_ANALYSIS_AND_FIGURE_API.md)
- [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)
- [AI_SCHEMA_CONTRACTS.md](AI_SCHEMA_CONTRACTS.md)
- [AGENT_TOOL_CONTRACTS.md](AGENT_TOOL_CONTRACTS.md)

以下正文由原入口文档对应章节机械迁入。路径、字段、错误码、Schema、Tool 名称和契约语义保持原样。


## M1 Contract Amendment 边界

本次增量正式补充 M1 必需的 ProjectMember、Artifact 和 AuditLog read projection。它是 additive amendment：不删除或重命名既有 API、Schema、Error Code、Tool、Requirement ID 或 Acceptance ID。

以下资源没有 generic public create API：

* ApprovalRecord 由需要 FORMAL_APPROVAL 的领域 Service 创建；
* Job 由产生异步工作的领域 Service 创建；
* ProcessingRun 由 Worker 在实际执行尝试开始时创建；
* AuditLog 由 Service side effect 追加写。

M1 不存在真实 FORMAL_APPROVAL consumer，不为演示制造虚假高风险命令。Approval 列表、详情和决定接口仍作为基础设施契约实现；首批真实 consumer 来自后续里程碑的正式领域命令。

# 14. Projects API

## 14.0 Project authorization 与 no-disclosure

* active ProjectMember 是 `removed_at=null` 的成员关系；
* 普通用户必须是 active member 才能读取项目；已认证非成员读取 project-scoped 资源统一返回 `404 RESOURCE_NOT_FOUND`，避免泄露私有项目存在性；
* active member 缺少某个写动作时返回 `403 PERMISSION_DENIED`；
* `is_superuser=true` 在 Competition Edition 可由后端 policy 执行管理覆盖，不要求伪造 ProjectMember；所有管理覆盖写操作必须创建 `actor_type=USER`、`outcome=SUCCEEDED/DENIED` 的 AuditLog，并在安全日志标记 administrative override；
* Router、前端路由、UUID 和对象存储键不构成授权；所有对象关系由 Service 校验同一 `project_id`；
* 具体 M1 角色动作矩阵见 `COMMON_API_JOB_AND_SSE_CONTRACTS.md` 第 9 章。

## 14.1 创建项目

```http id="bl26io"
POST /api/v1/projects
Idempotency-Key: <required>
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
    "current_stage": "INTENT",
    "module_availability": {
      "research_question": "NOT_AVAILABLE",
      "literature": "NOT_AVAILABLE",
      "dataset": "NOT_AVAILABLE",
      "analysis": "NOT_AVAILABLE",
      "figure": "NOT_AVAILABLE",
      "manuscript": "NOT_AVAILABLE",
      "evidence": "NOT_AVAILABLE"
    },
    "current_research_question": null,
    "foundation_counts": {
      "members": 1,
      "artifacts": 0,
      "jobs_active": 0,
      "approvals_pending": 0,
      "audit_events": 1
    },
    "counts": {
      "literature_total": null,
      "literature_included": null,
      "literature_uncertain": null,
      "datasets": null,
      "dataset_versions": null,
      "analysis_runs": null,
      "figures": null,
      "manuscript_issues": null,
      "high_risk_issues": null
    },
    "pending_actions": [],
    "evidence_completeness": null,
    "recent_activity": []
  }
}
```

`score` 仅用于流程完整度提示，不代表科研质量。

`module_availability` 只允许 `NOT_AVAILABLE`、`AVAILABLE`、`DEGRADED`。M1 尚未实现的 M2+ 模块必须返回 `NOT_AVAILABLE`，对应对象和 count 为 `null`。模块实现且查询成功但没有记录时才使用 `AVAILABLE` 与真实 `0`。`DEGRADED` 必须同时返回用户可见限制。`foundation_counts` 和 `recent_activity` 只统计已实现、已授权的 M1 数据。

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

# 14A. Project Members API

ProjectMember 使用 membership `id` 作为 URL 标识。项目始终恰好有一个 active OWNER，
并与 `ResearchProject.owner_id` 一致。所有 mutation 必须带 `Idempotency-Key`，不使用
`If-Match`；Service 通过事务锁和唯一 OWNER 不变量处理并发。

## 14A.1 成员列表

```http
GET /api/v1/projects/{project_id}/members
```

过滤：

```text
role
q
include_removed=false
page
page_size
```

普通 active member 可查看 active member。`include_removed=true` 仅 OWNER 或 superuser 可用。

响应项：

```json
{
  "id": "membership-uuid",
  "project_id": "project-uuid",
  "user": {
    "id": "user-uuid",
    "email": "member@example.edu",
    "full_name": "成员姓名"
  },
  "role": "EDITOR",
  "joined_at": "2026-07-31T08:30:00Z",
  "removed_at": null,
  "allowed_actions": ["project.read", "project.update"]
}
```

## 14A.2 添加或重新加入成员

```http
POST /api/v1/projects/{project_id}/members
Idempotency-Key: <required>
```

权限：active OWNER 或 superuser administrative override。

请求：

```json
{
  "user_id": "registered-user-uuid",
  "role": "EDITOR"
}
```

`role=OWNER` 不允许用于 add；ownership 只能通过 14A.3 的显式 transfer 完成。响应：
`201 Created`。如果 `(project_id, user_id)` 存在已移除关系，Service 复用该 membership、
清空 `removed_at` 并返回 `200 OK`；这不是创建第二行。active membership 已存在且请求角色
相同返回幂等结果；角色不同且不是同一 Idempotency-Key 重放时返回
`409 MEMBER_ALREADY_ACTIVE`，客户端应调用角色更新。

审计：`PROJECT_MEMBER_ADDED` 或 `PROJECT_MEMBER_REJOINED`。

## 14A.3 更新成员角色

```http
PATCH /api/v1/projects/{project_id}/members/{member_id}
Idempotency-Key: <required>
```

权限：active OWNER 或 superuser administrative override。

请求：

```json
{
  "role": "REVIEWER",
  "reason": "负责方法与结果复核。"
}
```

普通 role update 不能把当前 OWNER 改为非 OWNER，也不能把其他成员直接改为 OWNER。
ownership transfer 仍使用本 endpoint，但必须显式提交：

```json
{
  "role": "OWNER",
  "transfer_ownership": true,
  "previous_owner_role": "EDITOR",
  "reason": "将项目所有权移交给新的负责人。"
}
```

路径中的 `member_id` 是目标 successor membership。只有当前 OWNER 或带审计 reason 的
superuser administrative override 可以发起。Service 在同一事务中锁定项目、原 OWNER
和 successor，将 successor 设为 OWNER、原 OWNER 设为 `previous_owner_role`、更新
`ResearchProject.owner_id` 并写 `PROJECT_OWNERSHIP_TRANSFERRED` AuditLog；任一步失败全部
回滚。`previous_owner_role` 只能是 EDITOR、REVIEWER 或 VIEWER。

transfer 成功返回 `200 OK`，`data` 包含更新后的 successor ProjectMember、
`project_owner_id` 和原 OWNER 更新后的 member/role 摘要，使客户端能原子刷新成员与项目
owner projection。幂等重放返回同一响应，不重复写第二条 transfer audit。

普通 role update 审计 `PROJECT_MEMBER_ROLE_CHANGED`；transfer 审计保存双方 role、
owner_id before/after、reason 和 request_id。

## 14A.4 移除成员

```http
DELETE /api/v1/projects/{project_id}/members/{member_id}
Idempotency-Key: <required>
```

权限：active OWNER、成员本人或 superuser administrative override。非 OWNER 可以移除
自己。当前 OWNER 不允许直接删除或 self-remove，必须先通过 14A.3 transfer ownership。
成功设置非 OWNER 成员的 `removed_at` 并返回 `204 No Content`。

审计：`PROJECT_MEMBER_REMOVED`。

## 14A.5 成员错误

| HTTP | Code | 条件 |
| ---: | --- | --- |
| 404 | `RESOURCE_NOT_FOUND` | 项目、成员关系或注册用户不可见/不存在 |
| 403 | `PERMISSION_DENIED` | active member 缺少管理权限 |
| 409 | `MEMBER_ALREADY_ACTIVE` | 用户已是 active member 且非幂等重放 |
| 409 | `LAST_PROJECT_OWNER` | 普通 update/remove 试图降级或移除唯一 active OWNER，必须先 transfer ownership |
| 409 | `INVALID_STATE_TRANSITION` | 已移除成员更新、add OWNER、无 transfer flag 设置 OWNER、当前 OWNER 普通降级或无效 successor |
| 422 | `VALIDATION_ERROR` | role、UUID 或请求字段无效 |

---

# 14B. Artifact API

## 14B.1 项目 Artifact 列表

```http
GET /api/v1/projects/{project_id}/artifacts
```

过滤：`artifact_type`、`status`、`is_original`、`q`、`page`、`page_size`。需要 `artifact.read`。

## 14B.2 上传初始化

```http
POST /api/v1/projects/{project_id}/artifacts/uploads
Idempotency-Key: <required>
```

权限：`artifact.upload`。

请求：

```json
{
  "artifact_type": "PDF_DOCUMENT",
  "filename": "paper.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 245760,
  "sha256": "64-character-lowercase-hex",
  "is_original": true,
  "source_artifact_id": null
}
```

Service 校验扩展名、声明 MIME、大小限制、同项目 source relation，并生成 Artifact ID 与不含用户路径片段的 `storage_key`。响应：

```http
201 Created
```

```json
{
  "data": {
    "upload_id": "artifact-uuid",
    "artifact_id": "artifact-uuid",
    "status": "UPLOADING",
    "upload_method": "PUT",
    "upload_url": "/api/v1/artifact-uploads/{upload_id}/content",
    "required_headers": {
      "Content-Type": "application/octet-stream"
    },
    "expires_at": "2026-07-31T09:00:00Z"
  },
  "meta": {
    "request_id": "uuid",
    "idempotency_replayed": false
  }
}
```

Bucket、storage key 和对象存储凭据不进入公共响应。

## 14B.3 受控文件传输

```http
PUT /api/v1/artifact-uploads/{upload_id}/content
Content-Type: application/octet-stream
```

需要当前用户仍有 Artifact 所属项目的 `artifact.upload` 权限。API 以流式方式写入后端控制的临时对象；文件名不参与路径。一个 upload session 只接受一次成功传输，不支持分片或断点续传。再次 PUT 返回 `409 INVALID_STATE_TRANSITION`，不得覆盖临时或正式对象。

成功返回 `204 No Content`。传输中断保持 Artifact 为 `UPLOADING`，过期回收转为 `FAILED`；客户端必须新建 upload session。

## 14B.4 上传完成确认

```http
POST /api/v1/projects/{project_id}/artifacts/uploads/{upload_id}/complete
Idempotency-Key: <required>
```

请求：

```json
{
  "sha256": "64-character-lowercase-hex",
  "size_bytes": 245760
}
```

Service 必须重新读取已上传对象并自行计算 SHA-256、大小、MIME 和文件头。只有服务端结果同时匹配初始化声明与完成请求时才将 Artifact 转为 `AVAILABLE`。响应 `200 OK` 返回 Artifact detail。

不匹配时返回 `409 FILE_HASH_MISMATCH` 或适用文件错误，将 Artifact 标记为 `QUARANTINED`，不得下载。完成后检测到同项目已有 AVAILABLE 同 SHA-256 内容时仍保留当前独立 Artifact 和独立 storage key，并在 `meta.duplicate_of_artifact_id` 返回既有对象 ID；重复内容不是幂等重放。

## 14B.5 Artifact 详情

```http
GET /api/v1/artifacts/{artifact_id}
```

需要 `artifact.read`。响应至少包含 id、project_id、artifact_type、filename、original_filename、verified mime_type、size_bytes、sha256、source_artifact_id、is_original、is_immutable、status、created_by、created_at、deleted_at 和允许动作。不得返回 bucket、storage_key、内部路径或 Secret。

## 14B.6 授权下载

```http
GET /api/v1/artifacts/{artifact_id}/download
```

需要 `artifact.download`。只有 `AVAILABLE` 可下载；`QUARANTINED`、`FAILED`、`UPLOADING` 和 `DELETED` 均拒绝。响应：

```json
{
  "data": {
    "artifact_id": "uuid",
    "download_url": "short-lived-authorized-url",
    "expires_at": "2026-07-31T08:35:00Z",
    "disposition_filename": "paper.pdf"
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

`download_url` 可以是短期对象存储签名 URL 或短期后端流式下载 URL；客户端不得拼接 MinIO URL。每次请求重新校验项目权限和 Artifact 状态。

## 14B.7 Artifact 错误与审计

| HTTP | Code | 条件 |
| ---: | --- | --- |
| 404 | `RESOURCE_NOT_FOUND` | Artifact 或项目不可见/不存在 |
| 403 | `PERMISSION_DENIED` | active member 缺少 upload/read/download 动作 |
| 409 | `FILE_HASH_MISMATCH` | 服务端哈希或大小与声明不一致 |
| 409 | `INVALID_STATE_TRANSITION` | 重复传输、重复完成或终态上传 |
| 413 | `FILE_TOO_LARGE` | 超过当前服务端限制 |
| 415 | `FILE_TYPE_UNSUPPORTED` | 扩展名、MIME 或文件头不允许 |
| 503 | `FILE_UPLOAD_FAILED` | 存储不可用且没有形成 AVAILABLE Artifact |

初始化、成功完成、失败/隔离和授权下载必须分别记录 `ARTIFACT_UPLOAD_INITIATED`、`ARTIFACT_AVAILABLE`、`ARTIFACT_UPLOAD_FAILED`/`ARTIFACT_QUARANTINED` 和 `ARTIFACT_DOWNLOAD_AUTHORIZED`。Audit snapshot 不保存文件正文、bucket、storage key 或签名 URL。

Artifact soft delete 在 M1 是内部 Service command，供拥有具体业务资源的后续模块调用；没有 generic public Artifact delete API。

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
  "page_size": 25,
  "use_cache": true
}
```

Service 根据 QueryPlan、可用性、许可证与策略选择实际 Provider。既有
`provider` 字段仅保留为向后兼容的可选管理员/测试提示；普通客户端应省略，
模型不得指定 PyAlex、OpenAlex 或其他实现。实际引擎记录在 SearchRun 与
ProcessingRun，不进入公共资源命名。

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
    "uuid",
    "uuid"
  ]
}
```

`result_ids` 是检索运行内的 RECA 候选结果 ID，不是上游对象 ID。OpenAlex Work
ID、DOI 和原始响应只保存在候选元数据与来源记录中；导入后创建或匹配
`LiteratureRecord`。

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

ASReview 或其他排序引擎不调用决策写接口。其输出通过既有 ProcessingRun、
ToolCall 候选输出或 LiteratureRecord 展示投影提供 `rank`、`priority_score`、
`rationale` 和限制；用户提交上述决策请求后才创建 LiteratureDecision。筛选
能力不可用时回退人工排序，不改变当前决定。

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
  "allow_fallback": true,
  "extract_coordinates": true
}
```

返回 Job。

既有 `preferred_parser` 字段仅保留为管理员/测试兼容提示。普通客户端不选择
GROBID 或 pypdf；Service 选择实际解析器并记录 ProcessingRun。GROBID TEI 是
不可变中间产物，必须经 RECA Converter 后才能形成页面、Chunk 或引用候选。

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
  "evidence_type": "SAMPLE_DESCRIPTION",
  "user_declared_read_scope": "SECTIONS"
}
```

服务端必须记录 `source_text_hash`、解析器及其版本、页码和 `bounding_boxes`；初始 `location_verification_status` 只能为 `EXTRACTED`、`LOCATED` 或 `LOCATION_UNCERTAIN`，不得因为模型声称已阅读而设为 `VERIFIED`。`user_declared_read_scope` 仅记录用户声明的范围（`UNKNOWN`、`ABSTRACT`、`SECTIONS`、`FULL_TEXT_DECLARED`），`parser_coverage` 单独记录机器覆盖，两者均不等同于系统确认的全文阅读。

## 17.9A 确认证据定位与阅读范围

```http
POST /api/v1/evidence-spans/{evidence_span_id}/verification-records
```

```json
{
  "location_verification_status": "VERIFIED",
  "user_declared_read_scope": "SECTIONS",
  "reviewed_page_numbers": [8],
  "note": "已核对本页样本描述与原文一致。"
}
```

该记录只能由用户或具有显式人工审核身份的服务账户创建，保留 actor、时间、所见页码和原始文本哈希。缺失已解析页文本、页码或定位框时，服务必须拒绝将状态升级为 `VERIFIED`；定位失败且没有候选片段时不创建 EvidenceSpan，而是在 LiteratureExtractionField 保存 `evidence_status = NO_LOCATED_EVIDENCE` 与原因；有候选片段但定位不足时才使用 `LOCATION_UNCERTAIN`。

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
        "candidate_id": "uuid",
        "evidence_span_id": null,
        "literature_record_id": "uuid",
        "document_id": "uuid",
        "chunk_id": "uuid",
        "page_number": 6,
        "source_text": "……",
        "source_text_hash": "sha256",
        "retrieval_run_id": "uuid",
        "keyword_score": 0.74,
        "vector_score": 0.81,
        "fused_rank": 1,
        "rerank_score": 0.88,
        "limitations": []
      }
    ],
    "limitations": []
  }
}
```

这是向后兼容的候选响应扩展。`evidence_span_id` 保留原字段名，但在候选尚未
完成原文、页码、文档版本和哈希校验时必须为 `null`；不得为了满足旧响应示例
而伪造 EvidenceSpan。PaperQA 或其他实现只能影响召回、排序和 packing。当前
集合证据不足时返回空 `candidates` 与明确 `limitations`，不是 Provider 错误。

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

# 25. Approvals API

## 25.0 创建责任与有效性

Generic Approval create API：`NO`。

```text
domain operation
→ owning Service determines FORMAL_APPROVAL
→ Service builds canonical payload snapshot and SHA-256
→ Service creates PENDING ApprovalRecord
→ user decides through the APIs below
→ owning Service revalidates permission, target version and payload hash before execution
```

M1 只建设该基础设施，不制造一个仅用于演示的 FORMAL_APPROVAL consumer。ResearchQuestion、CleaningPlan、AnalysisPlan 等后续领域命令在其里程碑按正式需求创建 ApprovalRecord。

## 25.1 审批列表

```http id="r39whm"
GET /api/v1/projects/{project_id}/approvals
```

过滤：

* `status`；
* `approval_type`；
* `target_object_type`；
* `requested_by_actor_type`。

需要 `approval.read`。响应必须包含 `payload_hash`、目标、requester、status、decision、expires_at、supersedes_approval_id、allowed_actions 和脱敏 impact summary；普通列表不返回完整 payload_snapshot。

---

## 25.2 审批详情

```http id="0rd817"
GET /api/v1/approvals/{approval_id}
```

需要 `approval.read`。详情可返回完成决定所需的 payload_snapshot 和逐项决定结构，但必须按项目权限与敏感字段政策脱敏。

---

## 25.3 批准

```http id="1zbzba"
POST /api/v1/approvals/{approval_id}/approve
Idempotency-Key: <required>
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
Idempotency-Key: <required>
```

拒绝原因必填。

---

## 25.5 取消审批请求

```http id="wu9v8h"
POST /api/v1/approvals/{approval_id}/cancel
Idempotency-Key: <required>
```

仅发起者或有管理权限用户可执行。

## 25.6 决定规则

* approve/reject 需要 `approval.decide`，只允许 OWNER、REVIEWER 或 superuser administrative override；Agent、Worker 和 SYSTEM 不能批准或拒绝；
* cancel 只允许请求者、OWNER 或 superuser，且只允许 PENDING；
* 决策前校验 `expires_at`。已过期记录转为 EXPIRED 并返回 `409 APPROVAL_EXPIRED`；
* 决策前重算目标规范化 snapshot hash。PENDING 记录与 `payload_hash` 不同则转为 SUPERSEDED 并返回 `409 APPROVAL_STALE`；已决定记录保持原终态，后续新审批通过 `supersedes_approval_id` 引用它；
* PENDING 以外的 approve/reject/cancel 使用新 Idempotency-Key 时返回 `409 INVALID_STATE_TRANSITION`；同 Key、同 payload 返回首次响应并设置 `meta.idempotency_replayed=true`；
* `item_decisions` 必须覆盖领域命令声明为必选的 item。ApprovalItem 可独立持久化或由严格 payload_snapshot 承载，但公共响应语义不变；
* 每个决定创建 append-only AuditLog，绑定 approval_id、request_id、actor、project、before/after、reason 和 outcome；
* APPROVED 仅表示用户决定有效，不表示原领域操作已经执行。

---

# 26. AuditLog API

## 26.1 项目操作日志

```http
GET /api/v1/projects/{project_id}/audit-logs
```

这是只读 projection。不存在 `POST /audit-logs`、PATCH 或 DELETE API。

权限：`audit.read`。过滤与分页：

```text
actor_type
action
object_type
object_id
outcome
request_id
job_id
approval_id
from
to
page
page_size
```

排序固定为 `created_at desc, id desc`，不接受任意 sort 字段。

响应项：

```json
{
  "id": "audit-uuid",
  "project_id": "project-uuid",
  "actor": {
    "type": "USER",
    "id": "user-uuid",
    "display_name": "成员姓名"
  },
  "action": "PROJECT_MEMBER_ROLE_CHANGED",
  "target": {
    "type": "project_member",
    "id": "membership-uuid",
    "label": "member@example.edu"
  },
  "before": {"role": "EDITOR"},
  "after": {"role": "REVIEWER"},
  "reason": "负责方法复核。",
  "outcome": "SUCCEEDED",
  "request_id": "uuid",
  "job_id": null,
  "approval_id": null,
  "created_at": "2026-07-31T08:30:00Z"
}
```

Service 必须对 before/after、reason 和 target label 进行敏感字段白名单投影。不得返回密码、Token、Cookie、Secret、完整文件正文、模型敏感输入、storage key、内部路径或签名 URL。跨项目访问按 14.0 no-disclosure 规则处理。

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

# 兼容性路径索引：项目、研究、文献、审批与 AgentRun

以下索引保留原附录 A 基线，并加入本次 M1 additive amendment 的 Member、Artifact 和
Audit read paths。它不是第二份完整端点定义；请求、响应、错误和前置条件以本文件对应
资源章节为准。既有 `{id}` 参数命名保持兼容；新增路径使用本次冻结的具体参数名。

```text
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
GET    /api/v1/projects/{project_id}/overview
POST   /api/v1/projects/{project_id}/archive
POST   /api/v1/projects/{project_id}/restore
DELETE /api/v1/projects/{project_id}
GET    /api/v1/projects/{project_id}/members
POST   /api/v1/projects/{project_id}/members
PATCH  /api/v1/projects/{project_id}/members/{member_id}
DELETE /api/v1/projects/{project_id}/members/{member_id}
GET    /api/v1/projects/{project_id}/artifacts
POST   /api/v1/projects/{project_id}/artifacts/uploads
PUT    /api/v1/artifact-uploads/{upload_id}/content
POST   /api/v1/projects/{project_id}/artifacts/uploads/{upload_id}/complete
GET    /api/v1/artifacts/{artifact_id}
GET    /api/v1/artifacts/{artifact_id}/download
GET    /api/v1/projects/{project_id}/audit-logs
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
POST   /api/v1/evidence-spans/{id}/verification-records
GET    /api/v1/projects/{project_id}/literature-matrix
POST   /api/v1/projects/{project_id}/evidence-search
POST   /api/v1/projects/{project_id}/evidence-set-summaries
GET    /api/v1/evidence-set-summaries/{id}
POST   /api/v1/projects/{project_id}/topic-generation-runs
GET    /api/v1/projects/{project_id}/approvals
GET    /api/v1/approvals/{id}
POST   /api/v1/approvals/{id}/approve
POST   /api/v1/approvals/{id}/reject
POST   /api/v1/approvals/{id}/cancel
POST   /api/v1/projects/{project_id}/agent-runs
GET    /api/v1/agent-runs/{id}
GET    /api/v1/agent-runs/{id}/tool-calls
POST   /api/v1/agent-runs/{id}/messages
POST   /api/v1/agent-runs/{id}/cancel
```
