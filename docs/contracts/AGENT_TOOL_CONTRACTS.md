# AGENT_TOOL_CONTRACTS

- 所属入口文档：[API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

所有白名单 Tool、参数、返回、前置状态、权限、数据访问、审批、副作用、幂等、审计、工具状态和禁止行为的唯一完整定义。

## 不负责的内容

不定义业务资源 API 或 AI 输出 Schema；Tool 不能直接访问数据库或扩大 Prompt/Policy 权限。

## 文档导航

- 返回 [API_AI_TOOL_CONTRACTS.md](../API_AI_TOOL_CONTRACTS.md)
- [COMMON_API_JOB_AND_SSE_CONTRACTS.md](COMMON_API_JOB_AND_SSE_CONTRACTS.md)
- [PROJECT_RESEARCH_AND_LITERATURE_API.md](PROJECT_RESEARCH_AND_LITERATURE_API.md)
- [DATA_ANALYSIS_AND_FIGURE_API.md](DATA_ANALYSIS_AND_FIGURE_API.md)
- [MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md](MANUSCRIPT_EVIDENCE_AND_EXPORT_API.md)
- [AI_SCHEMA_CONTRACTS.md](AI_SCHEMA_CONTRACTS.md)
- [AGENT_TOOL_CONTRACTS.md](AGENT_TOOL_CONTRACTS.md)

以下正文由原入口文档对应章节机械迁入。路径、字段、错误码、Schema、Tool 名称和契约语义保持原样。


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
| prompt_contract_id     | 允许发起本工具调用的 Prompt 合同标识 |
| max_allowed_data_access_level | 本工具/策略允许的最高模型数据访问级别 |
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
  "degradation": null,
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

<a id="tool-approve-on-behalf-of-user"></a>
<a id="tool-bypass-permission"></a>
<a id="tool-delete-original-file"></a>
<a id="tool-download-paid-fulltext"></a>
<a id="tool-execute-python"></a>
<a id="tool-execute-shell"></a>
<a id="tool-execute-sql"></a>
<a id="tool-generate-complete-thesis"></a>
<a id="tool-get-analysis-plan"></a>
<a id="tool-get-analysis-result"></a>
<a id="tool-get-claim-evidence-graph"></a>
<a id="tool-get-dataset-profile"></a>
<a id="tool-get-dataset-version"></a>
<a id="tool-get-export-readiness"></a>
<a id="tool-get-figure"></a>
<a id="tool-get-literature-matrix"></a>
<a id="tool-get-literature-record"></a>
<a id="tool-get-manuscript-issues"></a>
<a id="tool-get-pending-approvals"></a>
<a id="tool-get-research-question"></a>
<a id="tool-list-project-literature"></a>
<a id="tool-modify-analysis-result"></a>
<a id="tool-overwrite-dataset"></a>
<a id="tool-run-arbitrary-code"></a>
<a id="tool-suggest-literature-decision"></a>

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

<a id="tool-get-project-state"></a>

# 43. get_project_state / ProjectContextSnapshot

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
  "snapshot_schema_version": "1.0",
  "snapshot_revision": 1,
  "snapshot_hash": "sha256",
  "generated_at": "2026-07-30T09:00:00Z",
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
  "available_artifact_ids": [],
  "source_object_versions": {},
  "blocking_issue_ids": [],
  "allowed_next_actions": ["RUN_APPROVED_ANALYSIS"],
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

`ProjectContextSnapshot` 是从数据库领域对象实时派生的只读输入：不得由 Agent、工具输出或会话状态反向写入；每个 AgentRun 默认记录 `snapshot_schema_version`、`snapshot_revision`、`snapshot_hash`、`source_object_versions` 与 `safe_snapshot_summary`，而非完整敏感快照。任何 source object 版本变化都会令先前快照过期。该工具是内部只读查询工具，不新增公共 REST 端点，也不返回超出任务所需的完整原文或敏感数据。

---

<a id="tool-parse-research-question"></a>

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

<a id="tool-generate-query-plan"></a>

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

<a id="tool-search-literature"></a>

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

<a id="tool-verify-literature-record"></a>

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

<a id="tool-parse-document"></a>

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

<a id="tool-extract-literature-fields"></a>

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

<a id="tool-retrieve-evidence"></a>

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

<a id="tool-summarize-evidence-set"></a>

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

<a id="tool-generate-topic-candidates"></a>

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

<a id="tool-profile-dataset"></a>

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

<a id="tool-suggest-cleaning-plan"></a>

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

<a id="tool-preview-cleaning-plan"></a>

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

<a id="tool-apply-approved-transformations"></a>

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

<a id="tool-suggest-analysis-plan"></a>

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

<a id="tool-validate-analysis-assumptions"></a>

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

<a id="tool-run-descriptive-statistics"></a>

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

<a id="tool-run-group-comparison"></a>

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

<a id="tool-run-correlation"></a>

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

<a id="tool-run-simple-linear-regression"></a>

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

<a id="tool-recommend-figure"></a>

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

<a id="tool-render-figure"></a>

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

<a id="tool-check-manuscript"></a>

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

<a id="tool-suggest-manuscript-issues"></a>

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

<a id="tool-audit-claim"></a>

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

<a id="tool-export-repro-package"></a>

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
