# MANUSCRIPT_AGENT_AND_EXPORT_MODELS

- 所属入口文档：[DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

Manuscript、ManuscriptVersion、ManuscriptIssue、Claim、ClaimEvidenceLink、AuditResult、AgentRun、ToolCall、ModelInvocation、ProjectContextSnapshot、Export 和 ReproPackage 的完整模型定义。

## 不负责的内容

不定义 Prompt 注册表元数据、降级 DTO 或状态转换；Agent Session 不是业务事实来源。

## 文档导航

- 返回 [DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- [FOUNDATION_AND_PROJECT_MODELS.md](FOUNDATION_AND_PROJECT_MODELS.md)
- [LITERATURE_AND_EVIDENCE_MODELS.md](LITERATURE_AND_EVIDENCE_MODELS.md)
- [DATA_ANALYSIS_AND_FIGURE_MODELS.md](DATA_ANALYSIS_AND_FIGURE_MODELS.md)
- [MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md](MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md)
- [STATE_MACHINES_AND_INVARIANTS.md](STATE_MACHINES_AND_INVARIANTS.md)

以下正文由原入口文档对应对象或章节机械迁入；字段、枚举、约束、外键和语义保持不变。

# 18. 论文领域模型

## 18.1 Manuscript

逻辑论文对象。

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| project_id         | UUID     |  是 |
| title              | String   |  否 |
| current_version_id | UUID     |  否 |
| status             | Enum     |  是 |
| created_by         | UUID     |  是 |
| created_at         | DateTime |  是 |
| updated_at         | DateTime |  是 |

---

## 18.2 ManuscriptVersion

具体 DOCX 版本。

### 字段

| 字段                       | 类型       | 必填 |
| ------------------------ | -------- | -: |
| id                       | UUID     |  是 |
| manuscript_id            | UUID     |  是 |
| project_id               | UUID     |  是 |
| version_number           | Integer  |  是 |
| parent_version_id        | UUID     |  否 |
| artifact_id              | UUID     |  是 |
| version_type             | Enum     |  是 |
| source_transformation_id | UUID     |  否 |
| status                   | Enum     |  是 |
| created_by               | UUID     |  否 |
| created_at               | DateTime |  是 |

### version_type

* `ORIGINAL`；
* `USER_UPLOAD`；
* `AUTO_FIXED`；
* `USER_REVISED`；
* `DERIVED`。

### 规则

* 原始版本不可覆盖；
* 自动修复生成新版本；
* 高风险语义问题不得自动生成修改版。

---

## 18.3 ManuscriptCheckRun

### 字段

| 字段                         | 类型       | 必填 |
| -------------------------- | -------- | -: |
| id                         | UUID     |  是 |
| project_id                 | UUID     |  是 |
| manuscript_version_id      | UUID     |  是 |
| rule_set_version           | String   |  是 |
| status                     | Enum     |  是 |
| issue_count                | Integer  |  否 |
| high_issue_count           | Integer  |  否 |
| processing_run_id          | UUID     |  否 |
| source_model_invocation_id | UUID     |  否 |
| started_at                 | DateTime |  否 |
| completed_at               | DateTime |  否 |
| created_at                 | DateTime |  是 |

---

## 18.4 ManuscriptIssue

### 字段

| 字段                         | 类型       | 必填 |
| -------------------------- | -------- | -: |
| id                         | UUID     |  是 |
| project_id                 | UUID     |  是 |
| manuscript_check_run_id    | UUID     |  是 |
| manuscript_version_id      | UUID     |  是 |
| issue_type                 | Enum     |  是 |
| severity                   | Enum     |  是 |
| section_name               | String   |  否 |
| paragraph_index            | Integer  |  否 |
| table_index                | Integer  |  否 |
| original_text              | Text     |  否 |
| normalized_reference       | Text     |  否 |
| reason                     | Text     |  是 |
| suggestion                 | Text     |  否 |
| auto_fixable               | Boolean  |  是 |
| status                     | Enum     |  是 |
| source_model_invocation_id | UUID     |  否 |
| created_at                 | DateTime |  是 |
| resolved_at                | DateTime |  否 |

### issue_type

* `IN_TEXT_CITATION_MISSING_REFERENCE`；
* `UNUSED_REFERENCE`；
* `CITATION_METADATA_MISMATCH`；
* `DUPLICATE_REFERENCE`；
* `INVALID_DOI_FORMAT`；
* `SAMPLE_SIZE_MISMATCH`；
* `STATISTIC_MISMATCH`；
* `FIGURE_TEXT_MISMATCH`；
* `CAUSAL_OVERCLAIM`；
* `POPULATION_OVERGENERALIZATION`；
* `CONSENSUS_OVERCLAIM`；
* `TERMINOLOGY_INCONSISTENCY`；
* `UNDEFINED_ABBREVIATION`；
* `HEADING_LEVEL_ISSUE`；
* `FIGURE_NUMBERING_ISSUE`；
* `UNIT_FORMAT_ISSUE`；
* `PUNCTUATION_ISSUE`。

### status

* `OPEN`；
* `ACKNOWLEDGED`；
* `ACCEPTED`；
* `REJECTED`；
* `RESOLVED`；
* `INVALIDATED`。

---

## 18.5 ManuscriptIssueEvidence

关联论文问题的证据。

| 字段                   | 类型     | 必填 |
| -------------------- | ------ | -: |
| id                   | UUID   |  是 |
| manuscript_issue_id  | UUID   |  是 |
| evidence_type        | Enum   |  是 |
| evidence_object_type | String |  是 |
| evidence_object_id   | UUID   |  否 |
| evidence_text        | Text   |  否 |
| metadata             | JSONB  |  否 |

evidence_type：

* `LITERATURE_RECORD`；
* `EVIDENCE_SPAN`；
* `ANALYSIS_RESULT`；
* `FIGURE`；
* `MANUSCRIPT_LOCATION`；
* `RULE`。

---

## 18.6 ManuscriptTransformation

P0 仅用于低风险格式修复。

字段：

* manuscript_version_id；
* approved_issue_ids；
* output_manuscript_version_id；
* code_artifact_id；
* status；
* log；
* created_at。

---

# 19. Claim 与证据链模型

## 19.1 Claim

Claim 表示系统中需要被证据支持、反对或限定的科研论述。

### Claim 来源

* 文献综述结论；
* 候选研究问题依据；
* 数据分析解释；
* 图表说明；
* 论文中的句子或段落；
* 审核生成的待验证论述。

### 字段

| 字段                    | 类型          | 必填 |
| --------------------- | ----------- | -: |
| id                    | UUID        |  是 |
| project_id            | UUID        |  是 |
| claim_type            | Enum        |  是 |
| source_object_type    | String      |  否 |
| source_object_id      | UUID        |  否 |
| source_location       | JSONB       |  否 |
| claim_text            | Text        |  是 |
| normalized_claim      | Text        |  否 |
| scope_statement       | Text        |  否 |
| status                | Enum        |  是 |
| confidence            | Enum        |  否 |
| created_by_actor_type | Enum        |  是 |
| created_by_actor_id   | UUID/String |  否 |
| created_at            | DateTime    |  是 |
| updated_at            | DateTime    |  是 |
| invalidated_at        | DateTime    |  否 |

### claim_type

* `LITERATURE_SUMMARY`；
* `CONSENSUS`；
* `CONTROVERSY`；
* `EVIDENCE_GAP`；
* `TOPIC_RATIONALE`；
* `DATA_DESCRIPTION`；
* `STATISTICAL_RESULT`；
* `INTERPRETATION`；
* `MANUSCRIPT_STATEMENT`。

### 状态

* `DRAFT`；
* `NEEDS_EVIDENCE`；
* `SUPPORTED`；
* `CONFLICTED`；
* `INSUFFICIENT`；
* `CONFIRMED`；
* `REJECTED`；
* `INVALIDATED`。

---

## 19.2 ClaimEvidenceLink

证据链核心关系表。

### 字段

| 字段                         | 类型       | 必填 |
| -------------------------- | -------- | -: |
| id                         | UUID     |  是 |
| project_id                 | UUID     |  是 |
| claim_id                   | UUID     |  是 |
| evidence_object_type       | Enum     |  是 |
| evidence_object_id         | UUID     |  是 |
| relation_type              | Enum     |  是 |
| strength                   | Enum     |  否 |
| explanation                | Text     |  否 |
| source_model_invocation_id | UUID     |  否 |
| confirmed_by_user_id       | UUID     |  否 |
| status                     | Enum     |  是 |
| created_at                 | DateTime |  是 |
| invalidated_at             | DateTime |  否 |

### evidence_object_type

* `LITERATURE_RECORD`；
* `EVIDENCE_SPAN`；
* `DATASET`；
* `DATASET_VERSION`；
* `DATA_TRANSFORMATION`；
* `ANALYSIS_PLAN`；
* `ANALYSIS_RUN`；
* `ANALYSIS_RESULT`；
* `FIGURE`；
* `APPROVAL_RECORD`；
* `AUDIT_RESULT`；
* `MANUSCRIPT_ISSUE`；
* `ARTIFACT`。

### relation_type

* `SUPPORTED_BY`；
* `CONTRADICTED_BY`；
* `QUALIFIED_BY`；
* `DERIVED_FROM`；
* `TRANSFORMED_FROM`；
* `ANALYZED_BY`；
* `PRODUCED_BY`；
* `VISUALIZED_AS`；
* `CONFIRMED_BY`；
* `AUDITED_BY`；
* `INVALIDATED_BY`。

### 强度

* `STRONG`；
* `MODERATE`；
* `WEAK`；
* `UNKNOWN`。

### 约束

* 关系不得跨项目；
* EvidenceSpan 必须真实存在；
* 失效证据不能继续作为 VERIFIED；
* 模型可建议关系，但高风险 Claim 需审核。

---

## 19.3 AuditResult

表示可信审核结果。

### 字段

| 字段                         | 类型       | 必填 |
| -------------------------- | -------- | -: |
| id                         | UUID     |  是 |
| project_id                 | UUID     |  是 |
| audit_type                 | Enum     |  是 |
| target_object_type         | String   |  是 |
| target_object_id           | UUID     |  是 |
| status                     | Enum     |  是 |
| findings                   | JSONB    |  是 |
| evidence_object_ids        | JSONB    |  否 |
| limitations                | JSONB    |  否 |
| source_model_invocation_id | UUID     |  否 |
| rule_set_version           | String   |  否 |
| created_at                 | DateTime |  是 |
| invalidated_at             | DateTime |  否 |

### audit_type

* `LITERATURE_EVIDENCE_AUDIT`；
* `NUMERIC_CONSISTENCY_AUDIT`；
* `FIGURE_VERSION_AUDIT`；
* `CAUSALITY_AUDIT`；
* `CLAIM_COMPLETENESS_AUDIT`；
* `EXPORT_READINESS_AUDIT`。
* `REVISION_DRIFT_AUDIT`；
* `READ_SCOPE_AUDIT`；
* `PROMPT_CONTRACT_AUDIT`；
* `DEGRADATION_AUDIT`。

### 标准 Finding Code

`findings` 中的每条发现必须包含稳定的 `code`。P0 至少定义：

```text
CLAIM_NO_EVIDENCE
CLAIM_SOURCE_NOT_IN_PROJECT
CLAIM_EVIDENCE_SCOPE_MISMATCH
CLAIM_CAUSAL_OVERSTATEMENT
CLAIM_UNBOUNDED_NOVELTY
CLAIM_NUMERIC_MISMATCH
CLAIM_FIGURE_VERSION_MISMATCH
CLAIM_STALE_AFTER_REVISION
```

### status

* `VERIFIED`；
* `NEEDS_REVIEW`；
* `INSUFFICIENT_EVIDENCE`；
* `SOURCE_INCOMPLETE`；
* `CONFLICTED`；
* `DATA_MISMATCH`；
* `FIGURE_MISMATCH`；
* `OVERCLAIM_RISK`；
* `REJECTED_BY_USER`；
* `INVALIDATED`。

---

## 19.4 EvidenceGraphSnapshot

用于保存某次导出或演示时的图谱快照。

### 字段

* project_id；
* node_count；
* edge_count；
* snapshot_json；
* generated_at；
* source_export_id；
* schema_version。

数据库事实仍以节点和边表为准。

---

# 22. Agent 与模型运行模型：运行与快照

## 22.1 AgentRun

### 字段

| 字段                     | 类型       | 必填 |
| ---------------------- | -------- | -: |
| id                     | UUID     |  是 |
| project_id             | UUID     |  是 |
| user_id                | UUID     |  是 |
| agent_type             | Enum     |  是 |
| session_id             | String   |  否 |
| status                 | Enum     |  是 |
| user_goal              | Text     |  否 |
| project_state_snapshot | JSONB    |  否 |
| plan                   | JSONB    |  否 |
| started_at             | DateTime |  是 |
| completed_at           | DateTime |  否 |
| error_code             | String   |  否 |
| trace_identifier       | String   |  否 |

agent_type P0：

```text
RESEARCH_ORCHESTRATOR
TRUST_AUDITOR
```

可信审核可以实现为总控 Agent 的审核步骤，也可记录独立类型。

---

## 22.2 ToolCall

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| project_id         | UUID     |  是 |
| agent_run_id       | UUID     |  是 |
| tool_name          | String   |  是 |
| tool_version       | String   |  是 |
| input_summary      | JSONB    |  是 |
| input_hash         | String   |  是 |
| status             | Enum     |  是 |
| approval_record_id | UUID     |  否 |
| output_object_type | String   |  否 |
| output_object_id   | UUID     |  否 |
| output_summary     | JSONB    |  否 |
| started_at         | DateTime |  是 |
| completed_at       | DateTime |  否 |
| error_code         | String   |  否 |
| error_message      | Text     |  否 |

### 状态

* `REQUESTED`；
* `WAITING_APPROVAL`；
* `RUNNING`；
* `COMPLETED`；
* `FAILED`；
* `DENIED`；
* `CANCELLED`。

---

## 22.3 ModelInvocation

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| project_id         | UUID     |  否 |
| agent_run_id       | UUID     |  否 |
| tool_call_id       | UUID     |  否 |
| task_type          | Enum     |  是 |
| provider           | String   |  是 |
| model              | String   |  是 |
| requested_data_access_level | Enum | 是 |
| max_allowed_data_access_level | Enum | 是 |
| effective_data_access_level | Enum | 是 |
| redaction_policy_version | String | 否 |
| prompt_id          | String   |  是 |
| prompt_version     | String   |  是 |
| prompt_content_hash | String  |  是 |
| input_schema_version | String | 是 |
| output_schema_version | String | 是 |
| schema_name        | String   |  否 |
| schema_version     | String   |  否 |
| input_source_ids   | JSONB    |  否 |
| input_hash         | String   |  是 |
| status             | Enum     |  是 |
| token_input        | Integer  |  否 |
| token_output       | Integer  |  否 |
| latency_ms         | Integer  |  否 |
| output_artifact_id | UUID     |  否 |
| fallback_provider  | String   |  否 |
| fallback_model     | String   |  否 |
| degradation_record | JSONB    |  否 |
| consent_record_id  | UUID     |  否 |
| error_code         | String   |  否 |
| created_at         | DateTime |  是 |
| completed_at       | DateTime |  否 |

### 规则

* 不默认存储完整敏感输入；
* 可保存脱敏摘要和哈希；
* 输出必须可追溯到 Schema；
* 统计数字不得来自 ModelInvocation。
* `requested_data_access_level` 是 PromptContract 的最低必要级别；
  `max_allowed_data_access_level` 是 Tool/Policy 的上限；
  `effective_data_access_level` 是本次实际发送内容的级别，必须不高于上限并遵循最小化原则；
* 回退模型不得自动继承更高的数据访问权限；
* 不默认保存完整敏感输入或完整未公开稿件。

### 数据访问等级

```text
METADATA_ONLY
REDACTED_CONTENT
VERIFIED_EVIDENCE_ONLY
APPROVED_FULL_CONTENT
```

## 22.5 ProjectContextSnapshot

`ProjectContextSnapshot` 是派生查询 Schema，不是可写业务表或第二事实来源。
它至少包含：

```text
snapshot_schema_version
snapshot_revision
project_id
current_stage
source_object_versions
available_artifact_ids
pending_approval_ids
blocking_issue_ids
allowed_next_actions
generated_at
snapshot_hash
```

快照由数据库对象和授权上下文重新生成；任一 `source_object_versions` 变化即使旧快照过期。AgentRun 默认仅保存 `snapshot_schema_version`、`snapshot_revision`、`snapshot_hash`、`source_object_versions` 与 `safe_snapshot_summary`，不保存完整敏感快照；快照不得反向覆盖 ResearchProject、ApprovalRecord 或其他正式对象。

# 23. 导出模型

## 23.1 Export

### 字段

| 字段                   | 类型       | 必填 |
| -------------------- | -------- | -: |
| id                   | UUID     |  是 |
| project_id           | UUID     |  是 |
| export_type          | Enum     |  是 |
| status               | Enum     |  是 |
| requested_by_user_id | UUID     |  是 |
| scope                | JSONB    |  是 |
| readiness_audit_id   | UUID     |  否 |
| job_id               | UUID     |  否 |
| created_at           | DateTime |  是 |
| completed_at         | DateTime |  否 |
| error_code           | String   |  否 |

export_type：

* `REPRO_PACKAGE`；
* `LITERATURE_MATRIX`；
* `DATA_QUALITY_REPORT`；
* `ANALYSIS_REPORT`；
* `MANUSCRIPT_CHECK_REPORT`。

---

## 23.2 ReproPackage

### 字段

| 字段                       | 类型         | 必填 |
| ------------------------ | ---------- | -: |
| id                       | UUID       |  是 |
| export_id                | UUID       |  是 |
| project_id               | UUID       |  是 |
| artifact_id              | UUID       |  是 |
| manifest_artifact_id     | UUID       |  是 |
| package_version          | Integer    |  是 |
| schema_version           | String     |  是 |
| contains_sensitive_data  | Boolean    |  是 |
| contains_restricted_data | Boolean    |  是 |
| file_count               | Integer    |  是 |
| total_size_bytes         | BigInteger |  是 |
| sha256                   | String     |  是 |
| created_at               | DateTime   |  是 |

---

## 23.3 ExportItem

记录包内每项来源。

字段：

* export_id；
* object_type；
* object_id；
* artifact_id；
* package_path；
* sha256；
* include_status；
* exclusion_reason。

---
