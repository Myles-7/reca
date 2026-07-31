# 研证链 AI（RECA）安全与开源治理

> RECA 0.1 面向个人使用和校级比赛。安全治理以演示稳定、科研可信、
> 原始材料保护、基本隐私和合法复用开源成果为目标，不以企业生产安全
> 成熟度作为 Competition Edition 的完成条件。

## 文档组成

本入口文档与以下子文档共同构成本领域正式开发基准。入口负责场景、
分级、硬护栏和导航；子文档负责详细政策。发生冲突属于文档缺陷，开发者
和 Codex 不得自行选择更宽松解释。

| 子文档 | 唯一权威范围 |
| --- | --- |
| [SECURITY_CONTROLS.md](./security/SECURITY_CONTROLS.md) | 部署场景、认证、授权、项目隔离、密钥、日志、网络和基础运行控制 |
| [FILE_MODEL_AND_AGENT_SECURITY.md](./security/FILE_MODEL_AND_AGENT_SECURITY.md) | 文件、Artifact、模型数据访问、Prompt injection、Agent、审批和导出安全 |
| [OPERATIONS_DATA_AND_INCIDENTS.md](./security/OPERATIONS_DATA_AND_INCIDENTS.md) | 演示恢复、Worker、降级、备份、事件处理和未来生产运维 |
| [OPEN_SOURCE_GOVERNANCE.md](./security/OPEN_SOURCE_GOVERNANCE.md) | 依赖、许可证、复用模式、归属、Adapter、ARS-Codex 和根许可证治理 |

`docs/archive/` 为非权威历史材料。

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档版本 | 1.5.1 |
| 适用项目版本 | RECA 0.1 Competition Edition |
| 文档状态 | Conditional Approval |
| 默认部署场景 | `DEMO_LOCAL` |
| 主要读者 | 项目负责人、开发者、测试人员、演示人员和 Codex |
| 最后更新时间 | 2026-07-31 |
| 根许可证 | `PENDING_GOVERNANCE_DECISION` |
| 阶段基线 | [SECURITY_AND_REUSE_OPTIMIZATION_BASELINE.md](./reports/SECURITY_AND_REUSE_OPTIMIZATION_BASELINE.md) |

## 变更记录

| 版本 | 日期 | 状态 | 变更说明 |
| --- | --- | --- | --- |
| 1.2.0 | 2026-07-30 | Conditional Approval | 同步根许可证待决状态和数据访问三层语义 |
| 1.3.0 | 2026-07-31 | Conditional Approval | 拆分控制、文件/模型/Agent、运维和开源治理规范 |
| 1.4.0 | 2026-07-31 | Conditional Approval | 建立 competition-first 安全分级和 effect-first 开源复用政策 |
| 1.5.0 | 2026-07-31 | Conditional Approval | 增加研究项目许可证分类索引、实际引入验收和 Notices 状态准确性要求 |
| 1.5.1 | 2026-07-31 | Conditional Approval | 将 ARS-Codex 未引入说明更新为阶段 11 仓库审查事实；政策不变 |

## 1. 适用场景与非目标

RECA 0.1 当前用途是个人开发和使用、校级比赛展示及有限的校内共享。
首要目标是功能效果、开发速度、演示稳定和科研可信。

Competition Edition 不把以下能力作为完成条件：

- 企业组织、部门、SSO 和复杂 RBAC；
- 大规模多租户 SaaS 隔离体系；
- 法规合规和法律删除请求流程；
- 企业 Secret Manager、DLP 或安全运营中心；
- 异地灾备、多区域恢复、RPO/RTO；
- 全自动 SBOM 和所有等级漏洞的阻断 SLA；
- 高级网络策略、WAF 或正式事件指挥体系。

这些能力归入 `FUTURE_PRODUCTION`，不代表它们对未来公开生产部署不重要。

## 2. 安全级别

### 2.1 `COMPETITION_REQUIRED`

Competition Edition 必须满足的最小可靠性和安全要求。未满足时应修复，
但只有命中第 3 节明确列出的条件才成为 `RELEASE_BLOCKER`。

主要范围：

- 科研来源、证据和统计结果真实；
- 原始材料不可覆盖；
- 密钥不进入不可信位置；
- 文件不执行且路径受控；
- 已有认证和项目级授权不被删除；
- Agent 受 Tool、Service、Schema 和审批边界控制；
- 高风险科研数据操作经过正式审批；
- 外部失败和降级对用户可见；
- 第三方复用有许可证、归属、Commit 和修改记录；
- M0 required CI 与基础设施 clean-room 保持有效。

