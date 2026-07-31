# Security Controls

- 文档名称：Security Controls
- 文档版本：1.1.0
- 所属入口文档：[SECURITY_AND_OPEN_SOURCE.md](../SECURITY_AND_OPEN_SOURCE.md)
- 文档状态：APPROVED FOR M1 DEVELOPMENT
- 最后更新时间：2026-07-31
- Migration status: COMPLETE
- M1 Contract Amendment status: APPROVED

## 变更记录

| 版本 | 日期 | 状态 | 变更说明 |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-31 | Conditional Approval | 文档拆分后的认证、授权、项目隔离和运行控制基线 |
| 1.1.0 | 2026-07-31 | Conditional Approval | 按 DEMO_LOCAL、SHARED_SCHOOL、PUBLIC_PRODUCTION 重构控制要求 |

## 权威范围

本文件是部署场景、认证、授权、项目隔离、输入验证、数据库与对象存储、
Web、日志、密钥、网络和容器基础控制的唯一完整定义。

不负责文件解析、模型与 Agent 专项规则、事件响应流程或第三方许可证分类。
返回 [安全与开源治理入口](../SECURITY_AND_OPEN_SOURCE.md)。

## 1. Competition-first 原则

RECA 0.1 当前默认场景是 `DEMO_LOCAL`。安全控制必须与实际部署范围相称，
不得为了模拟企业生产成熟度阻塞功能、可信科研闭环和演示稳定性。

下列控制在所有场景都必须保留：

1. `.env` 和真实 Secret 不提交；
2. Token、API Key、密码和对象存储凭据不写普通日志；
3. 模型和对象存储密钥不进入前端包；
4. 数据库、队列和对象存储不得匿名公开；
5. 已存在的后端认证与权限校验不得删除或改成仅前端判断；
6. 多用户能力启用时不得跨项目访问记录、文件、事件或导出；
7. 用户输入和外部响应必须经过 Schema/类型校验；
8. 权限、状态和高风险操作由 Service 端强制执行。

## 2. 部署场景

### 2.1 `DEMO_LOCAL`

当前默认目标：单机开发、个人使用或可信局域环境中的比赛演示。

必须：

- 保留 M0 已实现的认证和基础安全功能；
- 使用后端配置加载 Secret，前端只接收公开配置；
- 只公开演示所需的 Web/API 端口；
- PostgreSQL、Valkey、MinIO 管理面和 GROBID 管理接口保持内部访问；
- 演示账户、数据和临时密钥可重置；
- 错误响应不泄露 Secret、连接串或完整堆栈；
- 若只有单用户，仍保留未来项目作用域字段和 Service 边界。

不要求：

- 组织、部门、SSO、企业身份提供商；
- 企业 RBAC、管理员审批链或定期访问审查；
- 复杂限流、WAF 或安全运营平台；
- 正式隐私请求与法律删除流程；
- 企业 Secret Manager 或自动轮换平台；
- 高级容器、网络或主机加固平台。

### 2.2 `SHARED_SCHOOL`

可选增强场景：有限校内用户共享同一部署。

至少具备：

- 基础登录和会话失效；
- 项目级授权；
- 简单成员角色，例如 Owner、Editor、Viewer；
- 私有文件访问，不允许匿名列举 Bucket；
- 登录和昂贵接口的简单限流；
- 成员变更、高风险操作和敏感导出的基础审计；
- 用户移除后不能继续访问项目资源。

这不是企业多租户承诺。共享范围扩大时应重新评估威胁模型。

### 2.3 `PUBLIC_PRODUCTION`

公开、商业、大规模或承载真实敏感科研数据的部署属于未来生产强化。
届时应单独设计：

- 企业身份、SSO、MFA、复杂 RBAC 和管理员治理；
- 多租户隔离、访问复核和权限证明；
- 企业 Secret Manager、集中轮换和密钥审计；
- WAF、DDoS/滥用防护、高级限流和网络策略；
- 容器只读文件系统、Capabilities 管理和主机加固；
- 法规、隐私请求、数据驻留和正式审计归档；
- 集中安全监控、告警和事件响应。

