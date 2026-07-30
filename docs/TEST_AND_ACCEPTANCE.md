# 研证链 AI（RECA）测试与验收标准

> 面向高校科研训练的全流程可信科研智能体
> Research Evidence Chain Agent

---

<!-- DOCUMENT_COMPOSITION_START -->
## 文档组成

本入口文档与其列出的子文档共同构成本领域的正式开发基准。
入口文档负责核心决策、红线和索引，子文档负责详细规范。
两者发生冲突属于文档缺陷，开发者和 Codex 不得自行猜测。

| 子文档 | 唯一权威范围 |
| --- | --- |
| [M0_REGRESSION_BASELINE.md](./testing/M0_REGRESSION_BASELINE.md) | 六项 required CI、clean-room 合同、两个 LOW 风险及 M1-M9 不退化规则 |
| [TEST_STRATEGY_AND_ENVIRONMENTS.md](./testing/TEST_STRATEGY_AND_ENVIRONMENTS.md) | 测试金字塔细节、目录、环境、数据治理、Mock/Recorded/Live、单元与前端策略 |
| [GOLDEN_SETS_AND_METRICS.md](./testing/GOLDEN_SETS_AND_METRICS.md) | 文献、EvidenceSpan、数据、统计、图表、论文、证据链、AI、Agent 与 Prompt 指标和容差 |
| [CONTRACT_INTEGRATION_AND_SECURITY_TESTS.md](./testing/CONTRACT_INTEGRATION_AND_SECURITY_TESTS.md) | API、Schema、Tool、Adapter、数据库、外部组件、状态机、安全、数据访问与降级测试 |
| [E2E_ACCEPTANCE_AND_RELEASE_GATES.md](./testing/E2E_ACCEPTANCE_AND_RELEASE_GATES.md) | 全部 AC/E2E、MANU-P0-018、性能、离线演示、发布门禁、比赛验收和报告模板 |

`archive/` 为非权威历史材料。
<!-- DOCUMENT_COMPOSITION_END -->

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档名称 | `TEST_AND_ACCEPTANCE.md` |
| 文档版本 | 1.4.0 |
| 适用项目版本 | RECA 0.1 Competition Edition |
| 文档状态 | Conditional Approval |
| 文档类型 | 测试权威入口、核心原则、缺陷等级、完成定义与门禁索引 |
| 主要读者 | 测试人员、前端开发、后端开发、AI 开发、产品负责人、运维人员、Codex |
| 负责人 | RECA Team |
| 最后更新时间 | 2026-07-31 |
| 上位文档 | `README.md`、`AGENTS.md`、`PRODUCT_REQUIREMENTS.md`、`ARCHITECTURE.md`、`DATA_MODEL_AND_WORKFLOW.md`、`API_AI_TOOL_CONTRACTS.md` |
| 关联文档 | `SECURITY_AND_OPEN_SOURCE.md` |

## 变更记录

| 版本 | 日期 | 状态 | 变更说明 | 负责人 |
| --- | --- | --- | --- | --- |
| 1.0.0 | 2026-07-29 | Draft | 建立 RECA 0.1 完整测试分层、黄金测试集、AI 评测、核心验收用例和发布门禁 | RECA Team |
| 1.0.0 | 2026-07-29 | Approved | 确认为 M0 开发前正式基准 | Myles-7 |
| 1.1.0 | 2026-07-30 | Approved | 增加 Agent 合同、注入、Claim 审核与降级黄金测试 | RECA Team |
| 1.2.0 | 2026-07-30 | Conditional Approval | 建立 M0 Regression Baseline、MANU-P0-018 AC 与真实 Bun 命令约束 | RECA Team |
| 1.3.0 | 2026-07-31 | Conditional Approval | 拆分测试策略、黄金指标、契约安全测试和 E2E 验收；入口保留核心决策与索引 | RECA Team |
| 1.4.0 | 2026-07-31 | Conditional Approval | 同步校赛最小安全护栏、开源来源验收和按风险分层的审批测试 | RECA Team |

---

# 1. 文档目的

本文档定义 RECA 0.1 的测试策略、质量指标、验收标准和发布门禁，用于判断一个模块、一个开发任务、一次发布以及整套比赛作品是否真正完成。

本文档重点回答：

1. 系统需要哪些层次的测试；
2. 文献、数据、统计、图表、论文和证据链应如何验证；
3. AI 输出如何评测；
4. 确定性统计结果如何与基准结果比较；
5. 原始文件不可覆盖如何证明；
6. 数据处理审批如何测试；
7. Agent 越权和工具白名单如何测试；
8. 离线与降级能力如何验收；
9. 比赛演示前必须满足哪些门禁；
10. 哪些缺陷会阻止发布。

