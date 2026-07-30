# 研证链 AI（RECA）产品需求文档

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档名称 | `PRODUCT_REQUIREMENTS.md` |
| 文档版本 | 1.2.0 |
| 适用项目版本 | RECA 0.1 Competition Edition |
| 文档状态 | Conditional Approval |
| 文档角色 | 产品定位、范围、需求索引和变更规则入口 |
| 负责人 | RECA Team |
| 最后更新 | 2026-07-30 |

## 文档组成

本入口文档与其列出的子文档共同构成本领域的正式开发基准。入口文档负责产品定位、范围、需求 ID 总表、边界、成功指标和索引；子文档负责每个需求的唯一完整定义。两者冲突属于文档缺陷，不得自行猜测。

- [项目、研究问题与候选问题](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md)
- [文献与原文证据](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md)
- [数据、分析与图表](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md)
- [论文、证据链、导出与 Agent](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md)
- [UX、非功能与追踪](./product/UX_NONFUNCTIONAL_AND_TRACEABILITY.md)

`archive/` 为非权威历史材料。

# 1. 文档目的与权威性

本文档是 RECA 0.1 的唯一产品范围和 Requirement ID 索引基准，用于回答产品为什么存在、服务谁、P0/P1 边界以及每项需求的完整定义位置。

冲突处理：

1. 开发红线以 [AGENTS.md](../AGENTS.md) 为准；
2. 功能范围和 Requirement ID 以本文档及五份产品子文档为准；
3. 数据对象和状态以 [DATA_MODEL_AND_WORKFLOW.md](./DATA_MODEL_AND_WORKFLOW.md) 为准；
4. API、AI Schema 和 Tool 以 [API_AI_TOOL_CONTRACTS.md](./API_AI_TOOL_CONTRACTS.md) 为准；
5. 技术实现以 [ARCHITECTURE.md](./ARCHITECTURE.md) 为准；
6. 测试指标以 [TEST_AND_ACCEPTANCE.md](./TEST_AND_ACCEPTANCE.md) 为准；
7. 安全和许可证以 [SECURITY_AND_OPEN_SOURCE.md](./SECURITY_AND_OPEN_SOURCE.md) 为准；
8. 实施顺序以 [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) 为准。

# 2. 产品定位

项目名称：研证链 AI（RECA），英文名 Research Evidence Chain Agent。

一句话定位：

> 面向高校科研训练的全流程可信科研工作台，把研究问题、真实文献、原文证据、数据版本、确定性分析、图表、论文论述、人工确认和复现材料连接为可追溯证据链。

RECA 是 Web 科研工作台，不是聊天机器人、论文生成器、全功能统计平台或校级科研管理系统。

核心价值：

- 科研提效：减少检索、抽取、检查、整理和导出的重复工作；
- 科研提质：让结论有来源、数字有运行记录、图表有数据版本；
- 科研可信：禁止虚构文献、模型计算正式数字和未批准高风险写入；
- 科研可复现：保留数据、处理、计划、结果、代码、版本和审批；
- 科研教学：让用户看见每一步依据、限制和责任边界。

# 3. 用户摘要

| 用户 | 主要目标 | P0 产品支持 |
| --- | --- | --- |
| 本科生 | 从模糊兴趣形成可执行研究问题 | Scoping、文献证据、基础数据分析和可信提示 |
| 研究生 | 提高文献、数据和论文工作效率 | 文献矩阵、EvidenceSpan、版本、分析、Claim 和复现包 |
| 教师 | 指导与检查科研过程 | 项目查看、问题定位、证据追踪和审批记录 |
| 管理员 | 维护基础系统 | 用户基础、示例项目、演示数据和服务状态；不建设完整校级后台 |

项目内权限、成员和 Agent 权限的完整需求见 [项目与研究需求](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md)。

# 4. 产品原则

1. AI 负责理解、建议、抽取、解释和审核辅助；确定性程序负责统计、绘图、解析、哈希和版本结果。
2. 文献、数字和证据必须来自真实来源或正式运行记录。
3. 原始文件和 Original DatasetVersion 不可覆盖。
4. 研究问题确认、处理计划、分析计划、图表、论文高风险修改和导出结论需要人工确认。
5. 缺少 EvidenceSpan 时必须表示“无已定位证据”，不得创建伪证据。
6. 业务状态保存在数据库，不保存在 Agent Session。
7. 采用单总控 Agent，不采用自由多 Agent；正式 Agent 在 M8 接入。
8. 功能少而稳定，失败、降级和限制必须显式展示。