### 2.2 `COMPETITION_RECOMMENDED`

建议实现但不阻断当前校赛开发和交付：

- 细粒度 RBAC；
- 基础登录限流和更完整审计；
- 杀毒扫描和高级内容消毒；
- 签名 URL；
- 自动 SBOM；
- Medium/Low 漏洞自动阻断；
- 完整模型数据分类和自动脱敏；
- 容器只读文件系统和更严格资源限制；
- 高级网络策略；
- 正式备份演练和完整删除工作流。

推荐项可以按实际部署风险升级为项目门禁，但必须记录触发原因，不能在
文档中默认伪装成 Competition Edition 已实现能力。

### 2.3 `FUTURE_PRODUCTION`

面向公开、商业或大规模部署的强化层：

- 企业权限、组织治理和多租户管理；
- 法规合规、数据保留和法律请求；
- 企业密钥管理、DLP 和安全监控；
- 正式漏洞治理和企业供应链流程；
- 灾难恢复、RPO/RTO 和多区域架构；
- 正式事件响应、长期安全档案和通知体系。

用途或部署范围变化时，必须重新评估本层并更新架构、测试和路线图。

## 3. `RELEASE_BLOCKER`

只有以下问题阻止当前校赛交付：

1. 真实密钥进入仓库、前端包、公开导出或普通日志；
2. 原始 PDF、数据、DOCX 或正式原始版本可被覆盖；
3. 模型生成或伪装成正式统计数字；
4. 伪造文献、`EvidenceSpan`、原文位置或引用；
5. 上传文件可被执行，或可通过文件名、路径、ZIP/DOCX 解包造成明显路径穿越；
6. Agent 可任意执行 Shell、SQL 或 Python；
7. 无许可证或来源不明的代码、Prompt、脚本、测试或其他材料被复制进正式仓库；
8. 第三方许可证、版权归属或强制 NOTICE 被删除；
9. CC BY-NC、Copyleft、文件级许可证或其他特殊内容未隔离、未署名或被错误声明为根许可证覆盖；
10. 演示包含无权使用的敏感、受限或不可再分发材料；
11. 失败、缓存、局部结果或降级被标记为正式成功；
12. 存在 Critical 且与实际执行路径相关、可利用的供应链风险；
13. 六项 M0 required CI 或基础设施 clean-room acceptance 被删除、跳过、伪造或降级。

普通 Low/Medium 漏洞、缺少企业 SBOM、缺少异地灾备或未进行正式恢复演练
不属于 Competition Edition 的 `RELEASE_BLOCKER`。

## 4. 科研可信硬护栏

| 护栏 | Competition Edition 要求 |
| --- | --- |
| 真实来源 | 文献和引用必须来自可验证来源；系统不得生成不存在的来源 |
| EvidenceSpan | 只能引用真实定位内容；缺失时返回缺失或定位不确定，不创建伪证据 |
| 确定性统计 | 正式数字、图表数据、哈希和版本检查来自确定性程序 |
| 原始不可变 | 原始 Artifact、Original DatasetVersion 和原始稿件不原地修改 |
| 人工决定 | Agent 可建议；不可逆或改变正式科研事实的操作由用户正式审批 |
| 失败可见 | 外部服务、模型或解析失败必须显示状态和影响 |
| 证据链 | 正式结果保留输入版本、计划、运行、结果、图表和确认关系 |

不得通过降低科研真实性来换取演示成功。

## 5. Agent 和审批总则

RECA 保持单总控 Agent 架构，正式 Agent 仍在 M8 接入。允许复用第三方
Prompt 或工作流不自动改变该时序。

审批分为：

| 等级 | 用途 |
| --- | --- |
| `AUTO_ALLOWED` | 查询、检索、解析、候选抽取、质量扫描、只读证据查询、规划和预览 |
| `LIGHT_CONFIRMATION` | 采用候选研究问题、修正候选字段、选择图表类型、接受低风险格式修复 |
| `FORMAL_APPROVAL` | 插补、异常值删除、重编码、正式 AnalysisPlan 执行、高风险稿件修改、敏感导出和正式结果失效 |
| `PROHIBITED` | 模型写正式统计、Agent 自我审批、任意代码执行、绕过 Service、覆盖原始对象、为显著性改数据 |

`LIGHT_CONFIRMATION` 的持久化对象与现有 `ApprovalRecord` 类型如何对齐，
由阶段 3 的数据模型和 API 契约统一处理。在完成该对齐前，不得自行改变
已有数据库或 API 语义。

