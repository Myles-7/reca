# Backend, Data, and Async Rules

- 文档名称：Backend, Data, and Async Rules
- 所属入口文档：[AGENTS.md](../../AGENTS.md)
- 文档状态：Conditional Approval
- Migration status: COMPLETE

## 权威范围

本文件详细规定后端模块、Service、数据库、迁移、数据版本、文件、异步任务和确定性工具的开发方式。

## 不负责的内容

产品范围、完整字段定义、API 形状、测试指标和安全政策仍由对应正式文档决定。

## 1. 当前 M0 后端事实

- 后端根：`backend/app/`；
- 唯一 Settings：`backend/app/core/config.py`；
- 唯一迁移目录：`backend/app/alembic/`；
- 唯一 Celery App：`app.core.celery:celery_app`；
- Celery 源文件：`backend/app/core/celery.py`；
- M0 task：`reca.health_ping`；
- PostgreSQL 与 pgvector 已通过 smoke；
- MinIO 和 GROBID 尚未形成科研业务；
- M0 尚无项目、Artifact、Approval、正式 Job 或科研模型。

## 2. 模块化单体

后端保持模块化单体，不为业务域建立独立微服务。

推荐模块内结构：

```text
module/
├── api.py
├── schemas.py
├── models.py
├── service.py
├── repository.py
├── errors.py
└── tests/
```

依赖方向：

```text
API → Service → Repository / Domain
Worker → Service
Tool → Service
Service → Direct Library / Adapter Protocol / Isolated Service
Adapter → External Library / Provider
```

禁止 Router、Worker、Tool 或前端绕过 Service 直接操作业务表。

## 3. Service 与事务

Service 负责：

- 权限和项目成员校验；
- 同项目关系校验；
- 状态转换和前置条件；
- 乐观锁与幂等；
- `ApprovalRecord` 版本核验；
- 事务边界；
- 失效传播；
- Artifact 和派生产物登记；
- 审计事件。

Router 只负责请求解析、认证上下文、Schema 验证、调用 Service 和错误映射。

## 4. 领域与数据保护

- 所有核心业务对象必须有 `project_id`；
- 跨对象 Link 两端必须属于同一项目；
- 逻辑对象与版本对象分离；
- 原始 `Artifact` 和 Original `DatasetVersion` 不可覆盖；
- 新版本通过显式关系连接旧版本；
- 计划、审批、执行、结果和 AI 建议分别建模；
- 失效使用状态和原因传播，不删除历史；
- 审计记录追加写；
- JSONB 只保存可变、非核心、可版本化细节；
- 正式字段、状态和约束以数据模型文档为准。

不得用一个大 JSON、聊天记录或 ToolCall 代替正式领域对象。

## 5. 数据库修改

修改模型前必须检查：

- 表与字段的权威定义；
- nullable、default、unique、index 和 check constraint；
- 外键删除行为；
- 项目隔离和同项目约束；
- 状态机和兼容性；
- 现有迁移顺序与数据库数据。

迁移规则：

- 只放在 `backend/app/alembic/versions/`；
- revision 和 down_revision 必须正确；
- 不修改已发布迁移来伪装新状态；
- 新增非空字段必须有安全回填路径；
- 枚举变更必须考虑 PostgreSQL 兼容和回滚；
- 重命名或删除字段必须有迁移和兼容计划；
- 空库 `upgrade head` 必须成功；
- 第二次 `upgrade head` 必须成功；
- 不引用任何非权威迁移目录。

当前命令：

```bash
uv run alembic upgrade head
uv run alembic upgrade head
```

## 6. Artifact 与文件