这些项目统一标记为 `FUTURE_PRODUCTION`，不阻塞 RECA 0.1 校赛版。

## 3. 身份认证

### 3.1 Competition Edition 要求

- 不删除当前已实现的认证入口、Token 校验和密码保护；
- 登录凭据只在受控后端处理；
- Token 无效、过期或账户停用时拒绝访问；
- 不在 URL、普通日志或前端持久化公开长期有效 Secret；
- 演示默认账户必须在演示后可停用或更换凭据；
- 错误信息不确认某个私有账户是否存在。

复杂密码策略、MFA、SSO、企业账号生命周期和自动异常登录检测属于
`COMPETITION_RECOMMENDED` 或 `FUTURE_PRODUCTION`，取决于部署范围。

### 3.2 登录保护

`DEMO_LOCAL` 不要求复杂限流。部署到共享网络时，建议对登录、密码重置和
高成本接口增加按 IP/账户的简单速率限制。公开生产部署必须重新设计。

## 4. 授权与项目隔离

### 4.1 服务端权威

前端隐藏按钮只用于体验，不能代替授权。Service 在读取或写入前至少检查：

1. 当前用户身份；
2. 目标项目；
3. 用户与项目的成员关系；
4. 操作所需的简单角色；
5. 目标对象属于同一项目；
6. 对象版本和状态允许该操作；
7. 高风险操作是否满足确认或审批要求。

UUID、对象键或前端路由不是秘密，不能作为授权依据。

普通已认证用户若不是目标项目成员，读取 project-scoped 对象统一采用不披露语义，
返回 `404 RESOURCE_NOT_FOUND`；已是成员但缺少具体 action 时返回
`403 PERMISSION_DENIED`。该规则同样适用于 Artifact 下载、Job/SSE、Approval 和 Audit
projection，不得通过响应差异枚举项目资源。

`superuser` 不是 ProjectMember role，也不自动创建或恢复 membership。仅后端 policy 可
为管理/恢复场景执行 override；override 必须关联 actor、project、target、request_id、
reason 和 outcome 写入 AuditLog。前端管理员标记不能代替该 policy。

### 4.2 项目作用域

启用多用户能力时，下列资源必须受 `project_id` 或等价所有权约束：

- ResearchProject、Artifact、Document 和 Dataset；
- EvidenceSpan、Analysis、Figure、Manuscript 和 Export；
- Job、ProcessingRun、AgentRun、ToolCall 和审计记录；
- 对象存储键、向量检索过滤、SSE 事件和下载响应。

跨对象关联必须验证双方属于同一项目。不得只验证其中一个 ID。

### 4.3 简单角色

Competition Edition 允许小型角色集。角色能力应由 Service 显式定义，不
建设组织层级、策略语言或企业权限引擎。复杂 RBAC 属于
`FUTURE_PRODUCTION`。

## 5. 输入与数据库控制

### 5.1 输入验证

- API 请求使用严格 Schema；
- 枚举、UUID、数值范围、分页和排序字段使用白名单；
- 不为错误输入静默转换成高风险状态；
- 富文本按展示场景转义或消毒；
- 外部服务响应也视为不可信输入；
- 原始请求体和模型内容不得无差别写入普通日志。

### 5.2 数据库

- 业务访问通过 Service/Repository 和参数化查询；
- 不允许来自用户或 Agent 的任意 SQL；
- 迁移进入版本控制并沿用 `backend/app/alembic/`；
- 应用账户不得为了开发方便获得不必要的管理权限；
- 数据库连接串不进入前端或日志；
- 审计和正式版本历史不得被普通更新覆盖。

## 6. 对象存储与文件访问