## 6. 部署场景

| 场景 | 定位 | 当前要求 |
| --- | --- | --- |
| `DEMO_LOCAL` | 单机或可信局域环境，当前默认 | 保留现有认证、密钥卫生、私有内部服务和原始材料保护；不新增企业体系 |
| `SHARED_SCHOOL` | 有限校内用户共享，可选增强 | 基础登录、项目级授权、简单成员角色、私有文件访问、基础限流和审计 |
| `PUBLIC_PRODUCTION` | 公开、商业或大规模部署 | 启动 Future Production 安全、合规、运维和许可证复审 |

无论场景如何，已存在的后端权限校验不得删除；多用户能力启用时不得跨
项目访问数据库记录、对象存储路径、SSE 事件或导出内容。

## 7. 开源复用总则

在许可证允许、来源明确并能够维护的前提下，RECA 优先复用成熟开源
项目，以提升作品效果、开发速度和演示稳定性。自行重新实现不再是默认
要求。

允许的复用模式：

```text
PACKAGE_DEPENDENCY
INDEPENDENT_SERVICE
FORK
VENDOR
GIT_SUBMODULE
SELECTIVE_COPY
RESEARCH_REFERENCE
CLEAN_ROOM_REIMPLEMENTATION
```

选择模式不能绕过以下最低要求：

- 核验固定版本或 Commit 的实际许可证文本；
- 保存项目、仓库、版本、复制路径和修改记录；
- 保留许可证、版权归属和适用的 NOTICE；
- 不把第三方贡献表述为 RECA 全部原创；
- 区分代码、数据、PDF、模型、字体和素材的权利；
- 无许可证内容只可研究，不得复制、修改后分发或 Vendor；
- 来源不明内容不得进入正式仓库；
- 用途变化、商业化或公开产品部署前重新审查特殊许可证。

完整规则及全部研究项目的许可证分类矩阵见
[OPEN_SOURCE_GOVERNANCE.md](./security/OPEN_SOURCE_GOVERNANCE.md)。研究记录不等于实际复制或依赖；`THIRD_PARTY_NOTICES.md` 必须描述仓库中的实际状态。

## 8. Adapter 总则

Adapter 是按风险选择的边界，不是所有第三方能力的绝对要求。

外部 API 易变化、需要多实现或离线 Mock、第三方对象不得进入领域层、
存在许可证隔离或安全边界、或契约测试收益明显时必须使用 Adapter。

成熟稳定、接口很小、无替换需求、不污染领域模型且直接使用维护成本更低
的库可以直接集成。直接集成仍不得绕过业务 Service、权限、项目隔离、
科研真实性、数据版本、Schema 和审批规则。

## 9. ARS-Codex 与 clean-room 术语

ARS-Codex 当前用途状态为 `NONCOMMERCIAL_INTENT_DECLARED`。该状态只记录
项目负责人意图，不构成对 CC BY-NC 4.0 “非商业”条件的法律确认。

在核验许可证、保留归属并记录复制和修改后，可以选择性复制 Prompt、
工作流、脚本和测试材料，也可以 Fork、Vendor，或经单独架构决策后作为
运行组件。截至阶段 11 审查基线，仓库没有实际复制、Vendor、Fork 或运行时
引入 ARS-Codex 内容。

必须区分：

- **M0 infrastructure clean-room acceptance**：六项 required CI 的环境隔离验收，继续强制；
- **`CLEAN_ROOM_REIMPLEMENTATION`**：一种可选的第三方复用模式，不再默认强制。

详细决策见 [ADR-001](./decisions/ADR-001-ARS-CODEX-USAGE.md) 和
[来源研究记录](./source-research/academic-research-skills-codex.md)。

## 10. 根许可证

RECA 根许可证继续为：

```text
PENDING_GOVERNANCE_DECISION
```

第三方项目采用 MIT、Apache、CC BY-NC、Copyleft 或其他许可证，均不会
自动决定 RECA 根许可证。未来根许可证只覆盖 RECA 有权授权的内容，不能
覆盖第三方文件自身许可证。

## 11. 变更与文档边界

本入口与四份安全子文档是安全与开源政策权威；产品、数据、契约、测试和
路线图只引用并验收这些规则，不得建立更宽松的平行许可证解释。研究、
计划、Spike、依赖声明和实际复制必须使用不同状态，且不得自行改变现有实现或稳定契约。

任何后续政策变更必须同步唯一完整定义、入口摘要、测试门禁和路线图；
不得静默选择根许可证、降低科研真实性或规避 M0 回归基线。