- 所有上传和派生文件统一通过 `Artifact`；
- 数据库保存元数据、哈希、存储键和版本关系；
- 文件内容存对象存储，不塞入业务 JSON；
- 原文件永不覆盖；
- 派生文件创建新 Artifact；
- 文件名仅用于展示，存储键由系统生成；
- 上传必须校验大小、扩展名、MIME、magic bytes 和哈希；
- PDF、DOCX、CSV、XLSX、ZIP 均视为不可信输入；
- 临时文件必须使用受控目录并清理；
- 下载必须重新校验权限和项目作用域。

## 7. 文献、数据与分析

文献：

- 元数据与 PDF 分离；
- DOI 和来源状态可核验；
- GROBID 失败时允许 pypdf 回退并降低定位置信度；
- `EvidenceSpan` 记录真实页码、位置、文本、哈希和验证状态；
- 未定位证据不能表示为伪造 EvidenceSpan。

数据：

- Original `DatasetVersion` 不可变；
- 数据质量检查与处理计划分离；
- `CleaningPlan` 先预览、审批，再执行；
- 每次转换生成新版本和 transformation 记录；
- 异常值不能在无批准时静默删除。

分析与图表：

- `AnalysisPlan` 先验证变量、样本关系、方法和前提；
- 批准后由确定性程序执行；
- 正式数字只能来自 `AnalysisResult`；
- 模型只能解释结果，不能计算或改写数字；
- 图表必须绑定分析运行和数据版本；
- 重绘生成新 Figure，不覆盖旧图。

## 8. 异步任务

必须异步的典型任务包括 PDF 解析、批量检索、数据质量、数据转换、分析、图表、论文检查、证据图、导出和 AgentRun。

规则：

- API 创建 Job 后立即返回；
- Job 与领域 `ProcessingRun` 分离；
- Worker 领取任务后重新校验权限、项目、版本和审批；
- 使用幂等键、数据库锁或唯一约束防止重复结果；
- 重试只用于明确可重试错误；
- 取消必须有可观察状态；
- 失败保存稳定 reason code 和脱敏信息；
- 不得把失败或降级显示为成功；
- SSE 只传状态，不成为业务事实来源。

唯一 Celery App 命令：

```bash
docker compose exec -T worker celery -A app.core.celery:celery_app inspect ping
```

不得注册任意代码执行、SQL、Shell、文件系统或无限网络工具。

## 9. 第三方能力与外部服务

按替换需求、领域污染、离线 Mock、许可证或安全边界与维护成本选择直接库、Protocol/Adapter 或隔离服务。以下复杂边界继续通过转换层隔离：

- OpenAlex 响应转换为内部 Schema；
- GROBID/pypdf 转换为统一文档页和 chunk；
- 模型 Provider 转换为严格 AI Schema；
- MinIO 转换为受控 Artifact 存储操作；
- 统计和图表引擎返回确定性结构化结果。

Adapter 不决定产品状态，不直接创建业务审批，也不吞掉外部错误。

成熟稳定、接口很小、无替换需求且不污染领域模型的库允许由 Service 直接集成。直接集成不允许 Router、Worker 或 Tool 绕过 Service，也不改变项目隔离、版本血缘、正式统计和高风险审批规则。

## 10. 配置与错误

- 配置只来自 Settings 和环境；
- 不在代码中硬编码 Secret、URL 或凭据；
- production 对缺失核心配置安全失败；
- 可选 Provider 未配置应返回 `UNCONFIGURED`；
- 领域错误映射为稳定公共错误；
- 外部错误必须分类为可重试、不可重试或降级；
- 日志不得包含敏感正文、Token、连接串或内部堆栈。

## 11. 后端完成检查

- 模块边界与依赖方向正确；
- Service 承担业务前置条件；
- 项目隔离和不可变规则有测试；
- 迁移目录和 revision 正确；
- 空库和重复迁移通过；
- 异步幂等、失败和取消可验证；
- 正式数字来自确定性工具；
- Approval 不能被绕过；
- API、数据模型和测试文档同步；
- 必要时 clean-room 通过。

## 返回入口文档

返回 [AGENTS.md](../../AGENTS.md)。
