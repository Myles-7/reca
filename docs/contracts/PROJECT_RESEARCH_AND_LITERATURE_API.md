# PROJECT_RESEARCH_AND_LITERATURE_API

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

Projects、Research Questions、Scoping、QueryPlan、Literature、Documents、Extraction、EvidenceSpan、TopicCandidate、Approvals 和 AgentRun 资源 API 的唯一完整定义。

## 不负责的内容

不定义数据分析、论文导出、AI 输出 Schema 或 Agent Tool。原契约缺失的 Members/Artifact CRUD 不在本次拆分中补造。

## 文档导航

- 返回 [API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- [COMMON_API_JOB_AND_SSE_CONTRACTS.md](COMMON_API_JOB_AND_SSE_CONTRACTS.md)
- [PROJECT_RESEARCH_AND_LITERATURE_API.md](PROJECT_RESEARCH_AND_LITERATURE_API.md)
- [DATA_ANALYSIS_AND_FIGURE_API.md](DATA_ANALYSIS_AND_FIGURE_API.md)
- [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)
- [AI_SCHEMA_CONTRACTS.md](AI_SCHEMA_CONTRACTS.md)
- [AGENT_TOOL_CONTRACTS.md](AGENT_TOOL_CONTRACTS.md)

以下正文由原入口文档对应章节机械迁入。路径、字段、错误码、Schema、Tool 名称和契约语义保持原样。


## Members 与 Artifact API 边界

原契约没有独立的 ProjectMember 或 Artifact CRUD 路径。成员管理和通用 Artifact API 因而仍是未决契约缺口；本次拆分不虚构端点。现有 Artifact 只通过 PDF、Dataset、Manuscript、Figure 和 Export 等资源端点及 Adapter 的 `ArtifactReference` 出现。后续补充必须经过正式契约变更。

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

以下字符串从原附录 A 原样迁入，仅保留旧 `{id}` 参数命名和总览兼容性。它们不是第二份完整端点定义；请求、响应、错误和前置条件以本文件对应资源章节为准。不得在本阶段擅自将 `{id}` 与更具体的参数名合并或重命名。

```text
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