# 5. 核心闭环

```text
创建项目
→ 输入研究想法
→ Scoping 与 ResearchQuestionVersion 确认
→ 真实文献检索或导入
→ PDF 解析、EvidenceSpan 和文献矩阵
→ 文献筛选、当前证据集合分析和候选研究问题
→ DatasetVersion、数据质量和 CleaningPlan 审批
→ AnalysisPlan、确定性统计和 Figure
→ DOCX、Claim 和 MANU-P0-018 修订漂移审核
→ 跨文献—数据—分析—图表—论文证据链
→ ReproPackage
→ M8 单总控 Agent 受控编排
```

所有结构化页面和确定性能力必须可以脱离 Agent 直接使用。

# 6. 范围分层

## 6.1 P0-Must

P0-Must 是比赛现场必须稳定、真实运行的最小完整闭环。它优先保证真实来源、EvidenceSpan、不可变版本、审批、确定性数字、Claim 证据链、复现包、离线演示和必要的单总控阶段导航。

P0-Must 的实施裁剪不删除任何 P0 Requirement ID，也不能把未完成能力伪装为已完成。具体方法、图表和检查器的 Must 子集以路线图为准。

## 6.2 P0-Full

P0-Full 是 RECA 0.1 Competition Edition 的完整 P0 目标，包含本文件总表中的全部 P0 Requirement ID。它在 P0-Must 基础上补齐完整统计方法、图表、批量文献处理、论文检查、交互、导出和治理能力。

`MANU-P0-018` 的 Competition Core 只依赖确定性或高稳定规则；P0-Full 才增加模型辅助的限定词、范围、新 Claim 和复杂语义漂移。该边界不得改变。

## 6.3 P1

P1 只在 P0 稳定后考虑，不得提前升级到 P0：

P0 稳定后再考虑：

* 文献主题聚类；
* 研究时间线；
* 文献关系图；
* 用户反馈重排序；
* 主动学习文献筛选；
* 多元线性回归；
* 常用非参数方法；
* 更多图表；
* 完整 CSL 引用；
* APA、Chicago 等格式；
* 教师批注；
* 低风险 DOCX 格式修复；
* 学校论文模板；
* 更多公开数据源；
* 文献真实性扩展核验；
* 简单领域异常线索包。

# 7. P0 模块总表

| 模块       | 功能ID范围                            | P0状态 |
| -------- | --------------------------------- | ---- |
| 科研项目     | PROJ-P0-001 至 PROJ-P0-010         | 必须   |
| 研究问题     | RQ-P0-001 至 RQ-P0-009             | 必须   |
| 文献检索     | SEARCH-P0-001 至 SEARCH-P0-012     | 必须   |
| PDF与文献矩阵 | LIT-P0-001 至 LIT-P0-018           | 必须   |
| 文献筛选与分析  | REVIEW-P0-001 至 REVIEW-P0-011     | 必须   |
| 候选问题     | TOPIC-P0-001 至 TOPIC-P0-008       | 必须   |
| 数据与版本    | DATA-P0-001 至 DATA-P0-014         | 必须   |
| 数据质量与处理  | QUALITY-P0-001 至 QUALITY-P0-015   | 必须   |
| 统计分析     | ANALYSIS-P0-001 至 ANALYSIS-P0-016 | 必须   |
| 科研图表     | FIG-P0-001 至 FIG-P0-012           | 必须   |
| 论文质控     | MANU-P0-001 至 MANU-P0-018         | 必须   |
| 证据链      | EVID-P0-001 至 EVID-P0-014         | 必须   |
| 复现包      | EXPORT-P0-001 至 EXPORT-P0-008     | 必须   |
| 总控智能体    | AGENT-P0-001 至 AGENT-P0-010       | 必须   |
| AI 治理与审计 | AGOV-P0-001 至 AGOV-P0-005         | 必须   |

<a id="functional-requirement-index"></a>
# 8. 功能需求 ID 总表

每个 ID 只在链接到的子文档中具有一个完整定义。本表只提供名称、领域和稳定链接。