RECA 的完成标准不是“页面能够打开”或“模型能够回答”，而是核心科研流程能够在真实来源、确定性计算、人工确认、版本留痕和证据追溯约束下稳定完成。

---

# 2. 文档权威性

## 2.1 本文档负责

本文档是以下内容的唯一正式基准：

* 测试分层；
* 测试目录；
* 测试数据；
* 黄金测试集；
* 单元测试范围；
* 集成测试范围；
* API 契约测试；
* AI Schema 测试；
* 工具契约测试；
* 端到端测试；
* 性能测试；
* 安全测试；
* 离线演示测试；
* 产品验收用例；
* 缺陷分级；
* 发布门禁；
* 比赛演示验收。

## 2.2 其他文档职责

| 内容           | 权威文档                          |
| ------------ | ----------------------------- |
| 产品功能和范围      | `PRODUCT_REQUIREMENTS.md`     |
| 技术架构         | `ARCHITECTURE.md`             |
| 数据对象和状态机     | `DATA_MODEL_AND_WORKFLOW.md`  |
| API、AI 和工具参数 | `API_AI_TOOL_CONTRACTS.md`    |
| 安全、隐私和许可证    | `SECURITY_AND_OPEN_SOURCE.md` |
| Codex 开发规范   | `AGENTS.md`                   |

## 2.3 验收冲突处理

当产品功能已经实现，但不满足本文档的核心门禁时：

* 不得标记为完成；
* 不得关闭对应 Issue；
* 不得进入比赛发布分支；
* 不得以“现场人工规避”替代修复；
* 不得使用 Mock 结果通过正式验收。

---

# 3. 测试目标

## 3.1 功能正确

验证每项 P0 功能：

* 输入正确时产生预期结果；
* 输入错误时返回明确错误；
* 状态不允许时拒绝操作；
* 权限不足时拒绝访问；
* 异步任务状态完整；
* 失败不会破坏已有数据。

## 3.2 科研可信

验证：

* 文献来自真实数据源；
* 原文证据来自真实 PDF；
* 统计数字来自确定性程序；
* 图表绑定正确数据版本；
* 论文数字与分析结果一致；
* Claim 能回到来源；
* AI 不伪造论文和数字。

## 3.3 可追溯

验证每项关键结果能够关联：

* Project；
* Artifact；
* DatasetVersion；
* AnalysisRun；
* EvidenceSpan；
* ApprovalRecord；
* ToolCall；
* AuditResult。

## 3.4 可复现

验证相同输入下：

* 数据转换结果一致；
* 统计结果在容差范围内一致；
* 图表核心数据一致；
* 导出包哈希和清单完整；
* 运行环境信息被记录。

## 3.5 安全受控

验证：

* 原始文件不可覆盖；
* Agent 不能执行任意代码；
* 未批准操作不能执行；
* 跨项目数据不可读取；
* 敏感字段不默认发送模型；
* 上传文件不会导致路径穿越。

## 3.6 比赛稳定

验证：

* 主演示流程可连续完成；
* 核心能力可在无外网时展示；
* 外部服务失败有降级；
* 全新 Docker 环境可启动；
* 演示项目可恢复；
* 录屏内容与真实产品能力一致。

---

# 4. 测试原则

## 4.1 测试必须覆盖成功与失败路径

每个功能至少测试：

* 正常输入；
* 空输入；
* 边界输入；
* 非法输入；
* 无权限；
* 错误状态；
* 外部服务失败；
* 重复提交；
* 并发修改；
* 取消和重试。

## 4.2 确定性能力优先做自动化测试

以下内容必须自动化：

* 文献去重；
* DOI 规范化；
* PDF 解析转换；
* 数据质量规则；
* 数据处理；
* 统计计算；
* 图表参数；
* 引用匹配；
* 数字核对；
* 状态机；
* 权限；
* 幂等；
* 文件哈希。

## 4.3 AI 输出采用黄金集与规则联合评测

AI 任务不能只依赖人工主观评价。

评测必须同时使用：

* Schema 验证；
* 来源覆盖；
* 字段准确率；
* 证据页码准确率；
* 禁止行为检测；
* 人工评分；
* 回归测试。

## 4.4 不使用生产用户数据作为测试数据

测试数据必须：

* 公开；
* 自建；
* 脱敏；
* 获得合法使用权限；
* 在仓库中记录来源和许可证。

## 4.5 测试数据必须可重复

测试不能依赖：

* 会频繁变化的在线搜索结果；
* 无固定版本的模型响应；
* 未锁定的远程数据；
* 无法重新获取的临时文件。

## 4.6 外部服务测试分层

对 OpenAlex、GROBID 和模型服务分别进行：

