# FOUNDATION_AND_PROJECT_MODELS

- 所属入口文档：[DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- Migration status: COMPLETE

## 权威范围

User、ResearchProject、ProjectMember、Artifact、ArtifactRelation、ApprovalRecord、AuditLog、Job、ProcessingRun、实现来源元数据、PromptContract/PromptVersion 元数据和 DegradationRecord DTO 的完整模型定义。

## 不负责的内容

不定义文献、数据分析、论文、Agent 运行明细或跨对象状态转换；这些内容由相应子模型承载。

## 文档导航

- 返回 [DATA_MODEL_AND_WORKFLOW.md](../DATA_MODEL_AND_WORKFLOW.md)
- [FOUNDATION_AND_PROJECT_MODELS.md](FOUNDATION_AND_PROJECT_MODELS.md)
- [LITERATURE_AND_EVIDENCE_MODELS.md](LITERATURE_AND_EVIDENCE_MODELS.md)
- [DATA_ANALYSIS_AND_FIGURE_MODELS.md](DATA_ANALYSIS_AND_FIGURE_MODELS.md)
- [MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md](MANUSCRIPT_AGENT_AND_EXPORT_MODELS.md)
- [STATE_MACHINES_AND_INVARIANTS.md](STATE_MACHINES_AND_INVARIANTS.md)

以下正文由原入口文档对应对象或章节机械迁入；字段、枚举、约束、外键和语义保持不变。

# 7. 项目领域模型

## 7.1 User

用户对象沿用全栈 FastAPI 模板。

### 主要字段

| 字段              | 类型       | 必填 | 说明                    |
| --------------- | -------- | -: | --------------------- |
| id              | UUID     |  是 | 用户 ID                 |
| email           | String   |  是 | 登录邮箱                  |
| full_name       | String   |  否 | 姓名                    |
| hashed_password | String   |  是 | 密码哈希                  |
| is_active       | Boolean  |  是 | 是否启用                  |
| is_superuser    | Boolean  |  是 | 是否管理员                 |
| role            | Enum     |  是 | STUDENT、TEACHER、ADMIN |
| created_at      | DateTime |  是 | 创建时间                  |
| updated_at      | DateTime |  是 | 更新时间                  |

### 约束

* Email 唯一；
* 密码不得明文存储；
* 用户删除不应级联删除科研项目；
* 被停用用户不能发起新任务。

---

## 7.2 ResearchProject

科研项目是所有业务对象的统一容器。

### 主要字段

| 字段                                   | 类型          | 必填 | 说明                                     |
| ------------------------------------ | ----------- | -: | -------------------------------------- |
| id                                   | UUID        |  是 | 项目 ID                                  |
| owner_id                             | UUID        |  是 | 项目所有者                                  |
| name                                 | String(200) |  是 | 项目名称                                   |
| description                          | Text        |  否 | 项目说明                                   |
| discipline                           | String(100) |  否 | 学科                                     |
| research_direction                   | String(200) |  否 | 研究方向                                   |
| project_type                         | Enum        |  是 | THESIS、COURSE、INNOVATION、RESEARCH、DEMO |
| current_stage                        | Enum        |  是 | 当前科研阶段                                 |
| status                               | Enum        |  是 | ACTIVE、ARCHIVED、DELETED                |
| expected_completion_date             | Date        |  否 | 预计完成时间                                 |
| resource_constraints                 | JSONB       |  否 | 资源约束                                   |
| ethical_constraints                  | JSONB       |  否 | 伦理约束                                   |
| current_research_question_version_id | UUID        |  否 | 当前研究问题版本                               |
| lock_version                         | Integer     |  是 | 乐观锁                                    |
| created_at                           | DateTime    |  是 | 创建时间                                   |
| updated_at                           | DateTime    |  是 | 更新时间                                   |
| deleted_at                           | DateTime    |  否 | 软删除时间                                  |

### 项目阶段

```text
INTENT
LITERATURE
REVIEW
TOPIC
DATA
ANALYSIS
FIGURE
MANUSCRIPT
EVIDENCE
EXPORT
```

### 约束

* `name` 在同一用户下不要求唯一；
* `owner_id` 必须有对应 ProjectMember；
* 已归档项目默认只读；
* 被软删除项目不允许发起任务。

---

## 7.3 ProjectMember

### 主要字段

| 字段          | 类型       | 必填 | 说明                           |
| ----------- | -------- | -: | ---------------------------- |
| id          | UUID     |  是 | 成员关系 ID                      |
| project_id  | UUID     |  是 | 项目                           |
| user_id     | UUID     |  是 | 用户                           |
| role        | Enum     |  是 | OWNER、EDITOR、REVIEWER、VIEWER |
| permissions | JSONB    |  否 | 细粒度扩展权限                      |
| invited_by  | UUID     |  否 | 邀请人                          |
| joined_at   | DateTime |  是 | 加入时间                         |
| removed_at  | DateTime |  否 | 移除时间                         |

### 约束

```text
UNIQUE(project_id, user_id)
```

项目必须至少有一个 OWNER。

---

## 7.4 AuditLog

AuditLog 记录业务操作，不等同于系统日志。

### 主要字段

| 字段              | 类型          | 必填 | 说明                       |
| --------------- | ----------- | -: | ------------------------ |
| id              | UUID        |  是 | 审计 ID                    |
| project_id      | UUID        |  否 | 项目                       |
| actor_type      | Enum        |  是 | USER、AGENT、SYSTEM、WORKER |
| actor_id        | UUID/String |  否 | 操作者                      |
| action          | String      |  是 | 操作代码                     |
| object_type     | String      |  是 | 对象类型                     |
| object_id       | UUID        |  否 | 对象 ID                    |
| before_snapshot | JSONB       |  否 | 修改前摘要                    |
| after_snapshot  | JSONB       |  否 | 修改后摘要                    |
| reason          | Text        |  否 | 原因                       |
| request_id      | UUID        |  否 | 请求 ID                    |
| job_id          | UUID        |  否 | 任务 ID                    |
| created_at      | DateTime    |  是 | 时间                       |

### 约束

* 追加写；
* 不允许普通用户修改；
* 不保存完整敏感文件内容；
* 快照只保存必要字段。

---

# 9. Artifact 与文件模型

## 9.1 Artifact

Artifact 是所有文件和系统产物的统一模型。

### Artifact 类型

```text
PDF_DOCUMENT
DATASET_FILE
MANUSCRIPT_DOCX
FIGURE_PNG
FIGURE_SVG
FIGURE_PDF
ANALYSIS_CODE
ANALYSIS_LOG
JSON_RESULT
CSV_EXPORT
XLSX_EXPORT
REPRO_PACKAGE
MANIFEST
MODEL_OUTPUT
OTHER
```

### 字段

| 字段                 | 类型         | 必填 | 说明                                             |
| ------------------ | ---------- | -: | ---------------------------------------------- |
| id                 | UUID       |  是 | Artifact ID                                    |
| project_id         | UUID       |  是 | 项目                                             |
| artifact_type      | Enum       |  是 | 类型                                             |
| filename           | String     |  是 | 显示文件名                                          |
| original_filename  | String     |  否 | 原文件名                                           |
| storage_provider   | Enum       |  是 | MINIO、S3、LOCAL                                 |
| storage_key        | String     |  是 | 对象存储键                                          |
| mime_type          | String     |  是 | MIME                                           |
| size_bytes         | BigInteger |  是 | 大小                                             |
| sha256             | String(64) |  是 | 文件哈希                                           |
| source_artifact_id | UUID       |  否 | 直接上游文件                                         |
| is_original        | Boolean    |  是 | 是否原始文件                                         |
| is_immutable       | Boolean    |  是 | 是否不可变                                          |
| status             | Enum       |  是 | UPLOADING、AVAILABLE、FAILED、DELETED、QUARANTINED |
| metadata           | JSONB      |  否 | 扩展元数据                                          |
| created_by         | UUID       |  否 | 创建用户                                           |
| created_at         | DateTime   |  是 | 创建时间                                           |
| deleted_at         | DateTime   |  否 | 删除时间                                           |

### 约束

* `storage_key` 唯一；
* 原始 Artifact 必须 `is_immutable=true`；
* 已完成 Artifact 不允许修改存储内容；
* 内容变化必须创建新 Artifact；
* 同项目、同 SHA-256 可复用文件内容，但业务关系独立。

---

## 9.2 ArtifactRelation

用于表示复杂文件来源。

### 关系类型

* `DERIVED_FROM`；
* `GENERATED_FROM`；
* `PACKAGED_IN`；
* `PREVIEW_OF`；
* `REPLACEMENT_OF`；
* `CODE_FOR`；
* `LOG_FOR`。

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| project_id         | UUID     |  是 |
| source_artifact_id | UUID     |  是 |
| target_artifact_id | UUID     |  是 |
| relation_type      | Enum     |  是 |
| metadata           | JSONB    |  否 |
| created_at         | DateTime |  是 |

---

# 20. 人工确认模型

操作审批采用规范性风险分类：`NONE`、`LIGHT_CONFIRMATION`、`FORMAL_APPROVAL`。前两类不要求创建 `ApprovalRecord`：只读、扫描、候选生成和预览通常为 `NONE`，低风险采用或格式修正通常为 `LIGHT_CONFIRMATION`。只有修改科研数据、正式结果、版本关系或不可逆输出的高风险操作使用 `FORMAL_APPROVAL` 并创建下述记录。

这三个名称是政策分类，不是本文件新增的数据库 Enum 或字段；现有实现可通过 `requires_approval`、普通确认记录与 `ApprovalRecord` 表达。

## 20.1 ApprovalRecord

ApprovalRecord 是高风险正式科研决策记录，不用于记录每次读取、模型调用或低风险 ToolCall。

### approval_type

* `RESEARCH_QUESTION_CONFIRMATION`；
* `LITERATURE_DECISION_CONFIRMATION`；
* `LITERATURE_EXTRACTION_CONFIRMATION`；
* `CLEANING_PLAN_APPROVAL`；
* `VARIABLE_ROLE_CONFIRMATION`；
* `ANALYSIS_PLAN_APPROVAL`；
* `FIGURE_CONFIRMATION`；
* `MANUSCRIPT_FIX_APPROVAL`；
* `CLAIM_CONFIRMATION`；
* `EXPORT_CONFIRMATION`。

### 字段

| 字段                      | 类型          | 必填 |
| ----------------------- | ----------- | -: |
| id                      | UUID        |  是 |
| project_id              | UUID        |  是 |
| approval_type           | Enum        |  是 |
| target_object_type      | String      |  是 |
| target_object_id        | UUID        |  是 |
| requested_by_actor_type | Enum        |  是 |
| requested_by_actor_id   | UUID/String |  否 |
| requested_at            | DateTime    |  是 |
| status                  | Enum        |  是 |
| decision_by_user_id     | UUID        |  否 |
| decision_at             | DateTime    |  否 |
| decision_reason         | Text        |  否 |
| payload_snapshot        | JSONB       |  是 |
| impact_summary          | JSONB       |  否 |
| expires_at              | DateTime    |  否 |
| supersedes_approval_id  | UUID        |  否 |
| created_at              | DateTime    |  是 |

### 状态

* `PENDING`；
* `APPROVED`；
* `REJECTED`；
* `CANCELLED`；
* `EXPIRED`；
* `SUPERSEDED`。

### 规则

* Agent 不能批准；
* Worker 不能批准；
* 审批内容必须保存快照；
* 目标对象变化后旧审批应失效或 superseded；
* 审批通过不等于执行完成。

---

## 20.2 ApprovalItem

用于一个审批中包含多个项目，例如多个 CleaningPlanAction。

字段：

* approval_record_id；
* item_type；
* item_id；
* decision；
* reason。

P0 可根据实现复杂度放入 `payload_snapshot`，但必须保留逐项决定能力。

---

# 21. 异步任务与运行模型

## 21.1 Job

Job 表示调度层任务。

### 字段

| 字段                   | 类型       | 必填 |
| -------------------- | -------- | -: |
| id                   | UUID     |  是 |
| project_id           | UUID     |  是 |
| task_type            | Enum     |  是 |
| resource_type        | String   |  是 |
| resource_id          | UUID     |  是 |
| status               | Enum     |  是 |
| idempotency_key      | String   |  是 |
| progress_percent     | Integer  |  是 |
| current_step         | String   |  否 |
| total_steps          | Integer  |  否 |
| completed_steps      | Integer  |  否 |
| retry_count          | Integer  |  是 |
| max_retries          | Integer  |  是 |
| celery_task_id       | String   |  否 |
| requested_by_user_id | UUID     |  否 |
| created_at           | DateTime |  是 |
| queued_at            | DateTime |  否 |
| started_at           | DateTime |  否 |
| completed_at         | DateTime |  否 |
| last_heartbeat_at    | DateTime |  否 |
| error_code           | String   |  否 |
| error_message        | Text     |  否 |
| retryable            | Boolean  |  否 |

### 状态

* `DRAFT`；
* `QUEUED`；
* `RUNNING`；
* `NEEDS_REVIEW`；
* `COMPLETED`；
* `FAILED`；
* `CANCEL_REQUESTED`；
* `CANCELLED`；
* `DISPATCH_FAILED`。

---

## 21.2 ProcessingRun

ProcessingRun 表示一次具体业务处理。

### 示例

* PDF 解析；
* 文献字段抽取；
* 数据质量检查；
* 图表渲染；
* DOCX 检查；
* 复现包打包。

### 字段

| 字段                 | 类型       | 必填 |
| ------------------ | -------- | -: |
| id                 | UUID     |  是 |
| project_id         | UUID     |  是 |
| job_id             | UUID     |  是 |
| process_type       | Enum     |  是 |
| input_object_type  | String   |  是 |
| input_object_id    | UUID     |  是 |
| input_hash         | String   |  否 |
| parameters         | JSONB    |  否 |
| parameters_hash    | String   |  是 |
| engine             | String   |  是 |
| engine_version     | String   |  否 |
| implementation_metadata | JSONB | 否 |
| status             | Enum     |  是 |
| output_object_type | String   |  否 |
| output_object_id   | UUID     |  否 |
| log_artifact_id    | UUID     |  否 |
| started_at         | DateTime |  否 |
| completed_at       | DateTime |  否 |

### 区别

Job 关心队列和进度。

ProcessingRun 关心业务输入、引擎和输出。

### implementation_metadata

这是阶段 9 唯一建议增加的持久化兼容字段，用于保存与业务参数不同的执行来源
信息。它是严格、可版本化的 JSONB，不是自由字典：

```text
metadata_schema_version
engine_name
engine_version
upstream_project
upstream_commit
adopted_release_or_digest
configuration_hash
ruleset_version
prompt_version
schema_version
integration_mode
```

规则：

* `engine_name` 必须与 `ProcessingRun.engine` 一致；
* `engine_version` 不得与物理字段冲突；
* `configuration_hash` 通常等于或可由 `parameters_hash`、规则配置与资源哈希重建；
* 未使用 Vendor、Prompt 或规则集时，对应字段为 `null`，不得伪造 Commit；
* ToolCall 和 AgentRun 通过关联 ProcessingRun、ModelInvocation 或输出 Artifact 获取该信息，不重复建立第三方运行表；
* 对外 DTO 默认不暴露许可证路径、内部镜像地址或敏感配置。

---

# 22. Agent 与模型运行模型：治理元数据

## 22.4 PromptContract 与 PromptVersion

P0 唯一方案是代码注册表/manifest：`backend/app/agents/prompts/prompt-manifest.yaml` 与同目录受 Git 管理的 Prompt 资产。它不是数据库可编辑对象；普通用户和 Agent 均不能修改系统 Prompt。每个可执行模型任务必须由正式契约描述：

| 字段 | 说明 |
|---|---|
| prompt_id | 稳定且唯一的 Prompt 标识 |
| prompt_version | 语义版本 |
| task_type | 允许的模型任务 |
| input_schema | 输入 Schema 名称与版本 |
| output_schema | 输出 Schema 名称与版本 |
| allowed_tools | 可请求的 Tool 名称与版本 |
| required_source_types | 必须提供的来源对象类型 |
| max_tool_calls | 最大工具调用次数 |
| failure_behavior | Schema、来源或权限失败后的可控结果 |
| requested_data_access_level | 最低必要数据访问等级 |
| max_allowed_data_access_level | 工具/策略允许的上限 |
| status | `DRAFT`、`ACTIVE`、`RETIRED` |
| content_hash | 固定 Prompt 内容哈希 |

`ModelInvocation` 必须保存 `prompt_id`、`prompt_version`、`prompt_content_hash`、输入/输出 Schema 版本与实际 `effective_data_access_level`。更新
Prompt 必须创建新版本，不能静默覆盖。

## 22.6 DegradationRecord DTO

P0 先将 `DegradationRecord` 作为绑定 `ProcessingRun`、`ToolCall`、
`ModelInvocation` 或 `AuditLog` 的严格 DTO，而不是新增核心表：

```text
requested_capability
primary_provider
fallback_provider
reason_code
impact
result_status
user_visible_message
```

它记录回退事实和影响；不得把 `UNAVAILABLE`、缓存或低定位可信度伪装为
正常成功。只有跨模块查询和统计成为明确需求时才升级为独立表。

---
