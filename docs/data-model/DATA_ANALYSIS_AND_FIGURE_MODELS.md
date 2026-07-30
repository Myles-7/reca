# DATA_ANALYSIS_AND_FIGURE_MODELS

- 所属入口文档：[DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

Dataset、DatasetVersion、DatasetColumn、数据质量、CleaningPlan、DataTransformation、AnalysisPlan/Run/Result 和 Figure 相关对象的完整模型定义。

## 不负责的内容

不定义论文、Agent、导出或跨领域状态转换；正式统计数字仍只能来自确定性程序。

## 文档导航

- 返回 [DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- [FOUNDATION_AND_PROJECT_MODELS.md](FOUNDATION_AND_PROJECT_MODELS.md)
- [LITERATURE_AND_EVIDENCE_MODELS.md](LITERATURE_AND_EVIDENCE_MODELS.md)
- [DATA_ANALYSIS_AND_FIGURE_MODELS.md](DATA_ANALYSIS_AND_FIGURE_MODELS.md)
- [MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md](MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md)
- [STATE_MACHINES_AND_INVARIANTS.md](STATE_MACHINES_AND_INVARIANTS.md)

以下正文由原入口文档对应对象或章节机械迁入；字段、枚举、约束、外键和语义保持不变。

# 13. 数据领域模型

## 13.1 Dataset

逻辑数据集。

### 字段

| 字段                   | 类型       | 必填 |
| -------------------- | -------- | -: |
| id                   | UUID     |  是 |
| project_id           | UUID     |  是 |
| name                 | String   |  是 |
| description          | Text     |  否 |
| source_type          | Enum     |  是 |
| publisher            | String   |  否 |
| source_platform      | String   |  否 |
| source_identifier    | String   |  否 |
| doi                  | String   |  否 |
| acquired_at          | Date     |  否 |
| license_name         | String   |  否 |
| license_status       | Enum     |  是 |
| recommended_citation | Text     |  否 |
| known_limitations    | JSONB    |  否 |
| current_version_id   | UUID     |  否 |
| status               | Enum     |  是 |
| created_by           | UUID     |  是 |
| created_at           | DateTime |  是 |
| updated_at           | DateTime |  是 |

### source_type

* `USER_UPLOAD`；
* `PUBLIC_DATASET`；
* `DEMO_DATASET`；
* `MANUAL_ENTRY`。

### license_status

* `VERIFIED`；
* `DECLARED_BY_USER`；
* `UNKNOWN`；
* `RESTRICTED`。

---

## 13.2 DatasetVersion

不可变数据版本。

### 字段

| 字段                  | 类型       | 必填 |
| ------------------- | -------- | -: |
| id                  | UUID     |  是 |
| project_id          | UUID     |  是 |
| dataset_id          | UUID     |  是 |
| version_number      | Integer  |  是 |
| parent_version_id   | UUID     |  否 |
| artifact_id         | UUID     |  是 |
| version_type        | Enum     |  是 |
| row_count           | Integer  |  否 |
| column_count        | Integer  |  否 |
| file_format         | Enum     |  是 |
| schema_hash         | String   |  否 |
| data_hash           | String   |  是 |
| transformation_id   | UUID     |  否 |
| status              | Enum     |  是 |
| created_by          | UUID     |  否 |
| created_at          | DateTime |  是 |
| invalidated_at      | DateTime |  否 |
| invalidation_reason | Text     |  否 |

### version_type

* `ORIGINAL`；
* `CLEANED`；
* `FILTERED`；
* `TRANSFORMED`；
* `DERIVED`。

### 状态

* `CREATING`；
* `AVAILABLE`；
* `FAILED`；
* `INVALIDATED`；
* `DELETED`。

### 约束

```text
UNIQUE(dataset_id, version_number)
```

`ORIGINAL` 版本：

* `parent_version_id` 为空；
* `transformation_id` 为空；
* 永久只读。

---

## 13.3 DatasetColumn

### 字段

| 字段                  | 类型       | 必填 |
| ------------------- | -------- | -: |
| id                  | UUID     |  是 |
| dataset_version_id  | UUID     |  是 |
| project_id          | UUID     |  是 |
| source_name         | String   |  是 |
| display_name        | String   |  否 |
| column_order        | Integer  |  是 |
| inferred_type       | Enum     |  是 |
| confirmed_type      | Enum     |  否 |
| semantic_role       | Enum     |  否 |
| unit                | String   |  否 |
| description         | Text     |  否 |
| missing_codes       | JSONB    |  否 |
| category_mapping    | JSONB    |  否 |
| is_identifier       | Boolean  |  是 |
| is_sensitive        | Boolean  |  是 |
| confirmation_status | Enum     |  是 |
| created_at          | DateTime |  是 |

### semantic_role

* `ID`；
* `INDEPENDENT_VARIABLE`；
* `DEPENDENT_VARIABLE`；
* `CONTROL_VARIABLE`；
* `GROUP_VARIABLE`；
* `TIME_VARIABLE`；
* `WEIGHT`；
* `UNASSIGNED`。

### 规则

用户确认的变量角色只对特定 DatasetVersion 有效。

新版本创建时可继承，但必须记录来源。

---

# 14. 数据质量模型

## 14.1 DataQualityRun

表示一次数据质量检查。

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| project_id         | UUID     |  是 |
| dataset_version_id | UUID     |  是 |
| rule_set_version   | String   |  是 |
| status             | Enum     |  是 |
| issue_count        | Integer  |  否 |
| high_issue_count   | Integer  |  否 |
| started_at         | DateTime |  否 |
| completed_at       | DateTime |  否 |
| processing_run_id  | UUID     |  否 |
| created_at         | DateTime |  是 |

---

## 14.2 DataQualityIssue

### 字段

| 字段                  | 类型       | 必填 |
| ------------------- | -------- | -: |
| id                  | UUID     |  是 |
| project_id          | UUID     |  是 |
| data_quality_run_id | UUID     |  是 |
| dataset_version_id  | UUID     |  是 |
| issue_type          | Enum     |  是 |
| severity            | Enum     |  是 |
| column_id           | UUID     |  否 |
| affected_row_count  | Integer  |  否 |
| affected_rows       | JSONB    |  否 |
| evidence            | JSONB    |  是 |
| description         | Text     |  是 |
| suggested_actions   | JSONB    |  否 |
| requires_approval   | Boolean  |  是 |
| status              | Enum     |  是 |
| created_at          | DateTime |  是 |
| resolved_at         | DateTime |  否 |

### issue_type

* `MISSING_VALUE`；
* `DUPLICATE_ROW`；
* `DUPLICATE_ID`；
* `CONSTANT_COLUMN`；
* `MIXED_TYPE`；
* `CATEGORY_INCONSISTENCY`；
* `OUT_OF_RANGE`；
* `EXTREME_VALUE`；
* `GROUP_IMBALANCE`；
* `SUSPICIOUS_UNIT`；
* `INVALID_DATE`；
* `POSSIBLE_SENSITIVE_FIELD`。

### 状态

* `OPEN`；
* `ACKNOWLEDGED`；
* `PLANNED`；
* `RESOLVED`；
* `IGNORED`；
* `INVALIDATED`。

---

# 15. 数据处理模型

## 15.1 CleaningPlan

表示待批准的数据处理方案。

### 字段

| 字段                         | 类型       | 必填 |
| -------------------------- | -------- | -: |
| id                         | UUID     |  是 |
| project_id                 | UUID     |  是 |
| dataset_version_id         | UUID     |  是 |
| title                      | String   |  是 |
| rationale                  | Text     |  否 |
| status                     | Enum     |  是 |
| preview_summary            | JSONB    |  否 |
| affected_row_count         | Integer  |  否 |
| affected_column_count      | Integer  |  否 |
| source_model_invocation_id | UUID     |  否 |
| approval_record_id         | UUID     |  否 |
| created_by                 | UUID     |  否 |
| created_at                 | DateTime |  是 |
| updated_at                 | DateTime |  是 |

### 状态

* `DRAFT`；
* `VALIDATING`；
* `NEEDS_INPUT`；
* `READY`；
* `NEEDS_APPROVAL`；
* `APPROVED`；
* `REJECTED`；
* `QUEUED`；
* `RUNNING`；
* `COMPLETED`；
* `FAILED`；
* `CANCELLED`；
* `INVALIDATED`。

---

## 15.2 CleaningPlanAction

### action_type

* `KEEP_ROWS`；
* `DROP_ROWS`；
* `REPLACE_VALUE`；
* `MAP_CATEGORY`；
* `CAST_TYPE`；
* `MARK_MISSING`；
* `IMPUTE_VALUE`；
* `CONVERT_UNIT`；
* `RENAME_COLUMN`；
* `CREATE_DERIVED_COLUMN`。

P0 中 `CREATE_DERIVED_COLUMN` 应受严格限制。

### 字段

| 字段               | 类型      | 必填 |
| ---------------- | ------- | -: |
| id               | UUID    |  是 |
| cleaning_plan_id | UUID    |  是 |
| action_order     | Integer |  是 |
| action_type      | Enum    |  是 |
| target_columns   | JSONB   |  否 |
| row_selector     | JSONB   |  否 |
| parameters       | JSONB   |  是 |
| reason           | Text    |  是 |
| source_issue_ids | JSONB   |  否 |
| preview_before   | JSONB   |  否 |
| preview_after    | JSONB   |  否 |
| risk_level       | Enum    |  是 |

### 禁止

* 保存任意 Python 代码；
* 保存任意 SQL；
* 保存任意 Shell；
* 使用无法审计的表达式。

---

## 15.3 DataTransformation

实际执行记录。

### 字段

| 字段                        | 类型       | 必填 |
| ------------------------- | -------- | -: |
| id                        | UUID     |  是 |
| project_id                | UUID     |  是 |
| cleaning_plan_id          | UUID     |  是 |
| source_dataset_version_id | UUID     |  是 |
| target_dataset_version_id | UUID     |  否 |
| status                    | Enum     |  是 |
| action_count              | Integer  |  是 |
| affected_row_count        | Integer  |  否 |
| affected_column_count     | Integer  |  否 |
| parameters_hash           | String   |  是 |
| code_artifact_id          | UUID     |  否 |
| log_artifact_id           | UUID     |  否 |
| processing_run_id         | UUID     |  否 |
| started_at                | DateTime |  否 |
| completed_at              | DateTime |  否 |
| error_code                | String   |  否 |

### 规则

* 只有 Approved CleaningPlan 可创建；
* 成功后创建 Target DatasetVersion；
* 失败时 Target 版本不得进入 AVAILABLE；
* 重复执行相同幂等键不得重复创建正式版本。

---

# 16. 分析领域模型

## 16.1 AnalysisPlan

### 字段

| 字段                           | 类型       | 必填 |
| ---------------------------- | -------- | -: |
| id                           | UUID     |  是 |
| project_id                   | UUID     |  是 |
| research_question_version_id | UUID     |  是 |
| dataset_version_id           | UUID     |  是 |
| analysis_goal                | Enum     |  是 |
| method                       | Enum     |  是 |
| dependent_variable_ids       | JSONB    |  否 |
| independent_variable_ids     | JSONB    |  否 |
| control_variable_ids         | JSONB    |  否 |
| group_variable_id            | UUID     |  否 |
| pair_identifier_column_id    | UUID     |  否 |
| missing_data_policy          | JSONB    |  是 |
| sample_filter                | JSONB    |  否 |
| parameters                   | JSONB    |  否 |
| assumption_summary           | JSONB    |  否 |
| warnings                     | JSONB    |  否 |
| limitations                  | JSONB    |  否 |
| status                       | Enum     |  是 |
| approval_record_id           | UUID     |  否 |
| source_model_invocation_id   | UUID     |  否 |
| created_by                   | UUID     |  否 |
| created_at                   | DateTime |  是 |
| updated_at                   | DateTime |  是 |

### analysis_goal

* `DESCRIPTIVE`；
* `GROUP_COMPARISON`；
* `CORRELATION`；
* `SIMPLE_PREDICTION`。

### method

* `DESCRIPTIVE_STATISTICS`；
* `INDEPENDENT_TWO_GROUP`；
* `PAIRED_TWO_GROUP`；
* `PEARSON_CORRELATION`；
* `SPEARMAN_CORRELATION`；
* `SIMPLE_LINEAR_REGRESSION`。

---

## 16.2 AnalysisAssumptionCheck

### 字段

| 字段               | 类型       | 必填 |
| ---------------- | -------- | -: |
| id               | UUID     |  是 |
| analysis_plan_id | UUID     |  是 |
| check_code       | Enum     |  是 |
| status           | Enum     |  是 |
| observed_value   | JSONB    |  否 |
| threshold        | JSONB    |  否 |
| explanation      | Text     |  否 |
| warning_level    | Enum     |  否 |
| created_at       | DateTime |  是 |

### check_code

* `DATA_TYPE`；
* `SAMPLE_SIZE`；
* `INDEPENDENCE`；
* `NORMALITY`；
* `VARIANCE_HOMOGENEITY`；
* `LINEARITY`；
* `OUTLIER_INFLUENCE`；
* `PAIRING_VALIDITY`；
* `MISSINGNESS`。

### status

* `PASSED`；
* `FAILED`；
* `WARNING`；
* `NOT_APPLICABLE`；
* `REQUIRES_USER_CONFIRMATION`；
* `UNKNOWN`。

---

## 16.3 AnalysisRun

一次确定性执行。

### 字段

| 字段                   | 类型       | 必填 |
| -------------------- | -------- | -: |
| id                   | UUID     |  是 |
| project_id           | UUID     |  是 |
| analysis_plan_id     | UUID     |  是 |
| dataset_version_id   | UUID     |  是 |
| run_number           | Integer  |  是 |
| status               | Enum     |  是 |
| idempotency_key      | String   |  是 |
| statistical_engine   | String   |  是 |
| engine_version       | String   |  是 |
| python_version       | String   |  否 |
| environment_snapshot | JSONB    |  否 |
| code_artifact_id     | UUID     |  否 |
| log_artifact_id      | UUID     |  否 |
| processing_run_id    | UUID     |  否 |
| started_at           | DateTime |  否 |
| completed_at         | DateTime |  否 |
| invalidated_at       | DateTime |  否 |
| invalidation_reason  | Text     |  否 |
| error_code           | String   |  否 |
| error_message        | Text     |  否 |

### 状态

* `QUEUED`；
* `RUNNING`；
* `COMPLETED`；
* `FAILED`；
* `CANCEL_REQUESTED`；
* `CANCELLED`；
* `INVALIDATED`。

### 约束

* 完成后不可修改结果；
* 重新运行创建新 AnalysisRun；
* 失效不删除。

---

## 16.4 AnalysisResult

### 字段

| 字段                         | 类型       | 必填 |
| -------------------------- | -------- | -: |
| id                         | UUID     |  是 |
| project_id                 | UUID     |  是 |
| analysis_run_id            | UUID     |  是 |
| result_type                | Enum     |  是 |
| method                     | Enum     |  是 |
| variables                  | JSONB    |  是 |
| sample_size                | Integer  |  是 |
| statistics                 | JSONB    |  是 |
| confidence_intervals       | JSONB    |  否 |
| effect_information         | JSONB    |  否 |
| assumption_results         | JSONB    |  否 |
| warnings                   | JSONB    |  否 |
| interpretation_constraints | JSONB    |  否 |
| schema_version             | String   |  是 |
| created_at                 | DateTime |  是 |

### 约束

* 一次 AnalysisRun 可有一个主结果和多个子结果；
* 结果数字来自统计引擎；
* 模型不能更新 `statistics`；
* 前端不得通过文本解析获取正式数字。

---

## 16.5 CodeArtifact

CodeArtifact 可直接复用 Artifact，并增加业务关系。

建议字段：

* artifact_id；
* code_type；
* template_version；
* language；
* execution_entry；
* dependency_snapshot；
* input_hash；
* output_hash。

代码是系统生成的受控代码，不接受用户任意代码。

---

# 17. 图表领域模型

## 17.1 FigurePlan

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| project_id         | UUID     |  是 |
| dataset_version_id | UUID     |  是 |
| analysis_run_id    | UUID     |  否 |
| chart_type         | Enum     |  是 |
| x_column_id        | UUID     |  否 |
| y_column_id        | UUID     |  否 |
| group_column_id    | UUID     |  否 |
| parameters         | JSONB    |  是 |
| caption_draft      | Text     |  否 |
| status             | Enum     |  是 |
| approval_record_id | UUID     |  否 |
| created_at         | DateTime |  是 |

### chart_type

* `HISTOGRAM`；
* `BOXPLOT`；
* `SCATTER`；
* `GROUP_COMPARISON`；
* `CORRELATION_MATRIX`。

---

## 17.2 Figure

P0 推荐将 Figure 记录视为不可变产物。

参数修改后创建新 Figure。

### 字段

| 字段                  | 类型       | 必填 |
| ------------------- | -------- | -: |
| id                  | UUID     |  是 |
| project_id          | UUID     |  是 |
| figure_plan_id      | UUID     |  是 |
| dataset_version_id  | UUID     |  是 |
| analysis_run_id     | UUID     |  否 |
| chart_type          | Enum     |  是 |
| image_artifact_id   | UUID     |  是 |
| svg_artifact_id     | UUID     |  否 |
| pdf_artifact_id     | UUID     |  否 |
| code_artifact_id    | UUID     |  是 |
| caption             | Text     |  是 |
| parameters          | JSONB    |  是 |
| status              | Enum     |  是 |
| created_at          | DateTime |  是 |
| invalidated_at      | DateTime |  否 |
| invalidation_reason | Text     |  否 |

### 状态

* `DRAFT`；
* `READY`；
* `CONFIRMED`；
* `INVALIDATED`；
* `ARCHIVED`。

---

## 17.3 FigureValidationIssue

### issue_type

* `MISSING_AXIS_LABEL`；
* `MISSING_UNIT`；
* `MISSING_LEGEND`；
* `MISSING_CAPTION`；
* `UNDEFINED_ERROR_BAR`；
* `MISLEADING_AXIS_RANGE`；
* `LOW_RESOLUTION`；
* `VERSION_MISMATCH`；
* `RESULT_MISMATCH`。

### 字段

| 字段         | 类型       | 必填 |
| ---------- | -------- | -: |
| id         | UUID     |  是 |
| figure_id  | UUID     |  是 |
| issue_type | Enum     |  是 |
| severity   | Enum     |  是 |
| evidence   | JSONB    |  否 |
| suggestion | Text     |  否 |
| status     | Enum     |  是 |
| created_at | DateTime |  是 |

---