1. Mock 测试；
2. 契约测试；
3. 少量真实集成测试；
4. 降级测试。

CI 默认不得依赖不稳定外网。

## 4.7 修复缺陷必须增加回归测试

每个阻断级或严重级缺陷修复后，必须增加能够复现原问题的自动化测试。

# M0 Regression Baseline 摘要

M0 基线对应 commit `79825914c7c975e8be256a5a89abe812f486769e` 和 tag `m0-complete`，M1 Entry Decision 为 `ALLOWED`。从 M1 到 M9，任何里程碑都不得降低六项 required CI、clean-room 验收或已知风险披露。

六项 required CI 为：`backend-quality`、`frontend-quality`、`migration-test`、`compose-smoke`、`security-supply-chain`、`e2e-smoke`。完整命令、隔离环境验证项和两个 LOW 风险见 [M0 Regression Baseline](./testing/M0_REGRESSION_BASELINE.md)。

---

# 测试金字塔摘要

RECA 按以下层次组织测试：

```text
静态检查与 Schema 检查
→ 单元测试
→ 契约测试
→ 集成测试
→ 黄金集与确定性基准
→ 端到端测试
→ clean-room、离线演示与比赛验收
```

低层测试负责快速定位，高层测试证明真实边界和完整闭环。Mock、缓存或预处理快照必须显式标记，不能代替真实迁移、确定性统计、文件安全、项目隔离、人工审批和正式发布验收。详细策略见 [Test Strategy and Environments](./testing/TEST_STRATEGY_AND_ENVIRONMENTS.md)。

---

# 6. 测试类型总览

| 测试类型         | 主要工具                         | 执行时机             |
| ------------ | ---------------------------- | ---------------- |
| Python 静态检查  | Ruff、mypy 或项目选定工具            | 每次提交             |
| 前端静态检查       | ESLint、TypeScript            | 每次提交             |
| 单元测试         | pytest、前端测试框架                | 每次提交             |
| API 契约测试     | pytest、FastAPI TestClient    | 每次提交             |
| AI Schema 测试 | pytest、Pydantic              | 每次提交             |
| Adapter 契约测试 | pytest                       | 每次提交             |
| 数据库测试        | pytest + PostgreSQL          | Pull Request     |
| 对象存储测试       | MinIO 测试容器                   | Pull Request     |
| Celery 测试    | Celery 测试 Worker             | Pull Request     |
| GROBID 集成测试  | GROBID 容器                    | 每日或发布前           |
| 前端组件测试       | 选定前端测试框架                     | Pull Request     |
| 浏览器 E2E      | Playwright                   | Pull Request、发布前 |
| 性能测试         | Locust/k6 或 pytest-benchmark | 里程碑、发布前          |
| 安全测试         | 自研用例、依赖扫描                    | Pull Request、发布前 |
| 离线演示测试       | Docker Compose               | 发布前              |
| 人工科研验收       | 专家或团队复核                      | 功能冻结前            |

---

# 36. 缺陷分级

## 36.1 Blocker：阻断级

满足任一条件：

* 主流程无法继续；
* 数据丢失；
* 原始文件被覆盖；
* 统计结果错误；
* 虚构文献进入正式演示；
* 未授权用户访问他人项目；
* Agent 可执行任意代码；
* 未批准数据修改被执行；
* 导出泄露密钥或敏感数据；
* Docker 无法启动；
* 演示项目无法打开。
* 真实 Secret 进入仓库、前端包或普通日志；
* 无许可证或来源不明内容被复制进正式仓库；
* 必须保留的 LICENSE、NOTICE 或归属缺失；
* 上传文件可执行或存在明显路径穿越；
* 模型生成正式统计数字或虚构 EvidenceSpan；
* Critical 供应链风险与实际执行路径相关且可达；
* required CI 或适用 clean-room 被规避。

发布要求：

```text
Blocker = 0
```

## 36.2 Critical：严重级

例如：

* 主要功能持续失败；
* EvidenceSpan 指向错误文献；
* 分析绑定错误数据版本；
* 图表与结果不一致；
* 论文数字核对错误；
* 审批状态可绕过；
* 核心审计记录缺失；
* 跨项目边建立成功。

发布要求：

```text
Critical = 0
```

## 36.3 Major：重要级

例如：

* 非核心字段抽取错误；
* 部分浏览器页面异常；
* 某类论文格式无法识别；
* 非主流程降级错误；
* 性能明显不达标但可继续操作。

以下校赛版缺口应记录为警告或后续强化，不因其自身阻断 Competition Edition：已披露 LOW advisory、与主演示和实际执行路径无关的 MEDIUM、缺少完整 SBOM、企业 Secret Manager、灾备演练、正式事件响应、高级容器强化或企业监控。它们不得被隐藏，也不得掩盖真实 Blocker 或可达 Critical 风险。