- Bucket 不匿名公开；
- 服务端根据项目和 Artifact 权限生成下载或流式响应；
- 存储键由系统生成，不使用用户文件名作为路径；
- 用户文件名只作为显示元数据；
- 对象存储凭据仅在后端和 Worker 使用；
- 下载前检查项目权限、Artifact 状态和许可证/敏感数据限制。
- 上传初始化、内容传输和完成确认都必须重新校验 actor 与项目；upload ID 不能作为授权凭据；
- 浏览器不得获得 Bucket、永久对象键或对象存储凭据；
- 完成确认前的对象不是可下载的正式 Artifact；hash、size、MIME 或文件头不一致时不得进入 `AVAILABLE`；
- 同一 upload session 不得覆盖已写对象，原始 Artifact 的任何更新路径都不得覆盖原始 bytes。

签名 URL 是 `COMPETITION_RECOMMENDED`。Competition Edition 可以使用经过
授权的后端流式下载，不要求为了形式引入签名 URL 基础设施。

## 7. 外部服务与 Adapter

外部 API、GROBID、模型服务和第三方库必须遵守超时、错误转换、最小数据
访问和降级披露。是否使用 Adapter 按以下条件决定：

必须使用 Adapter：

- 外部 API 易变化、远程、限额或需要替换；
- 需要多实现、Mock、Recorded 或离线替代；
- 第三方对象不得进入领域层；
- 存在许可证隔离或安全边界；
- 统一失败/降级契约能产生明显测试收益。

允许直接集成：

- 成熟稳定库且接口很小；
- 无现实替换需求；
- 不把第三方类型持久化为领域契约；
- 直接使用显著提升速度，维护成本低于抽象成本。

两种方式都不得绕过 Service、授权、Schema、版本、审批或审计。

## 8. Web、日志和错误

Competition Edition 必须：

- 明确 CORS 来源，不在共享/公开环境使用任意来源；
- 防止把未转义用户内容直接作为 HTML；
- 返回稳定的公共错误结构；
- 普通日志不含密码、Token、API Key、数据库 URL、MinIO Secret 或完整敏感数据；
- 生产式详细堆栈不直接返回给用户；
- 记录请求 ID、项目 ID、操作、状态和必要的错误码。

HTTPS、安全响应头、CSRF 策略和更强 XSS 防护应按实际暴露方式启用。
公网部署时升级为 `PUBLIC_PRODUCTION` 设计。

## 9. 密钥与配置

### 9.1 `COMPETITION_REQUIRED`

- 真实 `.env` 不提交；
- `.env.example` 只含占位符和说明；
- Secret 从后端环境或受控本地配置读取；
- 前端构建变量不得包含模型、数据库或对象存储密钥；
- 日志、错误、截图、演示包和 ReproPackage 不含有效 Secret；
- 泄露的临时密钥可以快速撤销或更换；
- Secret 扫描继续属于 M0 required CI。

### 9.2 推荐与未来生产

定期人工轮换属于 `COMPETITION_RECOMMENDED`。企业 Secret Manager、自动
轮换、双人访问和集中密钥审计属于 `FUTURE_PRODUCTION`。

## 10. 网络与容器

### 10.1 Competition Edition

- 只发布实际需要的端口；
- 内部服务使用 Compose 内部网络；
- 镜像和服务版本保持固定；
- 健康检查用于演示恢复和依赖状态，不伪装业务能力；
- 资源限制可用于防止解析或 Worker 拖垮演示机器；
- 可行时使用非 root 镜像，但第三方镜像限制不得阻塞全部开发。

### 10.2 Future Production

只读文件系统、Capabilities drop、镜像签名、集中漏洞治理、高级网络策略、
零信任服务身份和主机加固统一归入 `FUTURE_PRODUCTION`。

## 11. 控制验证

Competition Edition 至少验证：

- `.env`、Secret、Token 不进入仓库和前端产物；
- 未授权请求被后端拒绝；
- 多用户启用时跨项目读取、下载和 SSE 被拒绝；
- 数据库和对象存储不匿名公开；
- 输入 Schema、枚举和项目归属检查生效；
- 直接集成与 Adapter 均不绕过 Service；
- 六项 M0 required CI 和 infrastructure clean-room acceptance 未被规避。

阶段 3 将对齐详细测试门禁；本文件不在本阶段修改 CI 或测试实现。
