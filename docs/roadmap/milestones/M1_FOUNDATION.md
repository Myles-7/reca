# M1_FOUNDATION

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：APPROVED FOR M1 COMPLETION
- 当前增量状态：LOCAL EXIT GATE PASS；REMOTE BASELINE FINALIZATION AUTHORIZED
- Migration status: COMPLETE
- Milestone ID: M1

## 权威范围

本文件是 M1 目标、依赖、范围、交付、测试、安全、门禁、阻塞和降级要求的详细路线图。产品范围、字段、API 契约和测试指标仍由对应权威文档定义。

## 不负责的内容

本文件不改变 M1–M9 顺序，不新增 P0，不把 P1 升级，不降低 Competition Core，也不覆盖其他里程碑或公共交付规则。

## 文档导航

- 返回 [IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- [DELIVERY_WORKFLOW.md](../DELIVERY_WORKFLOW.md)
- [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md)
- [M0 Regression Baseline](../../testing/M0_REGRESSION_BASELINE.md)

## 开源复用与安全分层

本里程碑允许选择成熟开源实现，不要求先自行重写或预建复杂 Adapter。依赖、服务、Fork、Vendor、Submodule 或选择性复制必须在同一 PR 完成许可证核验、上游 Commit/Tag、归属和修改记录；无许可证或来源不明内容不得复制。企业生产强化不阻塞 Competition Core，Competition Edition 最小护栏仍必须满足。实际复制 ARS-Codex 内容需要单独记录许可证、归属和架构决定，且不提前 M8 或改变单总控 Agent 边界。

### M1 开源接入步骤

- `Research`：建立来源登记、Vendor/选择性复制规则、implementation metadata 约定和 ARS 资产到 RECA 对象/里程碑的映射草案。
- `Spike`：验证 Prompt manifest、来源/修改台账和实际集成 PR 模板能记录固定 Commit、许可证、配置哈希与回退。
- `Decision`：采用 ADR-002/ADR-008 的模式和元数据边界；ARS 仍按 ADR-001 条件式复用。
- `Integration`：只建设 M1 Prompt manifest 和治理底座；不复制 ARS 内容，不接入正式 Agent，不提前 M8。

## 里程碑契约覆盖索引

| 必需内容 | 本文件权威位置 |
| --- | --- |
| 目标 | 9.1 |
| 前置依赖 | 9.2 |
| Competition Core | 9.3 中属于 P0-Must / Competition Core 的条目；不得重新分类 |
| P0-Full | 9.3 中明确标为 P0-Full 的条目；未标记者以 PRD 为准 |
| 明确不做 | 9.4 |
| 数据模型 | 9.5 / 9.7 |
| API | 9.8 |
| 前端 | 9.6 |
| 测试 | 9.10 |
| 安全 | 9.11 |
| Prompt / AI | 9.3 / 9.9；无模型任务时不得擅自新增 |
| Codex 推荐任务顺序 | 9.16 |
| 可并行任务 | 9.14 |
| Entry Gate | 9.2 + 公共 Entry Gate |
| Exit Gate | 9.13 + 公共 Exit Gate |
| 阻塞问题 | 9.15 |
| 风险与降级 | 本里程碑原章节 + [RISK_SCOPE_AND_RELEASE.md](../RISK_SCOPE_AND_RELEASE.md) |

M0 Regression Baseline 适用于本里程碑，任何交付不得使 M0 已验收能力退化。以下正文由原路线图对应章节机械迁入，原顺序、依赖和语义不变。

<a id="milestone-m1"></a>

# 9. M1：基础领域能力

## 9.1 目标

建立所有科研业务模块共享的基础领域对象和基础服务。

## 9.2 前置依赖

M0 已完成。M1 必须从最新 `main` 创建专用分支，不继续使用 `codex/m0-continuous`；不得降低 M0 required CI 或 clean-room 基线。

## 9.3 本阶段范围

首次模型调用前必须完成最小 AI 治理底座：在 `backend/app/agents/prompts/prompt-manifest.yaml` 建立 Git 管理的 Prompt manifest/registry，并记录 `prompt_id`、`prompt_version`、`prompt_content_hash`、输入/输出 Schema 版本、ModelInvocation 审计结构、requested/max/effective 数据访问策略，以及 Mock/Recorded 模型测试模式。此项不接入 Agent；其目的仅是让 M2/M3 的模型任务可审计、可测且最小化数据发送。

核心对象：

```text
User
ResearchProject
ProjectMember
Artifact
ArtifactRelation
ApprovalRecord
AuditLog
Job
ProcessingRun
ModelInvocation
```

基础能力：

* 用户认证；
* 项目权限；
* 项目隔离；
* 文件上传；
* 文件哈希；
* 对象存储；
* 审批记录；
* 异步任务；
* 审计；
* 幂等；
* 乐观锁；
* SSE 或基础轮询。

## 9.3A M1 Contract Freeze Decision Matrix

本节是批准基线后的增量契约修订，已由 Project Owner 于 2026-07-31 批准。批准允许在新的 Contract Freeze baseline 记录后开始 M1 production implementation；不表示 M1 已实现或已验收，且不得移动 `docs-m1-approved`、`open-design-integration-approved` 历史 tag。

| Issue | Requirement | Domain need | Frontend need | Classification | Contract change | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| ProjectMember public contract incomplete | `PROJ-P0-006` | active membership、role、exactly-one OWNER invariant、isolation | 列表与成员 mutation | TYPE A — PUBLIC API REQUIRED | 增加 list/add/update/remove；现有 member PATCH 提供显式原子 ownership transfer | 客户端必须主动管理正式成员且不能隐式选择继任者 |
| Artifact API incomplete | M1 Artifact lifecycle、文件安全 | 不可变原件、hash、storage metadata、project ownership | 上传、状态、详情和授权下载 | TYPE A — PUBLIC API REQUIRED | 增加 list/initiate/transfer/complete/detail/download | MinIO smoke 不是 Artifact 业务合同 |
| Approval creation/ownership undefined | 正式高风险审批 | owning domain command 产生 ApprovalRecord | 只读 projection 与用户决定 | TYPE B — DOMAIN COMMAND CREATES RESOURCE | 无 generic create；Service 创建，用户 approve/reject/cancel | 客户端不能制造审批事实 |
| Audit query API undefined | `PROJ-P0-010`、M1 审计 UI | Service append-only side effect | 最近操作、筛选和分页 | TYPE D — READ PROJECTION ONLY | 增加 project-scoped AuditLog list；无客户端写入口 | UI 需要可追踪活动但不拥有审计 |
| Job creation ownership undefined | M1 Job foundation | domain Service 创建 Job；Worker 创建 ProcessingRun | list/detail/status/retry/cancel/SSE | TYPE B + TYPE C + TYPE D | 无 generic create；增加 project Job list，冻结执行责任 | Job 是业务执行事实，不是独立用户意图 |
| M1 idempotency binding incomplete | M1 写操作和异步边界 | Service/Repository 绑定 key、hash、事务与授权 | controller 生成/复用 key并处理 replay/conflict | TYPE C — INTERNAL SERVICE CONTRACT | 冻结逐操作矩阵、scope、重放、冲突、保留与失败边界 | 后续实现可直接写契约测试 |
| No legitimate M1 Approval consumer | 风险分级与 M1 范围 | 基础设施存在，真实 consumer 在后续 milestone | projection fixture，不展示虚假业务审批 | TYPE E — NO CONTRACT CHANGE REQUIRED | 明确 M1 不制造 FORMAL_APPROVAL operation | M1 没有改变科研事实的真实高风险命令 |
| ModelInvocation M1 scope inconsistent | `AGOV-P0-001`、`AGOV-P0-002` | Prompt governance 与 invocation audit persistence | 无 M1 用户操作；仅测试/状态边界 | TYPE C — INTERNAL SERVICE CONTRACT | 加入 M1 persistence deliverable；无 Provider/runtime | 首次 M2/M3 模型调用前必须可审计 |
| Project Overview M2+ fields ambiguous | `PROJ-P0-004` | projection 区分模块 availability 与真实 count | 不把 unavailable 展示为 empty/zero | TYPE D — READ PROJECTION ONLY | 增加 availability；未实现值为 `null` | 保护 M1 UI 和演示真实性 |
| M0 error envelope differs from formal contract | M0 regression + M1 API | 保留 M0 endpoint 行为；M1 使用正式 envelope | adapter 归一化两种 Envelope | TYPE E — NO M0 CONTRACT REWRITE | 文档化兼容策略，不改 M0 API | 避免扩大为 M0 重构 |

Job retry 是 intentional clarifying amendment：批准基线已要求 retry 创建新的 ProcessingRun，
但未明确 Job identity；M1 冻结为 same Job + `retry_count` increment + new ProcessingRun。
当前没有正式 M1 Job 数据或迁移兼容负担。

### M1 创建责任

```text
public user/domain command
→ owning Service validates authorization, project, state and idempotency
→ Service creates domain object and any AuditLog / ApprovalRecord / Job side effect
→ Worker creates ProcessingRun when execution actually starts
```

禁止新增：

```text
POST <API_BASE>/jobs
POST <API_BASE>/approvals
POST <API_BASE>/audit-logs
POST <API_BASE>/processing-runs
```

### M1 Contract Amendment stable identifier delta

统计规则沿用 `docs-m1-approved`：扫描全部受版本控制且不在 `docs/archive/` 的 Markdown，
提取以正式 API base prefix 开头的 path 字符串并按完整 path 唯一化；不合并参数名，也不把 HTTP method
计入 identifier。以下 delta 已纳入 2026-07-31 Project Owner 批准的 M1 Contract Amendment。

| Identifier | Before | After | Change |
| --- | ---: | ---: | --- |
| API path identifiers | 236 | 242 | +6 additive；removed 0；renamed 0 |
| Public METHOD + path operations | baseline contract set | baseline + 12 | +12 additive；removed 0；renamed 0 |
| Requirement IDs | 181 | 181 | added 0；removed 0；renamed 0 |
| Acceptance IDs | 16 | 16 | 0 |
| Existing schema names | baseline | baseline | renamed 0 |
| Existing Tool names | baseline | baseline | changed 0 |
| Milestone IDs | baseline | baseline | changed 0 |
| ADR IDs | baseline | baseline | changed 0 |

6 个新增 path identifiers 对应 Member collection/item、Artifact project collection、Artifact
content transfer、project Job list 和 project Audit list。12 个 METHOD + path operations 全部
属于 Member、Artifact、Job/Audit read projection 的预期 M1 amendment；历史 path 指标不区分
GET/POST 或 PATCH/DELETE，因此两个数字不要求相等。

新增公共错误码仅为 `MEMBER_ALREADY_ACTIVE`、`LAST_PROJECT_OWNER`、
`APPROVAL_EXPIRED`、`APPROVAL_STALE`；既有错误码未删除、重命名或静默改义。

### M1 Enum / projection delta

| Name | Old values at `docs-m1-approved` | New values | Authority | Persistent domain enum | OpenAPI enum | Frontend projection only |
| --- | --- | --- | --- | --- | --- | --- |
| `PermissionAction` M1 additions | `project.read`, `project.update`, `project.delete`, `literature.read`, `literature.create`, `literature.decide`, `dataset.read`, `dataset.upload`, `dataset.approve_transform`, `analysis.create`, `analysis.approve`, `analysis.run`, `figure.create`, `figure.confirm`, `manuscript.upload`, `manuscript.review`, `evidence.read`, `claim.confirm`, `export.create` | old values + `project.manage_members`, `artifact.read`, `artifact.upload`, `artifact.download`, `job.read`, `job.cancel`, `job.retry`, `approval.read`, `approval.decide`, `approval.cancel`, `audit.read` | Common API Contract | NO; policy constants | YES | NO; API authorization projection consumed by frontend |
| Public error code additions | existing approved error set | old values + `MEMBER_ALREADY_ACTIVE`, `LAST_PROJECT_OWNER`, `APPROVAL_EXPIRED`, `APPROVAL_STALE` | Common API Contract | NO | YES | NO |
| `AuditLog.outcome` | not defined | `SUCCEEDED`, `FAILED`, `DENIED` | Foundation model + Project API | YES | YES | NO |
| `ModelInvocation.status` | value set not defined | `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED` | Foundation model + AI Schema | YES | NO in M1 | NO |
| `ModelInvocation.data_access_level` | fields named; value set not defined | `METADATA_ONLY`, `REDACTED_CONTENT`, `VERIFIED_EVIDENCE_ONLY`, `APPROVED_FULL_CONTENT` | Foundation model + AI Schema | YES | NO in M1 | NO |
| `ProjectOverview.module_availability` | field absent | `NOT_AVAILABLE`, `AVAILABLE`, `DEGRADED` | Project API | NO | YES | NO; API read projection consumed by frontend |
| `JobSseEventType` | existing Job events without resync marker | existing values + `job.resync_required` | Common Job/SSE Contract | NO | NO; SSE protocol contract | NO |
| Model test execution mode | Mock/Recorded prose, no stable uppercase value set | `MOCK`, `RECORDED` | AI Schema | NO; stored in implementation metadata | NO | NO |

Artifact、Approval、Job、ProjectMember role 和 frontend UI contract registry 复用批准基线的
既有 value sets；本 amendment 不增加其他持久化 domain enum。

## 9.4 明确不做

* 不实现具体文献抽取；
* 不实现数据分析；
* 不实现 Agent；
* 不实现复杂项目协作；
* 不实现实时多人编辑。

## 9.5 后端交付物

### Projects 模块

* ResearchProject；
* ProjectMember；
* 创建项目；
* 项目列表；
* 项目详情；
* 项目更新；
* 项目归档；
* 项目软删除；
* 项目权限查询。

### Artifacts 模块

* Artifact；
* ArtifactRelation；
* 上传初始化；
* 上传确认；
* 哈希；
* MIME 和文件头检查；
* MinIO 写入；
* 下载授权；
* 原始文件不可变；
* 软删除；
* 隔离状态。

### Approvals 模块

* ApprovalRecord；
* 供领域 Service 调用的审批请求创建边界；
* 批准；
* 驳回；
* 撤销或失效；
* 审批内容哈希；
* 审批对象项目校验。

### Jobs 模块

* Job；
* ProcessingRun；
* 供产生异步工作的领域 Service 调用的 Job 创建边界；
* 状态查询；
* 进度更新；
* 取消请求；
* 重试；
* 幂等；
* 错误结构；
* SSE 或轮询接口。

### Audit 模块

* AuditLog；
* 追加写；
* 项目操作日志；
* 请求 ID；
* Job ID；
* 操作者类型；
* 对象摘要。

### Prompt / Model Governance 模块

* Git 管理的 Prompt manifest；
* ModelInvocation 持久化；
* requested/max/effective 数据访问校验；
* Mock/Recorded 测试模式；
* 不接入模型 Provider、Agents SDK 或 Agent runtime。

## 9.6 前端交付物

* 登录；
* 项目列表；
* 创建项目；
* 项目基础详情；
* 文件上传组件；
* 上传进度；
* Job 状态组件；
* 审批卡片基础组件；
* 审计列表基础组件；
* 统一错误显示；
* 请求 ID 展示。

## 9.7 数据库与迁移

至少创建：

```text
users
research_projects
project_members
artifacts
artifact_relations
approval_records
audit_logs
jobs
processing_runs
idempotency_records
model_invocations
```

必须建立：

* `project_id` 索引；
* 资源外键；
* `storage_key` 唯一约束；
* `sha256` 索引；
* Job 幂等索引；
* ProjectMember 唯一约束；
* 乐观锁字段；
* 软删除字段；
* 失效字段。

## 9.8 API 与契约

必须实现并冻结核心端点：

```text
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
POST   /api/v1/projects/{project_id}/archive

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

GET    /api/v1/projects/{project_id}/jobs
GET    /api/v1/jobs/{job_id}
POST   /api/v1/jobs/{job_id}/cancel
POST   /api/v1/jobs/{job_id}/retry
GET    /api/v1/jobs/{job_id}/events

GET    /api/v1/projects/{project_id}/approvals
GET    /api/v1/approvals/{approval_id}
POST   /api/v1/approvals/{approval_record_id}/approve
POST   /api/v1/approvals/{approval_record_id}/reject
POST   /api/v1/approvals/{approval_id}/cancel

GET    /api/v1/projects/{project_id}/audit-logs
```

不存在 generic Job、Approval、AuditLog 或 ProcessingRun 创建 API。它们的创建责任由本文件 9.3A 和对应 API/Service 契约定义。

## 9.9 确定性工具

* SHA-256；
* MIME 检测；
* 文件头检测；
* 安全文件名；
* 对象存储键生成；
* 幂等请求哈希；
* 审批内容哈希。

## 9.10 测试要求

必须覆盖：

* 项目创建；
* 项目成员权限；
* 跨项目访问拒绝；
* Artifact 上传；
* 重复文件；
* 文件哈希；
* 原文件不可覆盖；
* 未授权下载拒绝；
* Job 状态转换；
* Job 重试；
* 幂等重放；
* 审批项目归属；
* 审批内容变化后失效；
* 审计追加写；
* 乐观锁冲突。

## 9.11 安全要求

* 所有资源校验 `project_id`；
* UUID 不构成授权；
* 文件名不影响存储路径；
* 上传多层校验；
* 下载使用短期授权；
* 已隔离文件不可下载；
* 审批不可由 Agent 自动完成；
* Job Worker 重新校验权限和状态。

## 9.12 演示成果

```text
登录
→ 创建项目
→ 管理项目成员
→ 上传文件
→ 文件生成 Artifact
→ 查看审计日志
```

Job、ProcessingRun 和 ApprovalRecord 在 M1 通过 Service/domain tests、contract fixtures 和前端 projection fixtures 验证。M1 不为演示人造脱离真实领域风险的 Job 或 FORMAL_APPROVAL consumer。

## 9.13 完成条件

1. 项目隔离测试全部通过；
2. 原始 Artifact 哈希不可变；
3. 领域 Service 可创建 Job，Job 可查询、取消和按契约重试；
4. 领域 Service 可创建 ApprovalRecord，审批决定 API 可批准、驳回和取消；
5. 审计记录不可普通修改；
6. 前端可展示项目、上传、Job 和审批；
7. 所有写接口拥有权限检查。

## 9.14 可并行任务

* Project 与成员；
* Artifact；
* Job；
* Approval；
* 前端基础组件。

## 9.15 阻塞下一阶段的缺陷

* 跨项目读取；
* 原始文件覆盖；
* Job 无幂等；
* 审批可被绕过；
* Artifact 下载无权限校验；
* 迁移不稳定。

## 9.16 Codex 推荐任务顺序

1. 实现 Project；
2. 实现项目权限；
3. 实现 Artifact；
4. 实现上传和下载；
5. 实现 AuditLog 追加写与查询投影；
6. 实现 Job；
7. 实现 ProcessingRun；
8. 实现 ApprovalRecord 基础设施；
9. 实现 Prompt manifest 与 ModelInvocation 治理底座；
10. 集成前端；
11. 完成跨项目安全测试。

---
