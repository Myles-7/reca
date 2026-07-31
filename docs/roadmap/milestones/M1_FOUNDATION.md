# M1_FOUNDATION

- 所属入口文档：[IMPLEMENTATION_ROADMAP.md](../../IMPLEMENTATION_ROADMAP.md)
- 文档状态：Conditional Approval
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
* 创建审批请求；
* 批准；
* 驳回；
* 撤销或失效；
* 审批内容哈希；
* 审批对象项目校验。

### Jobs 模块

* Job；
* ProcessingRun；
* 创建任务；
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

POST   /api/v1/projects/{project_id}/artifacts/uploads
POST   /api/v1/projects/{project_id}/artifacts/uploads/{upload_id}/complete
GET    /api/v1/artifacts/{artifact_id}
GET    /api/v1/artifacts/{artifact_id}/download

GET    /api/v1/jobs/{job_id}
POST   /api/v1/jobs/{job_id}/cancel
POST   /api/v1/jobs/{job_id}/retry
GET    /api/v1/jobs/{job_id}/events

POST   /api/v1/projects/{project_id}/approvals
POST   /api/v1/approvals/{approval_record_id}/approve
POST   /api/v1/approvals/{approval_record_id}/reject
```

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
→ 上传文件
→ 文件生成 Artifact
→ 创建 Job
→ 查看任务进度
→ 创建审批记录
→ 查看审计日志
```

## 9.13 完成条件

1. 项目隔离测试全部通过；
2. 原始 Artifact 哈希不可变；
3. Job 可查询、取消和重试；
4. ApprovalRecord 可创建、批准和驳回；
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
5. 实现 Job；
6. 实现 ProcessingRun；
7. 实现 ApprovalRecord；
8. 实现 AuditLog；
9. 集成前端；
10. 完成跨项目安全测试。

---
