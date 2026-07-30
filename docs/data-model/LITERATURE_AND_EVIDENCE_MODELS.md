# LITERATURE_AND_EVIDENCE_MODELS

- 所属入口文档：[DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

ResearchQuestion、ResearchQuestionVersion、QueryPlan、LiteratureRecord、Document、页面和 Chunk、抽取字段、EvidenceSpan、文献决策、证据集合分析与 TopicCandidate 的完整模型定义。

## 不负责的内容

不定义数据分析、论文 Claim、Agent 运行或状态转换的跨对象规则。

## 文档导航

- 返回 [DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- [FOUNDATION_AND_PROJECT_MODELS.md](FOUNDATION_AND_PROJECT_MODELS.md)
- [LITERATURE_AND_EVIDENCE_MODELS.md](LITERATURE_AND_EVIDENCE_MODELS.md)
- [DATA_ANALYSIS_AND_FIGURE_MODELS.md](DATA_ANALYSIS_AND_FIGURE_MODELS.md)
- [MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md](MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md)
- [STATE_MACHINES_AND_INVARIANTS.md](STATE_MACHINES_AND_INVARIANTS.md)

以下正文由原入口文档对应对象或章节机械迁入；字段、枚举、约束、外键和语义保持不变。

# 8. 研究问题领域模型

## 8.1 ResearchQuestion

表示一个逻辑研究问题。

### 字段

| 字段                 | 类型       | 必填 | 说明                                  |
| ------------------ | -------- | -: | ----------------------------------- |
| id                 | UUID     |  是 | 逻辑对象 ID                             |
| project_id         | UUID     |  是 | 项目                                  |
| status             | Enum     |  是 | DRAFT、CONFIRMED、SUPERSEDED、ARCHIVED |
| current_version_id | UUID     |  否 | 当前版本                                |
| created_by         | UUID     |  是 | 创建人                                 |
| created_at         | DateTime |  是 | 创建时间                                |
| updated_at         | DateTime |  是 | 更新时间                                |

---

## 8.2 ResearchQuestionVersion

### 字段

| 字段                         | 类型       | 必填 | 说明                                            |
| -------------------------- | -------- | -: | --------------------------------------------- |
| id                         | UUID     |  是 | 版本 ID                                         |
| research_question_id       | UUID     |  是 | 逻辑对象                                          |
| project_id                 | UUID     |  是 | 项目                                            |
| version_number             | Integer  |  是 | 版本号                                           |
| raw_input                  | Text     |  是 | 用户原始输入                                        |
| normalized_question        | Text     |  否 | 规范化问题                                         |
| research_object            | Text     |  否 | 研究对象                                          |
| population                 | Text     |  否 | 人群                                            |
| context                    | Text     |  否 | 场景                                            |
| independent_variables      | JSONB    |  否 | 自变量                                           |
| dependent_variables        | JSONB    |  否 | 因变量                                           |
| control_variables          | JSONB    |  否 | 控制变量                                          |
| research_goal              | Enum     |  否 | DESCRIBE、COMPARE、RELATE、PREDICT               |
| relationship_type          | Enum     |  否 | ASSOCIATION、COMPARISON、PREDICTION、UNSPECIFIED |
| method_preference          | JSONB    |  否 | 方法偏好                                          |
| time_scope                 | JSONB    |  否 | 时间范围                                          |
| region_scope               | JSONB    |  否 | 地区范围                                          |
| language_scope             | JSONB    |  否 | 语言范围                                          |
| resource_constraints       | JSONB    |  否 | 资源约束                                          |
| ethical_constraints        | JSONB    |  否 | 伦理约束                                          |
| uncertainties              | JSONB    |  否 | 不确定项                                          |
| source_model_invocation_id | UUID     |  否 | AI 来源                                         |
| status                     | Enum     |  是 | DRAFT、NEEDS_INPUT、READY、CONFIRMED、SUPERSEDED  |
| created_by                 | UUID     |  是 | 创建人                                           |
| created_at                 | DateTime |  是 | 创建时间                                          |

### 约束

```text
UNIQUE(research_question_id, version_number)
```

确认版本必须有 ApprovalRecord。

---

# 10. 文档解析模型

## 10.1 Document

Document 表示上传后可被解析的文档。

### 字段

| 字段               | 类型       | 必填 | 说明                             |
| ---------------- | -------- | -: | ------------------------------ |
| id               | UUID     |  是 | 文档 ID                          |
| project_id       | UUID     |  是 | 项目                             |
| artifact_id      | UUID     |  是 | 原始 PDF Artifact                |
| document_type    | Enum     |  是 | SCHOLARLY_PDF、MANUSCRIPT、OTHER |
| parser_type      | Enum     |  否 | GROBID、PYPDF、NONE              |
| parser_version   | String   |  否 | 解析器版本                          |
| parse_status     | Enum     |  是 | 状态                             |
| page_count       | Integer  |  否 | 页数                             |
| language         | String   |  否 | 文档语言                           |
| is_scanned       | Boolean  |  否 | 是否扫描件                          |
| parse_confidence | Enum     |  否 | HIGH、MEDIUM、LOW、UNKNOWN        |
| created_at       | DateTime |  是 | 创建时间                           |
| updated_at       | DateTime |  是 | 更新时间                           |

### 区别

Document 是实际文件的业务对象。

LiteratureRecord 是学术文献信息。

一篇文献可以没有 PDF；一个 PDF 也可能暂未匹配 LiteratureRecord。

---

## 10.2 DocumentPage

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| document_id        | UUID     |  是 |
| project_id         | UUID     |  是 |
| page_number        | Integer  |  是 |
| printed_page_label | String   |  否 |
| text_content       | Text     |  否 |
| width              | Float    |  否 |
| height             | Float    |  否 |
| parser_metadata    | JSONB    |  否 |
| created_at         | DateTime |  是 |

### 约束

```text
UNIQUE(document_id, page_number)
```

---

## 10.3 DocumentChunk

### 字段

| 字段                | 类型       | 必填 |
| ----------------- | -------- | -: |
| id                | UUID     |  是 |
| project_id        | UUID     |  是 |
| document_id       | UUID     |  是 |
| page_start        | Integer  |  是 |
| page_end          | Integer  |  是 |
| section_path      | JSONB    |  否 |
| chunk_index       | Integer  |  是 |
| content           | Text     |  是 |
| content_hash      | String   |  是 |
| token_count       | Integer  |  否 |
| embedding         | Vector   |  否 |
| embedding_model   | String   |  否 |
| embedding_version | String   |  否 |
| metadata          | JSONB    |  否 |
| created_at        | DateTime |  是 |

### 约束

* 只能检索当前项目；
* Embedding 模型变化时可重新生成；
* 重建 Chunk 不覆盖旧解析版本时，应保留 ProcessingRun 关联。

---

# 11. 文献领域模型

## 11.1 LiteratureRecord

表示一条文献学术元数据。

### 字段

| 字段                  | 类型       | 必填 | 说明                                                |
| ------------------- | -------- | -: | ------------------------------------------------- |
| id                  | UUID     |  是 | 文献 ID                                             |
| project_id          | UUID     |  是 | 项目                                                |
| document_id         | UUID     |  否 | 关联 PDF                                            |
| source_type         | Enum     |  是 | OPENALEX、DOI_IMPORT、USER_UPLOAD、MANUAL、CACHE      |
| source_identifier   | String   |  否 | OpenAlex ID 等                                     |
| title               | Text     |  是 | 题目                                                |
| normalized_title    | Text     |  是 | 标准化题目                                             |
| abstract            | Text     |  否 | 摘要                                                |
| publication_year    | Integer  |  否 | 年份                                                |
| journal_name        | String   |  否 | 期刊                                                |
| doi                 | String   |  否 | DOI                                               |
| normalized_doi      | String   |  否 | 规范化 DOI                                           |
| authors_text        | Text     |  否 | 作者显示文本                                            |
| keywords            | JSONB    |  否 | 关键词                                               |
| work_type           | String   |  否 | 文献类型                                              |
| open_access_status  | String   |  否 | 开放状态                                              |
| verification_status | Enum     |  是 | VERIFIED、PARTIALLY_VERIFIED、UNVERIFIED、CONFLICTED |
| raw_source_data     | JSONB    |  否 | 数据源摘要                                             |
| current_decision    | Enum     |  是 | INCLUDED、EXCLUDED、UNCERTAIN                       |
| created_at          | DateTime |  是 | 创建时间                                              |
| updated_at          | DateTime |  是 | 更新时间                                              |
| deleted_at          | DateTime |  否 | 删除时间                                              |

### 唯一性

同项目中：

* `normalized_doi` 非空时应唯一；
* 无 DOI 时通过去重服务判断；
* 不设置标题强唯一，避免误合并。

---

## 11.2 LiteratureAuthor

可选独立表。

### 字段

| 字段                   | 类型      | 必填 |
| -------------------- | ------- | -: |
| id                   | UUID    |  是 |
| literature_record_id | UUID    |  是 |
| author_order         | Integer |  是 |
| display_name         | String  |  是 |
| family_name          | String  |  否 |
| given_name           | String  |  否 |
| orcid                | String  |  否 |
| institution          | String  |  否 |

---

## 11.3 QueryPlan

### 字段

| 字段                           | 类型       | 必填 |
| ---------------------------- | -------- | -: |
| id                           | UUID     |  是 |
| project_id                   | UUID     |  是 |
| research_question_version_id | UUID     |  是 |
| chinese_terms                | JSONB    |  否 |
| english_terms                | JSONB    |  否 |
| synonyms                     | JSONB    |  否 |
| object_terms                 | JSONB    |  否 |
| method_terms                 | JSONB    |  否 |
| boolean_query                | Text     |  否 |
| filters                      | JSONB    |  否 |
| limitations                  | JSONB    |  否 |
| source_model_invocation_id   | UUID     |  否 |
| status                       | Enum     |  是 |
| created_at                   | DateTime |  是 |

---

## 11.4 LiteratureSearchRun

记录一次真实数据源调用。

### 字段

| 字段             | 类型       | 必填 |
| -------------- | -------- | -: |
| id             | UUID     |  是 |
| project_id     | UUID     |  是 |
| query_plan_id  | UUID     |  是 |
| provider       | String   |  是 |
| provider_query | JSONB    |  是 |
| result_count   | Integer  |  是 |
| cache_hit      | Boolean  |  是 |
| fetched_at     | DateTime |  是 |
| status         | Enum     |  是 |
| error_code     | String   |  否 |
| job_id         | UUID     |  否 |

---

## 11.5 LiteratureExtraction

表示一次对文献的结构化抽取。

### 字段

| 字段                         | 类型       | 必填 |
| -------------------------- | -------- | -: |
| id                         | UUID     |  是 |
| project_id                 | UUID     |  是 |
| literature_record_id       | UUID     |  是 |
| document_id                | UUID     |  是 |
| extraction_version         | Integer  |  是 |
| schema_version             | String   |  是 |
| status                     | Enum     |  是 |
| overall_confidence         | Enum     |  否 |
| source_model_invocation_id | UUID     |  否 |
| processing_run_id          | UUID     |  否 |
| created_at                 | DateTime |  是 |
| confirmed_at               | DateTime |  否 |

### 状态

* `DRAFT`；
* `NEEDS_REVIEW`；
* `CONFIRMED`；
* `SUPERSEDED`；
* `INVALIDATED`。

---

## 11.6 LiteratureExtractionField

为便于逐字段证据和修正，P0 推荐独立字段表。

### 字段

| 字段                   | 类型       | 必填 |
| -------------------- | -------- | -: |
| id                   | UUID     |  是 |
| extraction_id        | UUID     |  是 |
| field_code           | Enum     |  是 |
| value_text           | Text     |  否 |
| value_json           | JSONB    |  否 |
| confidence           | Enum     |  否 |
| evidence_span_id     | UUID     |  否 |
| confirmation_status  | Enum     |  是 |
| corrected_by_user_id | UUID     |  否 |
| correction_reason    | Text     |  否 |
| created_at           | DateTime |  是 |
| updated_at           | DateTime |  是 |

### P0 field_code

```text
TITLE
AUTHORS
YEAR
RESEARCH_OBJECT
SAMPLE_SIZE
CORE_VARIABLES
RESEARCH_DESIGN
ANALYSIS_METHOD
MAIN_CONCLUSION
LIMITATION
```

---

## 11.7 EvidenceSpan

### 字段

| 字段                  | 类型       | 必填 |
| ------------------- | -------- | -: |
| id                  | UUID     |  是 |
| project_id          | UUID     |  是 |
| document_id         | UUID     |  是 |
| document_page_id    | UUID     |  否 |
| chunk_id            | UUID     |  否 |
| page_number         | Integer  |  是 |
| section_path        | JSONB    |  否 |
| source_text         | Text     |  是 |
| context_before      | Text     |  否 |
| context_after       | Text     |  否 |
| bounding_boxes      | JSONB    |  否 |
| char_start          | Integer  |  否 |
| char_end            | Integer  |  否 |
| evidence_type       | Enum     |  是 |
| confidence          | Enum     |  否 |
| parser_version      | String   |  否 |
| model_invocation_id | UUID     |  否 |
| source_text_hash    | String   |  是 |
| location_verification_status | Enum | 是 |
| review_status       | Enum     |  是 |
| parser_coverage     | Enum     |  否 |
| user_declared_read_scope | Enum | 否 |
| reviewed_by_actor_type | Enum  |  否 |
| reviewed_by_actor_id | UUID/String | 否 |
| reviewed_at         | DateTime |  否 |
| verified_by_actor_id | UUID/String | 否 |
| verified_at        | DateTime |  否 |
| created_at          | DateTime |  是 |
| invalidated_at      | DateTime |  否 |

### Evidence 类型

* `FIELD_SUPPORT`；
* `CLAIM_SUPPORT`；
* `CLAIM_CONTRADICTION`；
* `METHOD_DESCRIPTION`；
* `SAMPLE_DESCRIPTION`；
* `LIMITATION`；
* `OTHER`。

### 定位与阅读验证

`location_verification_status`：

* `EXTRACTED`；
* `LOCATED`；
* `VERIFIED`；
* `LOCATION_UNCERTAIN`；

`review_status` 表示用户是否已查看、确认、驳回或尚未复核证据。
`user_declared_read_scope`（原 `review_scope`）只记录用户声明的阅读范围：
`UNKNOWN`、`ABSTRACT`、`SECTIONS`、`FULL_TEXT_DECLARED`。系统不得从页码、
局部文本或一次确认自动推断为 `FULL_TEXT_DECLARED`。机器解析覆盖另以
`parser_coverage` 记录，不能代替用户阅读范围。

### 约束

* `source_text` 必须来自实际文档；
* 不允许模型凭空生成；
* 页码必须对应 DocumentPage；
* 原文定位失败时不得伪造坐标或创建 EvidenceSpan；应在
  `LiteratureExtractionField.evidence_status = NO_LOCATED_EVIDENCE` 保存原因和限制。
* `source_text_hash` 必须由保存的 `source_text` 计算；
* 缺少解析器、页码校验或侧车验证时不得升级为 `VERIFIED`。

---

## 11.8 LiteratureDecision

### 字段

| 字段                     | 类型       | 必填 |
| ---------------------- | -------- | -: |
| id                     | UUID     |  是 |
| project_id             | UUID     |  是 |
| literature_record_id   | UUID     |  是 |
| decision               | Enum     |  是 |
| reason_code            | Enum     |  否 |
| reason_text            | Text     |  否 |
| ai_recommendation      | Enum     |  否 |
| ai_score               | Float    |  否 |
| decided_by_user_id     | UUID     |  是 |
| supersedes_decision_id | UUID     |  否 |
| created_at             | DateTime |  是 |

### 规则

* 当前状态取最新有效决策；
* 历史决策不覆盖；
* AI 不得创建最终 LiteratureDecision；
* 撤销通过创建新决策。

---

# 12. 文献分析与选题模型

## 12.1 EvidenceSetSummary

P0 可作为结构化 JSON 存在于 ProcessingRun 结果中，也可建独立表。

建议字段：

* project_id；
* included_literature_ids；
* consensus_items；
* controversy_items；
* evidence_gaps；
* counterexamples；
* limitations；
* source_model_invocation_id；
* created_at。

每项结论必须关联 EvidenceSpan 或 LiteratureRecord。

---

## 12.2 TopicGenerationRun

### 字段

| 字段                           | 类型       | 必填 |
| ---------------------------- | -------- | -: |
| id                           | UUID     |  是 |
| project_id                   | UUID     |  是 |
| research_question_version_id | UUID     |  是 |
| evidence_summary_id          | UUID     |  否 |
| user_constraints             | JSONB    |  否 |
| source_model_invocation_id   | UUID     |  否 |
| status                       | Enum     |  是 |
| created_at                   | DateTime |  是 |

---

## 12.3 TopicCandidate

### 字段

| 字段                            | 类型       | 必填 |
| ----------------------------- | -------- | -: |
| id                            | UUID     |  是 |
| topic_generation_run_id       | UUID     |  是 |
| project_id                    | UUID     |  是 |
| candidate_order               | Integer  |  是 |
| question_text                 | Text     |  是 |
| research_object               | Text     |  否 |
| variables                     | JSONB    |  否 |
| research_goal                 | String   |  否 |
| literature_basis              | Text     |  否 |
| possible_innovation           | Text     |  否 |
| data_requirements             | JSONB    |  否 |
| recommended_method            | Text     |  否 |
| difficulty_level              | Enum     |  否 |
| data_availability             | Enum     |  否 |
| time_feasibility              | Enum     |  否 |
| ethical_risk                  | Enum     |  否 |
| major_risks                   | JSONB    |  否 |
| supervisor_confirmation_items | JSONB    |  否 |
| status                        | Enum     |  是 |
| created_at                    | DateTime |  是 |

### 状态

* `PROPOSED`；
* `SHORTLISTED`；
* `ADOPTED`；
* `REJECTED`；
* `EXPIRED`。

---

## 12.4 TopicCandidateEvidence

关联候选题与文献证据。

| 字段                   | 类型   | 必填 |
| -------------------- | ---- | -: |
| id                   | UUID |  是 |
| topic_candidate_id   | UUID |  是 |
| literature_record_id | UUID |  否 |
| evidence_span_id     | UUID |  否 |
| relation_type        | Enum |  是 |
| explanation          | Text |  否 |

---