发布要求：

* 必须有负责人和处理计划；
* 主演示路径不得存在 Major；
* 未修复项必须写入已知限制。

## 36.4 Minor：一般级

例如：

* 文案；
* 对齐；
* 非关键样式；
* 低影响提示；
* 不影响结果的日志问题。

可带缺陷发布，但需登记。

## 36.5 Enhancement：改进项

不属于缺陷，不阻止发布。

---

# 38. 功能完成定义

一个 Issue 或功能只有同时满足以下条件才可关闭：

1. 对应需求已实现；
2. 正常路径完成；
3. 错误路径完成；
4. 权限完成；
5. 状态机完成；
6. 审计完成；
7. 幂等完成；
8. 单元测试完成；
9. 契约测试完成；
10. 必要集成测试完成；
11. 前端交互完成；
12. E2E 或验收用例完成；
13. 文档同步；
14. 不违反安全规则；
15. 不覆盖原始文件；
16. 不使用 Mock 冒充真实能力；
17. 已知限制登记；
18. Code Review 通过。

---

# 里程碑与发布门禁摘要

## 里程碑门禁

每个 M1-M9 里程碑必须同时满足对应路线图 Exit Gate、本入口的功能完成定义、M0 Regression Baseline 以及相关子测试文档。失败项必须记录为缺陷或阻塞问题，不能通过删除测试、降低阈值、扩大忽略范围或把 Mock 标记为真实能力来放行。

里程碑证据至少包含：

- 适用测试命令与真实结果；
- Requirement ID 与 Acceptance ID 的追踪；
- 数据库、API、AI Schema、Tool 或安全边界的变更说明；
- 未执行测试、降级路径、已知限制和残余风险；
- 必要的人工作业、专家复核或 `ApprovalRecord` 证据。

## 发布门禁

发布候选必须满足完整发布门禁，不允许入口摘要替代详细规则。唯一完整定义位于 [E2E Acceptance and Release Gates](./testing/E2E_ACCEPTANCE_AND_RELEASE_GATES.md)，包括代码质量、自动测试、科研可信、版本不可变、审批、安全、部署、缺陷和文档门禁。

| 类别 | 不可降低的门禁 |
| --- | --- |
| 真实来源 | 演示文献和 DOI 虚构数为 0，核心 EvidenceSpan 来自真实文档位置 |
| 确定性计算 | 正式统计数字来源率 100%，图表与 AnalysisResult、DatasetVersion 一致 |
| 人工确认 | 高风险操作审批覆盖率 100%，Agent 自行审批次数为 0 |
| 安全 | 项目隔离、文件安全、日志脱敏、模型 data-access 和任意代码禁令全部通过 |
| 版本 | 原始文件及 Original 版本覆盖次数为 0，派生结果创建新版本 |
| 回归 | 六项 required CI、适用 clean-room 和核心 E2E 全部通过 |
| 缺陷 | `Blocker = 0`、`Critical = 0`、主演示路径 `Major = 0` |

开源复用和审批专项验收至少覆盖：来源与上游 Commit/Tag 可追踪；Fork/Vendor/选择性复制所需归属文件完整；特殊许可证内容隔离；ARS-Codex 的 `NONCOMMERCIAL_INTENT_DECLARED` 和商业化复审门存在且未被误写为已完成复制；无许可证复制被拒绝；只读与候选生成工具不要求正式审批；改变科研数据、正式结果或文件的高风险工具仍要求有效审批。

---

# 子测试文档导航与变更规则

详细规范按唯一权威范围分布在五份子文档中。任何指标、容差、Acceptance ID、测试命令或门禁变更必须：

1. 修改唯一完整定义位置；
2. 同步入口摘要和需求追踪；
3. 保留稳定 ID，不得静默重命名；
4. 增加或更新对应回归证据；
5. 说明是否影响 M0 基线、Competition Core、P0-Full 或发布决定；
6. 将冲突作为文档缺陷处理，不得自行选择更低标准。

全部 Acceptance ID 的完整定义与显式锚点位于 [E2E Acceptance and Release Gates](./testing/E2E_ACCEPTANCE_AND_RELEASE_GATES.md)。指标和数值容差的完整定义位于 [Golden Sets and Metrics](./testing/GOLDEN_SETS_AND_METRICS.md)。

---

# 最终测试结论

RECA 的完成标准不是“页面能够打开”或“模型能够回答”，而是核心科研流程能够在真实来源、确定性计算、人工确认、版本留痕、项目隔离和证据追溯约束下稳定完成。入口文档负责不可降低的原则和门禁索引，子文档负责可执行的详细测试与验收规范。