| Requirement ID | 原名称 | 唯一完整定义领域 |
| --- | --- | --- |
| [PROJ-P0-001](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-001) | 创建项目 | 项目与研究 |
| [PROJ-P0-002](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-002) | 项目基础信息编辑 | 项目与研究 |
| [PROJ-P0-003](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-003) | 项目阶段 | 项目与研究 |
| [PROJ-P0-004](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-004) | 项目总览 | 项目与研究 |
| [PROJ-P0-005](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-005) | 项目待办 | 项目与研究 |
| [PROJ-P0-006](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-006) | 项目成员 | 项目与研究 |
| [PROJ-P0-007](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-007) | 项目归档 | 项目与研究 |
| [PROJ-P0-008](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-008) | 项目删除 | 项目与研究 |
| [PROJ-P0-009](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-009) | 快速工具归属 | 项目与研究 |
| [PROJ-P0-010](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#proj-p0-010) | 项目操作日志 | 项目与研究 |
| [RQ-P0-001](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-001) | 输入研究想法 | 项目与研究 |
| [RQ-P0-002](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-002) | 结构化提取 | 项目与研究 |
| [RQ-P0-003](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-003) | 信息不足提示 | 项目与研究 |
| [RQ-P0-004](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-004) | 用户编辑 | 项目与研究 |
| [RQ-P0-005](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-005) | 研究问题版本 | 项目与研究 |
| [RQ-P0-006](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-006) | 最终确认 | 项目与研究 |
| [RQ-P0-007](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-007) | 取消确认 | 项目与研究 |
| [RQ-P0-008](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-008) | 研究问题收缩建议 | 项目与研究 |
| [RQ-P0-009](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#rq-p0-009) | 验收标准 | 项目与研究 |
| [SEARCH-P0-001](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-001) | 查询规划 | 文献与证据 |
| [SEARCH-P0-002](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-002) | 查询编辑 | 文献与证据 |
| [SEARCH-P0-003](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-003) | OpenAlex 检索 | 文献与证据 |
| [SEARCH-P0-004](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-004) | 检索缓存 | 文献与证据 |
| [SEARCH-P0-005](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-005) | DOI 导入 | 文献与证据 |
| [SEARCH-P0-006](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-006) | 文献去重 | 文献与证据 |
| [SEARCH-P0-007](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-007) | 相关性解释 | 文献与证据 |
| [SEARCH-P0-008](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-008) | 真实性状态 | 文献与证据 |
| [SEARCH-P0-009](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-009) | 阅读清单 | 文献与证据 |
| [SEARCH-P0-010](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-010) | 引用导出 | 文献与证据 |
| [SEARCH-P0-011](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-011) | 文献结果加入项目 | 文献与证据 |
| [SEARCH-P0-012](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#search-p0-012) | 验收标准 | 文献与证据 |
| [LIT-P0-001](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-001) | PDF 上传 | 文献与证据 |
| [LIT-P0-002](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-002) | 文件哈希 | 文献与证据 |
| [LIT-P0-003](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-003) | 重复文件处理 | 文献与证据 |
| [LIT-P0-004](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-004) | GROBID 解析 | 文献与证据 |
| [LIT-P0-005](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-005) | pypdf 回退 | 文献与证据 |
| [LIT-P0-006](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-006) | 页面信息 | 文献与证据 |
| [LIT-P0-007](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-007) | 文档分块 | 文献与证据 |
| [LIT-P0-008](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-008) | 元数据匹配 | 文献与证据 |
| [LIT-P0-009](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-009) | 十字段抽取 | 文献与证据 |
| [LIT-P0-010](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-010) | EvidenceSpan | 文献与证据 |
| [LIT-P0-011](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-011) | 置信度 | 文献与证据 |
| [LIT-P0-011A](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-011a) | 证据验证状态 | 文献与证据 |
| [LIT-P0-012](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-012) | 用户修正 | 文献与证据 |
| [LIT-P0-013](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-013) | 修正历史 | 文献与证据 |
| [LIT-P0-014](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-014) | 文献矩阵 | 文献与证据 |
| [LIT-P0-015](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-015) | PDF 阅读器 | 文献与证据 |
| [LIT-P0-016](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-016) | 解析任务状态 | 文献与证据 |
| [LIT-P0-017](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-017) | 批量处理 | 文献与证据 |
| [LIT-P0-018](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#lit-p0-018) | 验收标准 | 文献与证据 |
| [REVIEW-P0-001](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-001) | 文献决策 | 文献与证据 |
| [REVIEW-P0-002](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-002) | 排除理由 | 文献与证据 |
| [REVIEW-P0-003](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-003) | 决策历史 | 文献与证据 |
| [REVIEW-P0-004](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-004) | AI 推荐 | 文献与证据 |
| [REVIEW-P0-005](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-005) | 共识识别 | 文献与证据 |
| [REVIEW-P0-006](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-006) | 争议识别 | 文献与证据 |
| [REVIEW-P0-007](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-007) | 当前证据不足 | 文献与证据 |
| [REVIEW-P0-008](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-008) | 原文依据 | 文献与证据 |
| [REVIEW-P0-009](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-009) | 待核实问题 | 文献与证据 |
| [REVIEW-P0-010](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-010) | 结果导出 | 文献与证据 |
| [REVIEW-P0-011](./product/LITERATURE_AND_EVIDENCE_REQUIREMENTS.md#review-p0-011) | 验收标准 | 文献与证据 |
| [TOPIC-P0-001](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-001) | 生成条件 | 项目与研究 |
| [TOPIC-P0-002](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-002) | 用户资源输入 | 项目与研究 |
| [TOPIC-P0-003](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-003) | 生成数量 | 项目与研究 |
| [TOPIC-P0-004](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-004) | 候选内容 | 项目与研究 |
| [TOPIC-P0-005](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-005) | 等级评价 | 项目与研究 |
| [TOPIC-P0-006](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-006) | 横向比较 | 项目与研究 |
| [TOPIC-P0-007](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-007) | 用户选择 | 项目与研究 |
| [TOPIC-P0-008](./product/PROJECT_AND_RESEARCH_REQUIREMENTS.md#topic-p0-008) | 验收标准 | 项目与研究 |
| [DATA-P0-001](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-001) | 文件格式 | 数据、分析与图表 |
| [DATA-P0-002](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-002) | 文件限制 | 数据、分析与图表 |
| [DATA-P0-003](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-003) | 数据上传 | 数据、分析与图表 |
| [DATA-P0-004](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-004) | 原始版本 | 数据、分析与图表 |
| [DATA-P0-005](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-005) | 数据身份证 | 数据、分析与图表 |
| [DATA-P0-006](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-006) | 数据预览 | 数据、分析与图表 |
| [DATA-P0-007](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-007) | 字段字典 | 数据、分析与图表 |
| [DATA-P0-008](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-008) | 变量角色 | 数据、分析与图表 |
| [DATA-P0-009](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-009) | 版本关系 | 数据、分析与图表 |
| [DATA-P0-010](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-010) | 版本比较 | 数据、分析与图表 |
| [DATA-P0-011](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-011) | 版本失效 | 数据、分析与图表 |
| [DATA-P0-012](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-012) | 数据来源合规提示 | 数据、分析与图表 |
| [DATA-P0-013](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-013) | 数据敏感字段提示 | 数据、分析与图表 |
| [DATA-P0-014](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#data-p0-014) | 验收标准 | 数据、分析与图表 |
| [QUALITY-P0-001](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-001) | 数据质量概览 | 数据、分析与图表 |
| [QUALITY-P0-002](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-002) | 缺失值 | 数据、分析与图表 |
| [QUALITY-P0-003](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-003) | 重复 | 数据、分析与图表 |
| [QUALITY-P0-004](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-004) | 类型异常 | 数据、分析与图表 |
| [QUALITY-P0-005](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-005) | 范围问题 | 数据、分析与图表 |
| [QUALITY-P0-006](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-006) | 极端值 | 数据、分析与图表 |
| [QUALITY-P0-007](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-007) | 类别一致性 | 数据、分析与图表 |
| [QUALITY-P0-008](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-008) | 分组不平衡 | 数据、分析与图表 |
| [QUALITY-P0-009](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-009) | 单位疑似不一致 | 数据、分析与图表 |
| [QUALITY-P0-010](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-010) | 隐私字段 | 数据、分析与图表 |
| [QUALITY-P0-011](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-011) | CleaningPlan | 数据、分析与图表 |
| [QUALITY-P0-012](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-012) | 处理预览 | 数据、分析与图表 |
| [QUALITY-P0-013](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-013) | 用户批准 | 数据、分析与图表 |
| [QUALITY-P0-014](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-014) | 执行处理 | 数据、分析与图表 |
| [QUALITY-P0-015](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#quality-p0-015) | 验收标准 | 数据、分析与图表 |
| [ANALYSIS-P0-001](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-001) | 分析目标 | 数据、分析与图表 |
| [ANALYSIS-P0-002](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-002) | AnalysisPlan | 数据、分析与图表 |
| [ANALYSIS-P0-003](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-003) | 描述统计 | 数据、分析与图表 |
| [ANALYSIS-P0-004](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-004) | 独立样本两组比较 | 数据、分析与图表 |
| [ANALYSIS-P0-005](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-005) | 配对两组比较 | 数据、分析与图表 |
| [ANALYSIS-P0-006](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-006) | Pearson 相关 | 数据、分析与图表 |
| [ANALYSIS-P0-007](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-007) | Spearman 相关 | 数据、分析与图表 |
| [ANALYSIS-P0-008](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-008) | 简单线性回归 | 数据、分析与图表 |
| [ANALYSIS-P0-009](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-009) | 前提检查 | 数据、分析与图表 |
| [ANALYSIS-P0-010](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-010) | 用户批准 | 数据、分析与图表 |
| [ANALYSIS-P0-011](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-011) | AnalysisRun | 数据、分析与图表 |
| [ANALYSIS-P0-012](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-012) | AnalysisResult | 数据、分析与图表 |
| [ANALYSIS-P0-013](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-013) | 结果解释 | 数据、分析与图表 |
| [ANALYSIS-P0-014](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-014) | 重复运行 | 数据、分析与图表 |
| [ANALYSIS-P0-015](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-015) | 结果失效 | 数据、分析与图表 |
| [ANALYSIS-P0-016](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#analysis-p0-016) | 验收标准 | 数据、分析与图表 |
| [FIG-P0-001](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-001) | 表达目标 | 数据、分析与图表 |
| [FIG-P0-002](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-002) | 图表推荐 | 数据、分析与图表 |
| [FIG-P0-003](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-003) | P0 图表类型 | 数据、分析与图表 |
| [FIG-P0-004](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-004) | 变量确认 | 数据、分析与图表 |
| [FIG-P0-005](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-005) | 图表生成 | 数据、分析与图表 |
| [FIG-P0-006](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-006) | 图注 | 数据、分析与图表 |
| [FIG-P0-007](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-007) | 规范检查 | 数据、分析与图表 |
| [FIG-P0-008](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-008) | 代码导出 | 数据、分析与图表 |
| [FIG-P0-009](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-009) | 参数保存 | 数据、分析与图表 |
| [FIG-P0-010](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-010) | 图表版本 | 数据、分析与图表 |
| [FIG-P0-011](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-011) | 图表确认 | 数据、分析与图表 |
| [FIG-P0-012](./product/DATA_ANALYSIS_AND_FIGURE_REQUIREMENTS.md#fig-p0-012) | 验收标准 | 数据、分析与图表 |
| [MANU-P0-001](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-001) | DOCX 上传 | 论文、证据链、导出与 Agent |
| [MANU-P0-002](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-002) | 文档解析 | 论文、证据链、导出与 Agent |
| [MANU-P0-003](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-003) | 引用提取 | 论文、证据链、导出与 Agent |
| [MANU-P0-004](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-004) | 文内与文末双向核对 | 论文、证据链、导出与 Agent |
| [MANU-P0-005](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-005) | 项目文献库核对 | 论文、证据链、导出与 Agent |
| [MANU-P0-006](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-006) | DOI 格式检查 | 论文、证据链、导出与 Agent |
| [MANU-P0-007](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-007) | 样本量检查 | 论文、证据链、导出与 Agent |
| [MANU-P0-008](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-008) | 统计数字核对 | 论文、证据链、导出与 Agent |
| [MANU-P0-009](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-009) | 图文一致性 | 论文、证据链、导出与 Agent |
| [MANU-P0-010](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-010) | 因果夸大 | 论文、证据链、导出与 Agent |
| [MANU-P0-011](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-011) | 样本外推 | 论文、证据链、导出与 Agent |
| [MANU-P0-012](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-012) | 学术共识夸大 | 论文、证据链、导出与 Agent |
| [MANU-P0-013](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-013) | 术语一致性 | 论文、证据链、导出与 Agent |
| [MANU-P0-014](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-014) | 基础格式 | 论文、证据链、导出与 Agent |
| [MANU-P0-015](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-015) | 问题清单 | 论文、证据链、导出与 Agent |
| [MANU-P0-016](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-016) | 自动修复边界 | 论文、证据链、导出与 Agent |
| [MANU-P0-017](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-017) | 验收标准 | 论文、证据链、导出与 Agent |
| [MANU-P0-018](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#manu-p0-018) | 修订漂移审核 | 论文、证据链、导出与 Agent |
| [EVID-P0-001](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-001) | Claim | 论文、证据链、导出与 Agent |
| [EVID-P0-002](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-002) | Claim 类型 | 论文、证据链、导出与 Agent |
| [EVID-P0-003](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-003) | Claim 与文献证据 | 论文、证据链、导出与 Agent |
| [EVID-P0-004](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-004) | Claim 与数据 | 论文、证据链、导出与 Agent |
| [EVID-P0-005](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-005) | Claim 与处理 | 论文、证据链、导出与 Agent |
| [EVID-P0-006](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-006) | Claim 与分析 | 论文、证据链、导出与 Agent |
| [EVID-P0-007](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-007) | Claim 与图表 | 论文、证据链、导出与 Agent |
| [EVID-P0-008](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-008) | Claim 与人工确认 | 论文、证据链、导出与 Agent |
| [EVID-P0-009](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-009) | Claim 与审核 | 论文、证据链、导出与 Agent |
| [EVID-P0-010](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-010) | 证据范围 | 论文、证据链、导出与 Agent |
| [EVID-P0-011](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-011) | 图谱页面 | 论文、证据链、导出与 Agent |
| [EVID-P0-012](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-012) | 完整度 | 论文、证据链、导出与 Agent |
| [EVID-P0-013](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-013) | 失效传播 | 论文、证据链、导出与 Agent |
| [EVID-P0-014](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#evid-p0-014) | 验收标准 | 论文、证据链、导出与 Agent |
| [EXPORT-P0-001](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-001) | 导出入口 | 论文、证据链、导出与 Agent |
| [EXPORT-P0-002](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-002) | 导出内容 | 论文、证据链、导出与 Agent |
| [EXPORT-P0-003](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-003) | manifest.json | 论文、证据链、导出与 Agent |
| [EXPORT-P0-004](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-004) | README_REPRODUCE.md | 论文、证据链、导出与 Agent |
| [EXPORT-P0-005](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-005) | 导出前检查 | 论文、证据链、导出与 Agent |
| [EXPORT-P0-006](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-006) | 异步导出 | 论文、证据链、导出与 Agent |
| [EXPORT-P0-007](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-007) | 导出版本 | 论文、证据链、导出与 Agent |
| [EXPORT-P0-008](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#export-p0-008) | 验收标准 | 论文、证据链、导出与 Agent |
| [AGENT-P0-001](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-001) | 产品定位 | 论文、证据链、导出与 Agent |
| [AGENT-P0-002](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-002) | 阶段判断 | 论文、证据链、导出与 Agent |
| [AGENT-P0-003](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-003) | 任务规划 | 论文、证据链、导出与 Agent |
| [AGENT-P0-004](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-004) | 工具选择 | 论文、证据链、导出与 Agent |
| [AGENT-P0-005](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-005) | 用户确认 | 论文、证据链、导出与 Agent |
| [AGENT-P0-006](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-006) | 结构化输出 | 论文、证据链、导出与 Agent |
| [AGENT-P0-007](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-007) | 运行记录 | 论文、证据链、导出与 Agent |
| [AGENT-P0-008](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-008) | 审核步骤 | 论文、证据链、导出与 Agent |
| [AGENT-P0-009](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-009) | 禁止行为 | 论文、证据链、导出与 Agent |
| [AGENT-P0-010](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agent-p0-010) | 验收标准 | 论文、证据链、导出与 Agent |
| [AGOV-P0-001](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agov-p0-001) | PromptContract manifest 与模型调用治理 | 论文、证据链、导出与 Agent |
| [AGOV-P0-002](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agov-p0-002) | 模型数据访问等级强制 | 论文、证据链、导出与 Agent |
| [AGOV-P0-003](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agov-p0-003) | 降级记录与用户披露 | 论文、证据链、导出与 Agent |
| [AGOV-P0-004](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agov-p0-004) | ProjectContextSnapshot 与 AgentRun 上下文 | 论文、证据链、导出与 Agent |
| [AGOV-P0-005](./product/MANUSCRIPT_AGENT_AND_EXPORT_REQUIREMENTS.md#agov-p0-005) | StageResolver 与受控路由 | 论文、证据链、导出与 Agent |

# 9. 产品边界

## 31.1 文献

* 付费全文绕过下载；
* 全网爬虫；
* 扫描件高精度 OCR；
* 自动下载未授权论文；
* 撤稿数据库完整覆盖；
* 完整引文网络。

## 31.2 数据

* 任意代码执行；
* 自动为显著性修改数据；
* 自动删除异常值；
* 全功能统计平台；
* 结构方程模型；
* 混合效应模型；
* 复杂时间序列；
* 贝叶斯模型；
* 生存分析。

## 31.3 论文

* 一键生成完整论文；
* 自动降重；
* 规避查重；
* 精确抄袭率；
* 完整 Word 在线编辑器；
* 复杂公式自动重排；
* 修订记录自动处理；
* LaTeX 排版。

## 31.4 协作与管理

* 多人实时编辑；
* 校级科研管理；
* 复杂审批流；
* 课程管理；
* 成绩管理。

## 31.5 实验诊断

* 全学科实验故障诊断；
* 在没有实验过程资料时确定错误原因；
* 自动生成实验结论。

# 10. 产品成功指标

## 33.1 核心流程指标

* 主演示流程成功率：100%；
* 正式演示文献虚构数：0；
* 统计数字可追溯率：100%；
* 原始文件覆盖次数：0；
* 用户确认记录率：100%；
* 主演示 Claim 证据链覆盖率：100%。

## 33.2 文献指标

* 十字段抽取准确率；
* EvidenceSpan 页码准确率；
* 文献真实性状态完整率；
* 用户修正率；
* 无来源字段率。

## 33.3 数据指标

* 已植入质量问题检出率；
* 误报率；
* 版本可追溯率；
* 统计结果一致率；
* 未批准修改次数。

## 33.4 论文指标

* 引用问题检出率；
* 数字问题检出率；
* 因果夸大检出率；
* 术语问题检出率；
* 问题定位准确率。

## 33.5 体验指标

* 用户完成主演示流程所需步骤；
* 关键页面成功加载率；
* 任务失败提示完整率；
* 用户理解确认内容的比例。

具体目标值见 `TEST_AND_ACCEPTANCE.md`。

# 11. 需求追踪摘要

完整追踪矩阵位于 [UX、非功能与追踪文档](./product/UX_NONFUNCTIONAL_AND_TRACEABILITY.md#requirement-traceability-matrix)。当前 Competition Core 重点保持：

| Requirement | 追踪重点 | Milestone |
| --- | --- | --- |
| RQ-P0-003 | Scoping 输出与 ResearchQuestionVersion 分离 | M2 |
| LIT-P0-011A | EvidenceSpan 定位、阅读范围和验证状态 | M3 |
| AGOV-P0-001 至 AGOV-P0-003 | Prompt manifest、数据访问和降级披露 | M1 / M1+ |
| MANU-P0-018 | 确定性修订漂移 Competition Core | M6 |
| AGOV-P0-004 至 AGOV-P0-005 | Snapshot、StageResolver 和单总控编排 | M8 |

需求到数据模型、API/AI 契约、验收测试、里程碑和 Competition Core 的映射不得静默改变。

# 12. 需求变更规则

在当前 `Conditional Approval` 状态下，任何需求调整都必须：

- 保留原 Requirement ID，除非产品负责人明确批准废弃；
- 说明对 P0-Must、P0-Full、P1、Competition Core 和演示的影响；
- 同步数据模型、API/AI/Tool 契约、测试、安全和路线图；
- 新增 P0 功能必须有资源来源和被移出范围；
- 不得通过删除需求、降低测试标准或扩大 P0 消除冲突；
- 破坏性变化必须记录版本、原因、批准人和迁移策略。

文档达到 Approved 后，新增 P0 功能必须经过产品负责人批准。许可证、外部模型发送和安全边界还需要对应治理决定。

# 13. 最终产品结论

RECA 的核心不是自动生成更多内容，而是让科研过程中的来源、证据、数据、分析、图表、论述、审批和复现记录形成可验证链路。所有开发必须保持真实来源、确定性计算、人工确认、项目隔离和失败透明。
